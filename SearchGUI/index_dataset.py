import json
from elasticsearch import Elasticsearch, helpers
import os
from setup import ADDRESS, API_KEY, INDEX, DATASET_FOLDER

def index_transcripts_from_folder(folder_path, index_name):
    number_of_files = 0
    actions = []
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if number_of_files % 100 == 1:
                print(f"{number_of_files} files indexed.")
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    document = json.load(file)
                    alternatives = document["results"]
                    curr_id = 0
                    for alt in alternatives:
                        try:
                            transcript = alt["alternatives"][0]["transcript"]
                            #contents = {"transcript": transcript}
                            actions.append({"_id" : file_name.replace(".json", "_"+str(curr_id)), "transcript": transcript})
                            curr_id += 1
                            if len(actions) >= 1000:
                                r = helpers.bulk(client, actions, index=index_name, stats_only=True)
                                print("Success : Error; " + r)
                                actions = []
                            #client.index(index=index_name, body=contents, id=file_name.replace(".json","_"+str(curr_id)))
                        except KeyError:
                            pass

                number_of_files += 1

    if (len(actions) != 0):
        try:
            r = helpers.bulk(client, actions, index=index_name, stats_only=True)
            print("Success : Error; " + r)
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
    # Create index
    create_index(INDEX)
    # Index the entire dataset
    index_transcripts_from_folder(DATASET_FOLDER, INDEX)
