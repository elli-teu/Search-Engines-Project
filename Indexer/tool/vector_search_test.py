from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
import time
import requests
import json

from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS


model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False, request_timeout=240)

#client.indices.refresh(index=INDEX_TRANSCRIPTS)
while True:
  sent = input("Sentence to search: ")
  vector = model.encode(sent)
  knn_query = { 
            "field": "new_vector",
            "query_vector": vector.tolist(), 
            "num_candidates": 10,
            "k": 5
        }
  print("Starting")
  start_time = time.time()
  response = client.search(index=INDEX_TRANSCRIPTS, knn=knn_query)
  print("Took: ", (time.time()-start_time))
  print("Number of results:", response['hits']['total']['value'])