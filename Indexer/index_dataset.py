import json
from elasticsearch import Elasticsearch, helpers
import os
import xml.etree.ElementTree as ET
import pandas as pd
import warnings
from urllib3.exceptions import InsecureRequestWarning
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from multiprocessing.pool import ThreadPool

from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS, DATASET_FOLDER

# Filter out the specific warning about insecure HTTPS requests
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

def index_transcripts_with_metadata_from_folder(folder_path, index_name, episode_index_name, show_index_name, disable_threading = True, max_cores = 4):
    transcript_file_path = os.path.join(folder_path, "podcasts-transcripts")
    metadata_file_path = os.path.join(folder_path, "metadata.tsv")
    rss_file_path = os.path.join(folder_path, "show-rss")
    
    metadata_df = pd.read_csv(metadata_file_path, delimiter='\t', dtype="string")
    
    actions = []
    actions_episodes = []
    actions_shows = []

    num_actions_cached = 5000
    num_processes = max_cores if not disable_threading else 1 # use 1/2 of all available threads
    pool = ThreadPool(processes=num_processes)
    models = [SentenceTransformer('sentence-transformers/all-mpnet-base-v2') for x in range(num_processes)]
    files_to_pool = []

    if disable_threading:
        print("Running sequentially")
    else:
        print(f"Running on {num_processes} cores!")

    file_count = sum(len(files) for _, _, files in os.walk(transcript_file_path)) # Inefficient but only once so ok
    with tqdm(total=file_count, desc="Indexing files") as tqdm_bar:
        with tqdm(total=num_actions_cached*2, desc="Actions in buffer") as tqdm_buffer_bar:
            for root, dirs, files in os.walk(transcript_file_path):
                for file_name in files:
                    tqdm_bar.update(1)

                    if file_name.endswith('.json'):
                        files_to_pool.append((root, file_name, metadata_df, models[len(files_to_pool)%num_processes], index_name, show_index_name))

                        if len(files_to_pool) == num_processes*10:
                            new_actions = pool.starmap(index_file, files_to_pool)
                            
                            files_to_pool = []
                            for a in new_actions:
                                tqdm_buffer_bar.update(len(a[0]))
                                actions.extend(a[0])
                                actions_episodes.extend(a[1])
                                actions_shows.extend(a[2])

                        #Submit all together
                        if (len(actions) >= num_actions_cached):
                            tqdm_buffer_bar.write(f"Sending to server! {len(actions)} actions")
                            r1 = helpers.bulk(client, actions, index=index_name, stats_only=True)
                            actions = []
                            r2 = helpers.bulk(client, actions_episodes, index=episode_index_name, stats_only=True)
                            actions_episodes = []
                            r3 = helpers.bulk(client, actions_shows, index=show_index_name, stats_only=True)
                            actions_shows = []

                            tqdm_buffer_bar.reset()

                            if (r1[1] > 0 or r2[1] > 0 or r3[1] > 0):
                                print("Something went wrong indexing")
                
    if len(files_to_pool) != 0:
        new_actions = pool.starmap(index_file, files_to_pool)
        files_to_pool = []
        for a in new_actions:
            print(len(a))
            actions.append(a[0])
            actions_episodes.append(a[1])
            actions_shows.append(a[2])        

    # Close thread pool to prevent memory leaks etc.
    pool.close()
    pool.join() 

    if (len(actions) != 0):
        try:
            r1 = helpers.bulk(client, actions, index=index_name)
            r2 = helpers.bulk(client, actions_episodes, index=episode_index_name)
            r3 = helpers.bulk(client, actions_shows, index=show_index_name)

            if (r1[1] > 0 or r2[1] > 0 or r3[1] > 0):
                print("Something went wrong indexing")
        except KeyError:
            pass


def index_file(root, file_name, metadata_df, model, index_name, show_index_name):
    actions = []
    actions_episodes = []
    actions_shows = []
    file_path = os.path.join(root, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        document = json.load(file)
        alternatives = document["results"]

        current_id = 0

        #Index episodes and shows
        episode_filename = os.path.splitext(file_name)[0]
        episode_row = metadata_df[metadata_df['episode_filename_prefix'] == episode_filename]

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

        tree = ET.parse(show_rss_path)
        xmlroot = tree.getroot()
        imageurl = xmlroot[0].find('.//image')[0].text
        link = xmlroot[0].find('.//link').text

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
        for alt in alternatives:
            try:
                transcript = alt["alternatives"][0]["transcript"]
                starttime = alt["alternatives"][0]["words"][0]["startTime"]
                endtime = alt["alternatives"][0]["words"][-1]["endTime"]
                confidence = alt["alternatives"][0]["confidence"]

                if (client.exists(index=index_name, id=episode_filename + "_" + str(current_id)).body) or (transcript == "" or transcript == None):
                    current_id += 1
                    continue

                vector = model.encode(transcript)

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
        print(f"Index: {index_name} already exsits!")
        r = input("You sure you want to continue [Y/N]?")
        if (r.lower() == "n"):
            exit(1)
        return

    # Create the index
    client.indices.create(index=index_name)
    print(f"Index '{index_name}' created successfully.")


if (__name__ == "__main__"):
    # Initialize Elasticsearch client
    client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False)

    # Create index
    create_index(INDEX_TRANSCRIPTS)
    create_index(INDEX_EPISODES)
    create_index(INDEX_SHOWS)

    # Index the entire dataset
    print("Indexing folder: " + DATASET_FOLDER)
    index_transcripts_with_metadata_from_folder(DATASET_FOLDER, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS, disable_threading=False, max_cores=4) ## Maximum cores depends on your vram and other stuff (play around with it)
