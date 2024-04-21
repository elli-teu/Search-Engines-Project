import json
from elasticsearch import Elasticsearch, helpers
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import pandas as pd
import warnings
from urllib3.exceptions import InsecureRequestWarning
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from elastic_transport import ConnectionTimeout
import time

from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS, DATASET_FOLDER

# Filter out the specific warning about insecure HTTPS requests
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

def index_transcripts_with_metadata_from_folder(folder_path, index_name, episode_index_name, show_index_name):
    transcript_file_path = os.path.join(folder_path, "podcasts-transcripts")
    metadata_file_path = os.path.join(folder_path, "metadata.tsv")
    
    metadata_df = pd.read_csv(metadata_file_path, delimiter='\t', dtype="string")
    
    actions = []
    actions_episodes = []
    actions_shows = []

    num_actions_cached = 5000
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    file_count = sum(len(files) for _, _, files in os.walk(transcript_file_path)) # Inefficient but only once so ok
    with tqdm(total=file_count, desc="Indexing files") as tqdm_bar:
        with tqdm(total=num_actions_cached*2, desc="Actions in buffer") as tqdm_buffer_bar:
            for root, dirs, files in os.walk(transcript_file_path):
                for file_name in files:
                    tqdm_bar.update(1)

                    if file_name.endswith('.json'):
                        (new_actions, new_actions_episodes, new_actions_shows) = index_file(root, file_name, metadata_df, model, episode_index_name, show_index_name)
                        
                        tqdm_buffer_bar.update(len(new_actions))
                        actions.extend(new_actions)
                        actions_episodes.extend(new_actions_episodes)
                        actions_shows.extend(new_actions_shows)

                        #Submit all together
                        if (len(actions) >= num_actions_cached):
                            try:
                                tqdm_buffer_bar.write(f"Sending to server! {len(actions)} actions")
                                r1 = helpers.bulk(client, actions, index=index_name, stats_only=False)
                                actions = []
                                r2 = helpers.bulk(client, actions_episodes, index=episode_index_name, stats_only=False)
                                actions_episodes = []
                                r3 = helpers.bulk(client, actions_shows, index=show_index_name, stats_only=False)
                                actions_shows = []

                                tqdm_buffer_bar.reset()

                                if (len(r1[1]) > 0 or len(r2[1]) > 0 or len(r3[1]) > 0):
                                    tqdm_buffer_bar.write("Something went wrong indexing")
                                    log_errors("Error sending to server: " + str(r1[1]))
                                    log_errors("Error sending to server: " + str(r2[1]))
                                    log_errors("Error sending to server: " + str(r3[1]))

                            except KeyError:
                                pass

    if (len(actions) != 0):
        try:
            print("Emptying buffers!")
            r1 = helpers.bulk(client, actions, index=index_name, stats_only=False)
            r2 = helpers.bulk(client, actions_episodes, index=episode_index_name, stats_only=False)
            r3 = helpers.bulk(client, actions_shows, index=show_index_name, stats_only=False)

            if (len(r1[1]) > 0 or len(r2[1]) > 0 or len(r3[1]) > 0):
                print("Something went wrong indexing")
                log_errors("Error sending to server: " + str(r1[1]))
                log_errors("Error sending to server: " + str(r2[1]))
                log_errors("Error sending to server: " + str(r3[1]))
        except KeyError:
            pass

    print("DONE!")
    return True

def index_file(root, file_name, metadata_df, model, episode_index_name, show_index_name):
    actions = []
    actions_episodes = []
    actions_shows = []
    file_path = os.path.join(root, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        #Index episodes and shows
        episode_filename = os.path.splitext(file_name)[0]
        episode_row = metadata_df[metadata_df['episode_filename_prefix'] == episode_filename]

        if (client.exists(index=episode_index_name, id=episode_filename).body):
            # We have already indexed this file
            return (actions, actions_episodes, actions_shows)

        episode = {
            "_id": episode_filename,
            "episode_name": episode_row["episode_name"].item(),
            "episode_description": episode_row["episode_description"].item(),
            "show": episode_row["show_filename_prefix"].item()
        }
        actions_episodes.append(episode)

        #ugly but should work (get image and podcast link)
        #assuming "correct" directory names
        pathlist = file_path.replace("/", os.path.sep).split(os.path.sep)[:-1]
        pathlist[-4] = "show-rss"
        show_rss_path = os.path.sep.join(pathlist) + ".xml"

        try:
            tree = ET.parse(show_rss_path)
            xmlroot = tree.getroot()
            imageurl = xmlroot[0].find('.//image')
            if (imageurl is None):
                imageurl = ""
                print(f"No imageurl found for: {show_rss_path}")
                log_errors(f"No imageurl found for: {show_rss_path}")
            else:
                imageurl = imageurl[0].text
            link = xmlroot[0].find('.//link')
            if (link is None):
                link = ""
                print(f"No link found for: {show_rss_path}")
                log_errors(f"No link found for: {show_rss_path}")
            else:
                link = link.text
        except ParseError as e:
            print(f"Parse error at: {show_rss_path}, skipping adding data to show")
            print(e)
            log_errors(f"Parse error at: {show_rss_path}, skipping adding data to show")
            imageurl = ""
            link = ""

        showID = episode_row["show_filename_prefix"].item()

        #avoid duplicates (possibly not needed)
        if (not client.exists(index=show_index_name, id=showID).body):
            show = {
                "_id": showID,
                "show_name": episode_row["show_name"].item(),
                "show_description": episode_row["show_description"].item(),
                "publisher": episode_row["publisher"].item(),
                "image": imageurl,
                "link": link
            }
            actions_shows.append(show)

        #Index transcripts
        document = json.load(file)
        alternatives = document["results"]

        current_id = 0
        for alt in alternatives:
            try:
                transcript = alt["alternatives"][0]["transcript"]
                starttime = alt["alternatives"][0]["words"][0]["startTime"]
                endtime = alt["alternatives"][0]["words"][-1]["endTime"]
                confidence = alt["alternatives"][0]["confidence"]

                if (transcript == "" or transcript == None):
                    continue
                
                attempts = 0
                success = False
                while attempts < 5 and not success:
                    try:
                        vector = model.encode(transcript)
                        success = True
                    except Exception as e:
                        print(f"Error with transcript:")
                        print(transcript)
                        print('\n')
                        print(e)
                        attempts += 1

                if not success:
                    print("Not success, exiting")
                    exit(1)

                contents = {
                    "_id": episode_filename + "_" + str(current_id),
                    "transcript": transcript,
                    "show_id": showID,
                    "starttime": starttime,
                    "endtime": endtime,
                    "confidence": confidence,
                    "vector":vector
                }
                current_id += 1
                actions.append(contents)
                
            except KeyError:
                pass
            except NotImplementedError as e:
                print(e)
                exit(1)

    return (actions, actions_episodes, actions_shows)

def create_index(index_name):
    # Define index settings and mappings if needed
    # You can define your index settings and mappings here
    # For simplicity, we'll skip this step

    if client.indices.exists(index=index_name):
        print(f"Index: {index_name} already exists!")
        r = input("You sure you want to continue [Y/N]?")
        if (r.lower() != "y"):
            exit(1)
        return

    # Create the index
    client.indices.create(index=index_name)
    print(f"Index '{index_name}' created successfully.")


def log_errors(error):
    with open("logs.txt", "a") as f:
        f.write(error + "\n\n")


if (__name__ == "__main__"):
    # Initialize Elasticsearch client
    client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False)

    # Create index
    create_index(INDEX_TRANSCRIPTS)
    create_index(INDEX_EPISODES)
    create_index(INDEX_SHOWS)

    # Index the entire dataset
    print("Indexing folder: " + DATASET_FOLDER)

    attempts = 0
    success = False
    finished = False
    while attempts < 5 and not success:
        try:
            finished = index_transcripts_with_metadata_from_folder(DATASET_FOLDER, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS)
            success = True
        except ConnectionTimeout as e:
            print("Connection timed out! Retrying in 10 seconds...")
            client.close()
            time.sleep(10)
            client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False)
            attempts += 1

    if (finished):
        print("Completed indexing without any major errors!")
    else:
        print("Something went wrong during indexing...")
        log_errors("Something went wrong during indexing...")