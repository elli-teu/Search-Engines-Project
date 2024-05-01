import json
from elasticsearch import Elasticsearch, helpers
import os
from setup import ADDRESS, INDEX, USERNAME, ELASTIC_PASSWORD, CA_CERT
import sys
#sys.path.append("C:\\Users\\ELLI\\anaconda3\\Lib\\site-packages")
from sentence_transformers import SentenceTransformer
import warnings
from urllib3.exceptions import InsecureRequestWarning
import openai
import torch.nn.functional as F

# Filter out the specific warning about insecure HTTPS requests
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

#API KEY
"""sk-proj-GuRuVvdJbwlXDQuQuyH0T3BlbkFJlBwVGo5RnIufufuXhhwJ"""

chat_client = openai.OpenAI(
    # This is the default and can be omitted
    api_key='sk-proj-GuRuVvdJbwlXDQuQuyH0T3BlbkFJlBwVGo5RnIufufuXhhwJ',
)
messages = [ {"role": "system", "content":"Correct any spelling misstakes"} ] #För att initialisera gpt
#Ändrat
"""sentences = ["This is an example sentence", "Each sentence is converted"]

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
embeddings = model.encode(sentences)"""
matryoshka_dim = 256 #Nyhet

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True) #Nyhet
sentences = ['search_query: What is TSNE?', 'search_query: Who is Laurens van der Maaten?']
"""Följande är bara nyheter för testet, men det visar flera vektorer i samma embeddings"""
embeddings = model.encode(sentences, convert_to_tensor=True) #Nyhet
embeddings = F.layer_norm(embeddings, normalized_shape=(embeddings.shape[1],)) #Nyhet
embeddings = embeddings[:, :matryoshka_dim] #Nyhet
embeddings = F.normalize(embeddings, p=2, dim=1) #Nyhet
print("hi again")
print(embeddings)

score_threshold = 0.7

class QueryType:
    union_query = "union"
    intersection_query = "intersection"
    phrase_query = "phrase"
    vector_query = "vector"
    combi_query = "combi"

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
    actions = []
    print("hello")
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            #if number_of_files % 1 == 1:
            #print(folder_path)
            print(f"{number_of_files} files indexed :).")
            #print(file_name)
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                #print("Test")
                with open(file_path, 'r', encoding='utf-8') as file:
                    document = json.load(file)
                    alternatives = document["results"]
                    curr_id = 0
                    for alt in alternatives:
                        try:
                            #print("Test")
                            transcript = alt["alternatives"][0]["transcript"]
                            embeddings = model.encode("search_document: " + transcript, convert_to_tensor=True) #Nyhet
                            embeddings = F.layer_norm(embeddings, normalized_shape=(embeddings.shape[0],)) #Nyhet
                            embeddings = embeddings[:matryoshka_dim] #Nyhet
                            vector = F.normalize(embeddings, p=2, dim=0) #Nyhet
                            #vector = model.encode(transcript) #ändrat
                            #contents = {"transcript": transcript, "vector":vector} #Tror man lägger till vektorn här
                            #client.index(index=index_name, body=contents)
                            actions.append({"_id" : file_name.replace(".json", "_"+str(curr_id)), "transcript" : transcript, "dense_vector":vector.tolist()}) #Nyhet att man MÅSTE skriva tolist()
                            curr_id += 1
                            if len(actions) >= 1000:
                                helpers.bulk(client, actions, index=index_name)
                                actions = []
                        except KeyError:
                            pass
                    # Index the document into Elasticsearch
            number_of_files += 1
    if (len(actions) != 0):
        try: 
            helpers.bulk(client, actions, index= index_name)
        except KeyError:
            pass

def generate_query(query_string, query_type):
    if query_type == QueryType.union_query:
        query = {
            "query": { #Här ska den göras tillvektor
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
    elif query_type == QueryType.vector_query:
            embeddings = model.encode("search_query: " + query_string, convert_to_tensor=True)
            embeddings = F.layer_norm(embeddings, normalized_shape=(embeddings.shape[0],))
            embeddings = embeddings[:matryoshka_dim]
            vector = F.normalize(embeddings, p=2, dim=0)
            query = { #Här lägga till att söka i titel, kombinera med tex intersect/phrase/union
            "query": {
                "knn": {
                    "field": "dense_vector",  # Field containing the vectors
                    "query_vector": vector.tolist(),  # Vector for similarity search
                    #"k": 10,
                    "num_candidates": 100
                }
            },
            "_source": ["id", "transcript"],
            "fields": []  # optional, if you want to include additional fields, can be newly computed results
        }
        
    elif query_type == QueryType.combi_query:
        #Börja med att kolla om querien innehåller något specialtecken - isf kör special
        """Gå igenom alla ord, om någon returnerar 0 kan vi tolka det som att det är felstavat -> kör in hela querien i chatGPT"""
        print(type(query_string))
        string_list = query_string.split(" ") #Kanske strunta i
        for string in string_list:
            print(string)
            spelling_query = {
                "query": { 
                    "match": {"transcript": string}
                }
            }
            
            res = client.search(body = spelling_query)
            print(res)
            print(res['hits']['total']['value'])
            if res['hits']['total']['value'] == 0:
                #Sätt query_string till_chat-gpt
                #Bryt
                print("hi there")
                messages.append(
                    {"role": "user", "content": query_string},
                )
                
                chat = chat_client.chat.completions.create(
                    messages = messages,
                
                
                    model="gpt-3.5-turbo",
                )
                query_string = chat.choices[0].message.content
                print(f"ChatGPT: {query_string}")
                messages.append({"role": "assistant", "content": query_string})

                break
            #på vilken form skickas denna tillbaka? Hur kolla längden?


        #Kan välja om vi ska kolla kolla allt med chat-gpt eller om vi ska kolla allt här först

        query = { #Vill söka i titel här
        "query":{
            "match": {"transcript": {
                "query": query_string,
                "boost": 0.1}
                      },
            
            #"match": {"title" : query_string} #Skulle vilja ha tillgång till titel för att kunna söka på det
        },
        "knn":{
                    "field": "vector",  # Field containing the vectors
                    "query_vector": model.encode(query_string).tolist(),  # Vector for similarity search
                    #"k": 10,
                    "num_candidates": 100,
                    "boost": 2.0
            
            },
            "_source": ["id", "transcript"],
        
        }

    # Perform the search
    #response = client.search(index=INDEX, body=query)


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
    index_mapping = {
        "mappings": {
            "properties": {
                "transcript": {"type": "text"},
                "vector": {"type": "dense_vector"}
            }
        }
    }

    # Create index with mapping
    client.indices.create(index=index_name, body=index_mapping) #Ska kanske vara document
    print(f"Index '{index_name}' created successfully.")

"""def index_transcripts_from_folder(folder_path, index_name):
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
                            vector = model.encode(transcript)
                            # Ensure vector is a list, as expected by Elasticsearch
                            contents = {"transcript": transcript, "vector": vector.tolist()}
                            client.index(index=index_name, body=contents)
                        except KeyError:
                            pass
            number_of_files += 1"""



"""def display_number_of_hits(response):
    print("Number of results:", response['hits']['total']['value'])


def get_number_of_hits(response):
    #score_threshold = 0.5
    return str(len([hit for hit in response['hits']['hits'] if hit['_score'] > score_threshold]))"""

def display_number_of_hits(response):
    print("Number of results:", response['hits']['total']['value'])


def get_number_of_hits(response):
    return response['hits']['total']['value']


def print_first_n_results(response, n=10):
    n = min(n,get_number_of_hits(response))
    for hit in response['hits']['hits'][:n]:
        transcript = hit['_source']["transcript"]
        print("-" * 30)
        print("Score:", hit["_score"])
        print("Transcript: " + transcript)
        print("-" * 30 + "\n")


def get_first_n_results(response, n=10):
    #score_threshold = 0.5
    print("LÄngd " + str(len([hit for hit in response['hits']['hits'] if hit['_score'] > score_threshold])))
    results = []
    for hit in response['hits']['hits'][:n]: #är detta sorterat??
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
client = Elasticsearch(ADDRESS, verify_certs=False, ca_certs=CA_CERT, http_auth=(USERNAME, ELASTIC_PASSWORD))
"""client = Elasticsearch(
    [ADDRESS],
    verify_certs=True,  # Set to True by default, but include for clarity
    ca_certs=CA_CERT,   # Specify the path to the CA certificate file
    http_auth=(USERNAME, ELASTIC_PASSWORD)  # Provide the username and password for basic authentication
)"""