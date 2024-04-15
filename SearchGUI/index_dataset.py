import search
import setup

search.create_index(setup.INDEX)
#search.index_transcripts_from_folder(setup.DATASET_FOLDER, setup.INDEX)

search.create_index(setup.EPISODEINDEX)
search.create_index(setup.SHOWINDEX)
search.index_transcripts_with_metadata_from_folder(setup.DATASET_FOLDER, setup.INDEX, setup.METADATA_PATH, setup.EPISODEINDEX, setup.SHOWINDEX)
