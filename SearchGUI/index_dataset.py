import search
import setup

search.create_index(setup.INDEX)
search.index_transcripts_from_folder(setup.DATASET_FOLDER, setup.INDEX)
