from elasticsearch import Elasticsearch, helpers
import time
from multiprocessing.pool import ThreadPool
import json
from tqdm import tqdm
from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS


def backup_index(index, total):
    client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False, request_timeout=120)

    filename = index + "_backup.json"

    with open(filename, "w") as f:
        for doc in tqdm(helpers.scan(client=client, scroll="6h", index=index, size=80), total=total):
            json.dump(doc, f)
            f.write("\n")


backup_index(INDEX_TRANSCRIPTS, 8429540)