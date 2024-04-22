import json
from elasticsearch import Elasticsearch, helpers
import os

ADDRESS = "https://129.151.196.60:9200"
API_KEY = "Rmd0VzhZNEJWU2NOMkpFRnNYUU06clUxQ0ROajlSa0dVRWl1U05vLVVTdw=="
INDEX = "podcast_transcripts"
DATASET_FOLDER = "../dataset_subset/"

def execute_query(client, query, n=10):
    return client.search(index=INDEX, body=query, size=n)

def get_first_n_results(response, n=10):
    results = []
    for hit in response['hits']['hits'][:n]:
        result = hit['_source']
        results.append(result)
    return results

def read_test(client, n):
    query = {
            "query": {
                "match": {"transcript": "I like peanuts"}
            }
        }
    
    resp = execute_query(client, query, n)

    return get_first_n_results(resp, n)


# Initialize Elasticsearch client
client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False)
resp = read_test(client, 1)
print(resp)