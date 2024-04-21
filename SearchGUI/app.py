from flask import Flask, request, jsonify, render_template
import search
app = Flask(__name__)


def search_query(query):
    query = search.generate_query(query, search.QueryType.smart_query)
    response = search.execute_query(query, n=10)
    results = search.get_first_n_results(response, n=10)
    # Implement your search logic here
    # This could be searching in a database, using a library like Whoosh, or any other method
    for res in results:
        metadata = search.get_transcript_metadata(res)
        res["podcast_name"] = metadata["podcast_name"]
        res["podcast_description"] = metadata["podcast_description"]
        res["publisher"] = metadata["publisher"]
        res["episode_name"] = metadata["episode_name"]
        res["episode_description"] = metadata["episode_description"]
        res["image"] = metadata["image"]  # "https://i.guim.co.uk/img/media/43352be36da0eb156e8551d775a57fadba8ae6d7/0_0_1440_864/master/1440.jpg?width=1200&height=1200&quality=85&auto=format&fit=crop&s=1829611852af3ffc6460b4068e20bcbc"
        res["link"] = metadata["link"]  # "https://open.spotify.com/show/54W3NtZwf5ImPtPO8B4CMy?si=e8ea2898e2914e0a"
    return results


@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'GET':
        return render_template('result.html', results=[])

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
    app.run(host="0.0.0.0", port=8000, debug=True)
