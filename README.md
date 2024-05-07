<div style="text-align: center;">

# PodysseyCast

<img src="SearchGUI/static/images/icon.png" alt="PodysseyCast Logo" width="100" height="100">

</div>


## Authors
- Carl Bentzer
- Simon Granström
- Joar Gunnarsson
- Ellinor Teurnberg

## Usage
In order to create an instance of this search engine, complete these steps:
- Install elasticsearch and obtain an API key.
- Index the data into the three indexes using the %TODO file.
- Change the contents of ``/SearchGUI/setup.py`` to include your API key and elasticsearch host adress.
- Run the file ``/SearchGUI/app.py``. 
- The website can now be accessed by typing ``http://192.168.1.121:8000`` into the search bar in any web browser, on any device connected to your network.
- In order to access the website from another network, you need to configure your router to forward all traffic on port 8000 to the machine running the ``flask`` server.


## Features
- Some features
