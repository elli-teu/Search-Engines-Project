ADDRESS = "https://129.151.196.60:9200"
API_KEY = "dklrT01vOEJoZHJJOEFESnM1UGU6VDdmT1JVVVlUZW1pYUl6NTYtS3dYQQ=="
INDEX_TRANSCRIPTS = "podcast_transcripts"
INDEX_EPISODES = "podcast_episodes"
INDEX_SHOWS = "podcast_shows"
DATASET_FOLDER = "dataset/spotify/spotify-podcasts-2020/" # Make sure this is path to the folder containing "podcasts-transcripts", "show-rss" and "metadata.tsv"
TRANSCRIPT_LENGTH = 125
MATRYOSHKA_DIM = 256

### INDEX MAPPINGS

## transcripts
transcript_mappings = {
        "properties": {
            "transcript": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "show_id": {
                "type": "text",
            },
            "vector": {
                "type": "dense_vector",
                "dims": MATRYOSHKA_DIM,
                "index": True,
                "similarity": "dot_product",
                "index_options": {
                    "type": "int8_hnsw",
                    "m": 16,
                    "ef_construction": 100
                }
            },
            "starttime": {
                "type": "float",
            },
            "endtime": {
                "type": "float",
            }
        }
    }

## episodes
episodes_mappings = {
        "properties": {
            "show": {
                "type": "text",
            },
            "episode_name": {
                "type": "text",
            },
            "episode_description": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            }
        }
    }

## shows
shows_mappings = {
        "properties": {
            "show_name": {
                "type": "text",
            },
            "image": {
                "type": "text",
            },
            "link": {
                "type": "text",
            },
            "publisher": {
                "type": "text",
            },
            "show_description": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            }
        }
    }
