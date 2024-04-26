import json
from elasticsearch import Elasticsearch, client as cl
from elasticsearch.exceptions import NotFoundError
import os
from setup import ADDRESS, API_KEY, INDEX
import re
import openai
from sentence_transformers import SentenceTransformer
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# Filter out the specific warning about insecure HTTPS requests
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


# Filter out the specific warning about insecure HTTPS requests
#warnings.filterwarnings("ignore", category=InsecureRequestWarning)

#API KEY
"""sk-proj-GuRuVvdJbwlXDQuQuyH0T3BlbkFJlBwVGo5RnIufufuXhhwJ"""

chat_client = openai.OpenAI(
    # This is the default and can be omitted
    api_key='sk-proj-GuRuVvdJbwlXDQuQuyH0T3BlbkFJlBwVGo5RnIufufuXhhwJ',
)
messages = [ {"role": "system", "content":"Correct any spelling misstakes"} ] #För att initialisera gpt

sentences = ["This is an example sentence", "Each sentence is converted"]

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
embeddings = model.encode(sentences)
print("hi")
print(embeddings)

score_threshold = 0.7


class QueryType:
    union_query = "union"
    intersection_query = "intersection"
    phrase_query = "phrase"
    smart_query = "smart"
    vector_query = "vector"
    combi_query = "combi"
    new = "new"


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
                this_metadata["link"] = show["link"]
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
    intersection_boost = 0
    phrase_boost = 0.6
    union_boost = 0.2
    semantic_boost = 0.9
    confidence_boost = 1
    title_boost = 0.1
    auto = True
    window_size = 20
    rank_constant = 10

    if query_type == QueryType.smart_query:
        #Vill börja med att kolla om den innehåller något tecken, isf gör det här
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
        #Annars ska en vector search göras
        #Vi vill kunna skicka in lite olika parametrar
        
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
            
            res = client.search(index = INDEX, body = spelling_query, size= 50)
            #print(res)
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
        query = {
            "query": {
                "match": {"transcript": query_string}
            }
        }

        #Kan välja om vi ska kolla kolla allt med chat-gpt eller om vi ska kolla allt här först

        """query = { #Vill söka i titel här
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
                    "k": 10,
                    "num_candidates": 11,
                    "boost": 2.0
            
            },
            "_source": ["id", "transcript"],
        
        }"""
        print("där")
        cl.IndicesClient(client).refresh()
        print("här")
        query = { #Vill söka i titel här
        
        "knn":{
                    "field": "vector",  # Field containing the vectors
                    "query_vector": model.encode(query_string),  # Vector for similarity search
                    "k": 10,
                    "num_candidates": 10,
                    
            
            },
            "_source": ["show_id", "transcript"],
        
        }
        now = datetime.now()
        print("titta")
        model.encode(query_string),
        print(datetime.now()-now)
        print("hej")
        now = datetime.now()
        response = client.search(index = INDEX, body = query, size = 10, request_timeout = 10000)
        print(response['hits']['total']['value'])
        print(datetime.now()-now)

        print("hopp")
        #client.knn_search(index = INDEX, body = query, )
        print("tjolahopp")
    elif query_type == QueryType.new:
        if check_char(query_string) == True:
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
        else:
            tokens = get_tokens(query_string)
            must_occur_list = [{"term": {"transcript": token}} for token in tokens]
            
            if auto == True: #Ingår inte i gratis:(
                #do something
                query = {
                    "sub_searches": [
                        {
                            "query": {
                                "match": {"transcript": query_string}
                        }
                        },
                        {
                            "query": {
                                "bool": {
                                    "must": must_occur_list
                                }
                            }
                        }, 
                        {
                            "query": {
                                "match_phrase": {
                                    "transcript": query_string
                                }
                            }
                        }
                    ],
                    "rank": {
                       "rrf": {
                            "window_size": window_size,
                            "rank_constant": rank_constant
                        }
                    }
                }
                

            else:
                #do something
                query = {
    "query": {
        "function_score": {
            "query": {
                "bool": {
                    "should": [
                        { 
                            "match": {
                                "transcript": {
                                    "query": query_string,
                                    "boost": union_boost
                                }
                            }
                        },
                        {
                            "match_phrase": {
                                "transcript": {
                                    "query": query_string,
                                    "boost": phrase_boost
                                }
                            }
                        },
                        {
                            "bool": {
                                "must": must_occur_list,
                                "boost": intersection_boost
                    }
                },
                            
                    ],
                    
                }
            },
            "script_score": {
                "script": {
                    "source": "double confidence = doc['confidence'].value; return confidence * params.weight;",
                    "params": {
                        "weight": confidence_boost
                    }
                }
            }
        }
    }
}


                
                #"match": {"title" : query_string} #Skulle vilja ha tillgång till titel för att kunna söka på det
            
            

    else:
        raise ValueError(f"{query_type} is not a valid query type.")
    return query

def check_char(string):
    pattern = r"""["']([^"]*)["']|\\+|\\-"""
    match = re.search(pattern, string)
    return match is not None


def execute_query(query, n=10, index=INDEX):
    #return client.search(index=index, body=query, size=n, request_timeout=60)
    response = client.search(index=index, body=query,  request_timeout=10000)
    print(response['hits']['total']['value'])
    return response


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


def get_first_n_results(response, n=20):
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
