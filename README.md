<div style="text-align: center;">

# PodysseyCast

<img src="SearchGUI/static/images/icon.png" alt="PodysseyCast Logo" width="100" height="100">

Visit our website at: http://www.podysseycast.se
In case that the domain is no longer available, try: http://129.151.196.60/

</div>


## Authors
- Carl Bentzer
- Simon Granström
- Joar Gunnarsson
- Ellinor Teurnberg

## Usage
In order to create an instance of this search engine, complete these steps:

### Elasticsearch
- Install elasticsearch and obtain an API key.

### Indexer
Start by editing the ``Indexer/setup.py`` file, you need to change the following:
* ``ADDRESS`` Address to your elastic search server
* ``API_KEY`` API key used to authenticate to your elastic search server
* ``DATASET_FOLDER`` path to your dataset folder, must comply with the spotify specifications (folder structure)
  
Once you have that setup, you can run the ``Indexer/index_dataset.py`` script to start indexing your data.
Once that is complete, run ``Indexer/fix_show_links.py`` to add ``pod_link`` and ``episode_links`` into your database.

The reason why this ``Indexer/fix_show_links.py`` script exists is because we added this after indexing and have not had the time to incoperate it into the main ``Indexer/index_dataset.py`` script.


### Web gui
- Change the contents of ``/SearchGUI/setup.py`` to include your API key and elasticsearch host adress.
- Obtain an OpenAI API key and replace the API key in ``/SearchGUI/setup.py`` for the chat client.
- Run the file ``/SearchGUI/app.py``. 
- The website can now be accessed by typing ``http://192.168.1.121:8000`` into the search bar in any web browser, on any device connected to your network.
- In order to access the website from another network, you need to configure your router to forward all traffic on port 8000 to the machine running the ``flask`` server.
