from flask import Flask, request, jsonify, render_template
import search
app = Flask(__name__)


def search_query(query):
    query = search.generate_query(query, search.QueryType.combi_query)
    query_response = search.execute_query(query, n=20)
    results = search.get_first_n_results(query_response, n=20)
    metadata = search.get_transcript_metadata(results)
    for res, data in zip(results, metadata):
        res["podcast_name"] = data["podcast_name"]
        res["podcast_description"] = data["podcast_description"]
        res["publisher"] = data["publisher"]
        res["episode_name"] = data["episode_name"]
        res["episode_description"] = data["episode_description"]
        res["image"] = data["image"]
        res["link"] = data["link"]

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
