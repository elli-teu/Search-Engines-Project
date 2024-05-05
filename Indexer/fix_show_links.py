from elasticsearch import Elasticsearch, helpers
import json
import time
from tqdm import tqdm
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import pandas as pd
import os
from setup import ADDRESS, API_KEY, INDEX_EPISODES, INDEX_SHOWS, DATASET_FOLDER

client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False)
actions_shows = []
actions_episodes = []
transcript_file_path = os.path.join(DATASET_FOLDER, "podcasts-transcripts")
metadata_file_path = os.path.join(DATASET_FOLDER, "metadata.tsv")
metadata_df = pd.read_csv(metadata_file_path, delimiter='\t', dtype="string")
file_count = sum(len(files) for _, _, files in os.walk(transcript_file_path)) # Inefficient but only once so ok

# action_buffer.append({'_op_type': 'update', "_id": doc_id, 'doc': {"transcript": trans, "vector": None, "new_vector": vector } })

with tqdm(total=file_count, desc="Indexing files") as tqdm_bar:
    for root, dirs, files in os.walk(transcript_file_path):
        for file_name in files:
            tqdm_bar.update(1)

            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    #Index episodes and shows
                    episode_filename = os.path.splitext(file_name)[0]
                    episode_row = metadata_df[metadata_df['episode_filename_prefix'] == episode_filename]
                    showID = episode_row["show_filename_prefix"].item()

                    # Get episode, show
                    episode_doc = client.get(index=INDEX_EPISODES, id=episode_filename)
                    show_doc = client.get(index=INDEX_SHOWS, id=showID)

                    #avoid duplicates (possibly not needed)
                    if (not "pod_link" in show_doc or not "audio_link" in episode_doc):
                        #ugly but should work (get image and podcast link)
                        #assuming "correct" directory names
                        pathlist = file_path.replace("/", os.path.sep).split(os.path.sep)[:-1]
                        pathlist[-4] = "show-rss"
                        show_rss_path = os.path.sep.join(pathlist) + ".xml"

                        try:
                            tree = ET.parse(show_rss_path)
                            xmlroot = tree.getroot()

                            try:    
                                characteristics = {
                                    item.findtext("title") : item.find('enclosure').attrib["url"]
                                    for item in xmlroot[0].findall('item')
                                }
                            except AttributeError as e:
                                tqdm_bar.write(f"Characteristic is None")
                                print(e)
                                characteristics = None

                            if (characteristics is None):
                                audiolink = None
                            else:
                                audiolink = characteristics.get(episode_row["episode_name"].item())
                                
                            if(audiolink is None):
                                audiolink = ""
                                tqdm_bar.write(f"No audiolink found for: {show_rss_path}")
                            
                            podlink = xmlroot[0].find('.//item/link')
                            if (podlink is None):
                                podlink = ""
                                tqdm_bar.write(f"No podlink found for: {show_rss_path}")
                            else:
                                podlink = "/".join(podlink.text.split("/")[:4])

                            if (not "audio_link" in episode_doc and audiolink != ""):
                                episode = {
                                    "audio_link": audiolink
                                }
                                actions_episodes.append({'_op_type': 'update', "_id": episode_doc['_id'], 'doc': episode })

                            if (not "pod_link" in show_doc and podlink != ""):
                                show = {
                                    "pod_link": podlink
                                }
                                actions_shows.append({'_op_type': 'update', "_id": show_doc['_id'], 'doc': show })  

                        except ParseError as e:
                            tqdm_bar.write(f"Parse error at: {show_rss_path}, skipping adding data to show")
                            print(e)

                    # do reindexing
                    if (len(actions_episodes) >= 1000 or len(actions_shows) >= 1000):
                        tqdm_bar.write("Sending episodes: " + str(len(actions_episodes)) + ", shows: " + str(len(actions_shows)))
                        r1 = helpers.bulk(client=client, actions=actions_episodes, index=INDEX_EPISODES, stats_only=False)
                        r2 = helpers.bulk(client=client, actions=actions_shows, index=INDEX_SHOWS, stats_only=False)

                        if (len(r1[1]) > 0 or len(r2[1]) > 0):
                            tqdm_bar.write("Error sending to server: " + str(r1[1]) + " : " + str(r2[1]))
                            exit(1)
                            
                        actions_episodes = []
                        actions_shows = []

    if (len(actions_episodes) != 0): # Empty buffer before exiting
        tqdm_bar.write("Sending episodes: " + str(len(actions_episodes)))
        r1 = helpers.bulk(client=client, actions=actions_episodes, index=INDEX_EPISODES, stats_only=False)

        if (len(r1[1]) > 0):
            tqdm_bar.write("Error sending to server: " + str(r1[1]))
            exit(1)

    if (len(actions_shows) != 0): # Empty buffer before exiting
        tqdm_bar.write("Sending episodes: " + str(len(actions_shows)))
        r1 = helpers.bulk(client=client, actions=actions_shows, index=INDEX_SHOWS, stats_only=False)

        if (len(r1[1]) > 0):
            tqdm_bar.write("Error sending to server: " + str(r1[1]))
            exit(1)
