import json
from elasticsearch import Elasticsearch, helpers
import os
import xml.etree.ElementTree as ET
import pandas as pd
import warnings
from urllib3.exceptions import InsecureRequestWarning
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS, DATASET_FOLDER

# Filter out the specific warning about insecure HTTPS requests
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

def index_transcripts_with_metadata_from_folder(folder_path, index_name, episode_index_name, show_index_name):
    transcript_file_path = os.path.join(folder_path, "podcasts-transcripts")
    metadata_file_path = os.path.join(folder_path, "metadata.tsv")
    rss_file_path = os.path.join(folder_path, "show-rss")
    
    metadata_df = pd.read_csv(metadata_file_path, delimiter='\t', dtype="string")

    actions = []
    actions_episodes = []
    actions_shows = []

    prev_showname = ""

    indexed_files = 0

    for root, dirs, files in os.walk(transcript_file_path):
        for file_name in tqdm(files, f"Indexing {root}"):
            if (indexed_files % 100 == 0):
                print(f"Index files: {indexed_files}")
            indexed_files += 1

            if file_name.endswith('.json'):
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
                    if(prev_showname != showID):
                        show = {
                            "_id": showID,
                            "show_name": episode_row["show_name"].item(),
                            "show_description": episode_row["show_description"].item(),
                            "publisher": episode_row["publisher"].item(),
                            "image": imageurl,
                            "link": link
                        }
                        actions_shows.append(show)
                        prev_showname = episode_row["show_filename_prefix"].item()

                    #Index transcripts
                    for alt in alternatives:
                        try:
                            transcript = alt["alternatives"][0]["transcript"]
                            starttime = alt["alternatives"][0]["words"][0]["startTime"]
                            endtime = alt["alternatives"][0]["words"][-1]["endTime"]
                            confidence = alt["alternatives"][0]["confidence"]
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

                            #Submit all together
                            if(len(actions) >= 5000):
                                r1 = helpers.bulk(client, actions, index=index_name, stats_only=True)
                                actions = []
                                r2 = helpers.bulk(client, actions_episodes, index=episode_index_name, stats_only=True)
                                actions_episodes = []
                                r3 = helpers.bulk(client, actions_shows, index=show_index_name, stats_only=True)
                                actions_shows = []

                                if (r1[1] > 0 or r2[1] > 0 or r3[1] > 0):
                                    print("Something went wrong indexing")
                            
                        except KeyError:
                            pass
                    

    if (len(actions) != 0):
        try:
            r1 = helpers.bulk(client, actions, index=index_name)
            r2 = helpers.bulk(client, actions_episodes, index=episode_index_name)
            r3 = helpers.bulk(client, actions_shows, index=show_index_name)

            if (r1[1] > 0 or r2[1] > 0 or r3[1] > 0):
                print("Something went wrong indexing")
        except KeyError:
            pass


def create_index(index_name):
    # Define index settings and mappings if needed
    # You can define your index settings and mappings here
    # For simplicity, we'll skip this step

    if client.indices.exists(index=index_name):
        print("Index already exsits!")
        return

    # Create the index
    client.indices.create(index=index_name)
    print(f"Index '{index_name}' created successfully.")


if (__name__ == "__main__"):
    # Initialize Elasticsearch client
    client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False)

    # Init word2vec
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    # Create index
    create_index(INDEX_TRANSCRIPTS)
    create_index(INDEX_EPISODES)
    create_index(INDEX_SHOWS)

    # Index the entire dataset
    index_transcripts_with_metadata_from_folder(DATASET_FOLDER, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS)
