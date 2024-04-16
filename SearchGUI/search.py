import json
from elasticsearch import Elasticsearch, helpers
import os
import pandas as pd
from setup import ADDRESS, API_KEY, INDEX
import xml.etree.ElementTree as ET

class QueryType:
    union_query = "union"
    intersection_query = "intersection"
    phrase_query = "phrase"


def index_documents_from_folder(folder_path, index_name):
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            print(file_name)
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    document = json.load(file)
                    # Index the document into Elasticsearch
                    client.index(index=index_name, body=document)


def index_transcripts_from_folder(folder_path, index_name):
    number_of_files = 0
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if number_of_files % 100 == 1:
                print(f"{number_of_files} files indexed.")
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    document = json.load(file)
                    alternatives = document["results"]
                    for alt in alternatives:
                        try:
                            transcript = alt["alternatives"][0]["transcript"]
                            contents = {"transcript": transcript}
                            client.index(index=index_name, body=contents)
                        except KeyError:
                            pass
                    # Index the document into Elasticsearch
            number_of_files += 1

def index_transcripts_with_metadata_from_folder(folder_path, index_name, episode_index_name, show_index_name):
    transcript_file_path = os.path.join(folder_path, "podcasts-transcripts")
    metadata_file_path = os.path.join(folder_path, "metadata.tsv")
    rss_file_path = os.path.join(folder_path, "show-rss")
    
    metadata_df = pd.read_csv(metadata_file_path, delimiter='\t', dtype="string")

    number_of_files = 0
    actions = []
    actions_episodes = []
    actions_shows = []

    prev_showname = ""

    for root, dirs, files in os.walk(transcript_file_path):
        for file_name in files:
            if number_of_files % 100 == 1:
                print(f"{number_of_files} files indexed.")
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
                        "episode_name": episode_row["episode_name"].item(),
                        "episode_description": episode_row["episode_description"].item()
                    }
                    actions_episodes.append(episode)

                    #ugly but should work (get image and podcast link)
                    #assuming "correct" directory names
                    pathlist = file_path.split(os.path.sep)[:-1]
                    pathlist[-4] = "show-rss"
                    show_rss_path = os.path.sep.join(pathlist) + ".xml"

                    tree = ET.parse(show_rss_path)
                    xmlroot = tree.getroot()
                    imageurl = xmlroot[0].find('.//image')[0].text
                    link = xmlroot[0].find('.//link').text

                    #avoid duplicates (possibly not needed)
                    if(prev_showname != episode_row["show_name"].item()):
                        show = {
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

                            contents = {
                                "_id": episode_filename + "_" + str(current_id),
                                "transcript": transcript,
                                "starttime": starttime,
                                "endtime": endtime
                            }
                            current_id += 1
                            actions.append(contents)

                            #Submit all together
                            if(len(actions) >= 1000):
                                helpers.bulk(client, actions, index=index_name)
                                actions = []
                                helpers.bulk(client, actions_episodes, index=episode_index_name)
                                actions_episodes = []
                                helpers.bulk(client, actions_shows, index=show_index_name)
                                actions_shows = []
                            
                        except KeyError:
                            pass
                    

                    # Index the document into Elasticsearch
            number_of_files += 1


def generate_query(query_string, query_type):
    if query_type == QueryType.union_query:
        query = {
            "query": {
                "match": {"transcript": query_string}
            }
        }
    elif query_type == QueryType.intersection_query:
        tokens = get_tokens(query_string)
        must_occur_list = [{"term": {"transcript": token}} for token in tokens]
        query = {
            "query": {
                "bool": {
                    "must": must_occur_list
                }
            }
        }
    elif query_type == QueryType.phrase_query:
        query = {
            "query": {
                "match_phrase": {
                    "transcript": query_string
                }
            }
        }
    else:
        raise ValueError(f"{query_type} is not a valid query type.")
    return query


def execute_query(query):
    return client.search(index=INDEX, body=query)


def delete_index(index_name):
    # Check if the index exists
    if client.indices.exists(index=index_name):
        # Delete the index
        client.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted successfully.")
    else:
        print(f"Index '{index_name}' does not exist.")


def create_index(index_name):
    # Define index settings and mappings if needed
    # You can define your index settings and mappings here
    # For simplicity, we'll skip this step

    # Create the index
    client.indices.create(index=index_name)
    print(f"Index '{index_name}' created successfully.")


def display_number_of_hits(response):
    print("Number of results:", response['hits']['total']['value'])


def get_number_of_hits(response):
    return response['hits']['total']['value']


def print_first_n_results(response, n=10):
    for hit in response['hits']['hits'][:n]:
        transcript = hit['_source']["transcript"]
        print("-" * 30)
        print("Score:", hit["_score"])
        print("Transcript: " + transcript)
        print("-" * 30 + "\n")


def get_first_n_results(response, n=10):
    results = []
    for hit in response['hits']['hits'][:n]:
        transcript = hit['_source']["transcript"]
        results.append(transcript)
    return results


def get_tokens(text):
    analyze_body = {
        "text": text,
        "analyzer": "standard"  # You can specify the name of the analyzer here
    }
    response = client.indices.analyze(index=INDEX, body=analyze_body)

    # Extract and print the tokens
    tokens = [token['token'] for token in response['tokens']]
    return tokens


# Initialize Elasticsearch client
client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False)
