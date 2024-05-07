from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
import time
import requests
import json
import torch.nn.functional as F


from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)

client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False, request_timeout=240)

#client.indices.refresh(index=INDEX_TRANSCRIPTS)
while True:
    sent = input("Sentence to search: ")
    embeddings = model.encode("search_query: " + sent, convert_to_tensor=True)
    embeddings = F.layer_norm(embeddings, normalized_shape=(embeddings.shape[0],))
    embeddings = embeddings[:256]
    vector = F.normalize(embeddings, p=2, dim=0)
    knn_query = { 
            "field": "vector",
            "query_vector": vector.tolist(), 
            "num_candidates": 100,
            "k": 15
        }
    print("Starting")
    start_time = time.time()
    response = client.search(index=INDEX_TRANSCRIPTS, knn=knn_query, source=["show_id", "transcript", "starttime", "endtime"])
    print("Took: ", (time.time()-start_time))
    print("Number of results:", response['hits']['total']['value'])
    print("Reported time: ", response['took'])
    print("Keys:", response["hits"]['hits'][0]['_source'].keys())