from flask import Flask, request, jsonify, render_template
import search
app = Flask(__name__)


def search_query(query):
    query = search.generate_query(query, search.QueryType.smart_query)
    response = search.execute_query(query, n=1000)
    results = search.get_first_n_results(response, n=1000)
    # Implement your search logic here
    # This could be searching in a database, using a library like Whoosh, or any other method
    final_results = []
    for res in results:
        res["podcast_name"] = "Animals"
        res["podcast_description"] = "This is a podcast about animals"
        res["episode_name"] = "The cat episode"
        res["episode_description"] = "In this episode we will talk about cats."
        res["image"] = "https://i.guim.co.uk/img/media/43352be36da0eb156e8551d775a57fadba8ae6d7/0_0_1440_864/master/1440.jpg?width=1200&height=1200&quality=85&auto=format&fit=crop&s=1829611852af3ffc6460b4068e20bcbc"
        res["link"] = "https://open.spotify.com/show/54W3NtZwf5ImPtPO8B4CMy?si=e8ea2898e2914e0a"
    return results


@app.route('/result', methods=['POST'])
def result():
    query = request.form['query']

    # Process the search query (e.g., pass it to a Python function)
    # For example:
    # results = search_function(query)
    results = search_query(query)  # Dummy results
    return render_template('result.html', results=results)


@app.route('/')
def index():
    return render_template('start.html')


if __name__ == '__main__':
    app.run(debug=True)
