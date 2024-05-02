import json
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
import os
from setup import ADDRESS, API_KEY, INDEX
import re

import warnings
from urllib3.exceptions import InsecureRequestWarning

# Filter out the specific warning about insecure HTTPS requests
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class QueryType:
    union_query = "union"
    intersection_query = "intersection"
    phrase_query = "phrase"
    smart_query = "smart"


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


def get_transcript_metadata(results):
    if len(results) == 0:
        return []
    episode_bulk_requests = []
    metadata = []
    shows = []
    for res in results:
        show = res["show_id"]
        shows.append(show)
        episode_bulk_requests.append({"index": "podcast_episodes"})
        episode_request = {
            "query": {
                "match": {"show": show}
            }}
        episode_bulk_requests.append(episode_request)

    episode_request = "\n".join([json.dumps(request) for request in episode_bulk_requests])
    episode_bulk_response = client.msearch(body=episode_request)

    show_bulk_response = client.mget(index="podcast_shows", body={"ids": shows})
    for episode_response, show_response in zip(episode_bulk_response["responses"], show_bulk_response["docs"]):
        this_metadata = {}
        episode_hits = episode_response["hits"]["hits"]
        if len(episode_hits) != 0:
            episode = episode_hits[0]["_source"]

            if "episode_name" in episode:
                this_metadata["episode_name"] = episode["episode_name"]
            else:
                this_metadata["episode_name"] = "null"

            if "episode_name" in episode:
                this_metadata["episode_description"] = episode["episode_description"]
            else:
                this_metadata["episode_description"] = "null"
        else:
            this_metadata["episode_name"] = "null"
            this_metadata["episode_description"] = "null"

        if show_response["found"]:
            show = show_response["_source"]
            if "show_name" in show:
                this_metadata["podcast_name"] = show["show_name"]
            else:
                this_metadata["podcast_name"] = "null"

            if "show_description" in show:
                this_metadata["podcast_description"] = show["show_description"]
            else:
                this_metadata["podcast_description"] = "null"

            if "publisher" in show:
                this_metadata["publisher"] = show["publisher"]
            else:
                this_metadata["publisher"] = "null"

            if "link" in show:
                this_metadata["link"] = show["link"].lstrip(" ").rstrip(" ")
            else:
                this_metadata["link"] = "null"

            if "image" in show:
                this_metadata["image"] = show["image"]
            else:
                this_metadata["image"] = "null"

        else:
            this_metadata["podcast_name"] = "null"
            this_metadata["podcast_description"] = "null"
            this_metadata["publisher"] = "null"
            this_metadata["link"] = "null"
            this_metadata["image"] = "null"

        metadata.append(this_metadata)

    return metadata


def generate_query(query_string, query_type):
    if query_type == QueryType.smart_query:
        words = query_string.split(" ")
        words = [x for x in words if len(x) != 0]
        must_occur_words = [x[1:] for x in words if x[0] == "+"]
        must_occur_tokens = get_tokens(" ".join(must_occur_words))
        must_occur_list = [{"term": {"transcript": token}} for token in must_occur_tokens]

        must_not_occur_words = [x[1:] for x in words if x[0] == "-"]
        must_not_occur_tokens = get_tokens(" ".join(must_not_occur_words))
        must_not_occur_list = [{"term": {"transcript": token}} for token in must_not_occur_tokens]

        phrases = re.findall("""["']([^"]*)["']""", query_string)
        phases_list = [{"match_phrase": {"transcript": x}} for x in phrases]
        must_occur_list.extend(phases_list)

        should_occur_words = [x for x in words if
                              x not in must_occur_words and x not in must_not_occur_words and x not in " ".join(
                                  phrases)]
        should_occur_tokens = get_tokens(" ".join(should_occur_words))
        should_occur_list = [{"term": {"transcript": token}} for token in should_occur_tokens]

        query = {
            "query": {
                "bool": {
                    "must": must_occur_list,
                    "must_not": must_not_occur_list,
                    "should": should_occur_list
                }
            }
        }
    elif query_type == QueryType.union_query:
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


def execute_query(query, n=10, index=INDEX):
    # TODO: This results in 0 results if the query is too long.
    return client.search(index=index, body=query, size=n)


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
        result = hit['_source']
        results.append(result)
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
client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False)
