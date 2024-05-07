from elasticsearch import Elasticsearch, helpers
import json
from tqdm import tqdm
from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS


def check_index(index, total):
    client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False, request_timeout=120)

    errors = []
    
    with open("errors.json", "a") as f:
        for doc in tqdm(helpers.scan(client=client, scroll="6h", index=index, size=80), total=total):
            if doc['_source']['vector'] != None:
                json.dump(doc, f)
                f.write("\n")
                errors.append(doc)
                print("Found error: ", doc['_id'])

            if doc['_source']['new_vector'] == None:
                print("Did not find a new vector for: ", doc['_source']['new_vector'])

    print(errors)
    print("Errors found: ", len(errors))


check_index(INDEX_TRANSCRIPTS, 8429540)
