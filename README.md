# Search-Engines-Project

## Indexer
Start by editing the setup.py file in the Index/ folder, you need to change the following:
* ADDRESS := Address to your elastic search server
* API_KEY := API key used to authenticate to your elastic search server
* DATASET_FOLDER := path to your dataset folder, must comply with the spotify specifications (folder structure)
  
Once you have that setup, you can run the index_dataset.py script, in the Index/ folder, to start indexing your data.
Once that is complete, run fix_show_links.py, in the Index/ folder, to add pod_link and episode_links into your database.

The reason why this fix_show_links.py script exists is because we added this after indexing and have not had the time to incoperate it into the main index_dataset.py script.
