from elasticsearch import Elasticsearch, helpers
import json
import time
from tqdm import tqdm
from setup import ADDRESS, API_KEY, INDEX_TRANSCRIPTS, INDEX_EPISODES, INDEX_SHOWS

client = Elasticsearch(ADDRESS, api_key=API_KEY, verify_certs=False, ssl_show_warn=False, request_timeout=120)
action_buffer = []
done_lines = dict()
sent_updates = 0

"""with open("../elastic_backup/podcast_transcripts_backup.json", "r") as data_file:
    for line in data_file:
        doc = json.loads(line)
        #doc_id = doc['_id']
        #vector = doc['_source']['vector']
        doc_id = "5byitvMgqKIGsDXhe4Wg2c_57"
        res = client.get(index=INDEX_TRANSCRIPTS, id=doc_id)
        vector = res["_source"]["vector"]
        trans = res["_source"]["transcript"]

        action_buffer.append({'_op_type': 'update', "_id": doc_id, 'doc': {"transcript": trans, "vector": None, "new_vector": vector } })

        # do reindexing
        r1 = helpers.bulk(client=client, actions=action_buffer, index=INDEX_TRANSCRIPTS, stats_only=False)

        print(r1)
        break"""

with open("Progress.txt", "r") as f:
    for line in f:
        done_lines[line.strip()] = True
    print(len(done_lines), " lines done")

with open("Progress.txt", "a") as f:
    with open("../elastic_backup/podcast_transcripts_backup.json", "r") as data_file:
        with tqdm(total=8429540, desc="Processing") as tqdm_bar:
            for i, line in enumerate(data_file):
                tqdm_bar.update(1)

                if (i+1 < len(done_lines)):
                    continue

                doc = json.loads(line)
                doc_id = doc['_id']

                if (doc_id in done_lines):
                    continue

                vector = doc['_source']['vector']
                trans = doc["_source"]["transcript"]

                action_buffer.append({'_op_type': 'update', "_id": doc_id, 'doc': {"transcript": trans, "vector": None, "new_vector": vector } })

                # do reindexing
                if (len(action_buffer) >= 1000):
                    tqdm_bar.write("Sending: " + str(len(action_buffer)))
                    r1 = helpers.bulk(client=client, actions=action_buffer, index=INDEX_TRANSCRIPTS, stats_only=False)
                    sent_updates += len(action_buffer)

                    if (len(r1[1]) > 0):
                        tqdm_bar.write("Error sending to server: " + str(r1[1]))
                        exit(1)
                    else:
                        for d in action_buffer:
                            f.write(d["_id"] + "\n")
                        
                        action_buffer = []
                    
                    if (sent_updates % 100_000 == 0):
                        tqdm_bar.write("Sleeping for 6m to let server work...", end="")
                        time.sleep(60*6)
                        client.indices.refresh(index=INDEX_TRANSCRIPTS) # Clear all the deleted stuff and make sure indexing is done
                        tqdm_bar.write(" Continuing!")

            if (len(action_buffer) != 0): # Empty buffer before exiting
                tqdm_bar.write("Sending: " + str(len(action_buffer)))
                r1 = helpers.bulk(client=client, actions=action_buffer, index=INDEX_TRANSCRIPTS, stats_only=False)

                if (len(r1[1]) > 0):
                    tqdm_bar.write("Error sending to server: " + str(r1[1]))
                    exit(1)
                else:
                    for d in action_buffer:
                        f.write(d["_id"] + "\n")
                    
                    action_buffer = []
                
                client.indices.refresh(index=INDEX_TRANSCRIPTS) # Clear all the deleted stuff and make sure indexing is done

