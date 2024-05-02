from flask import Flask, request, jsonify, render_template
import search
import re
app = Flask(__name__)


def search_query(query):
    query = search.generate_query(query, search.QueryType.smart_query)
    query_response = search.execute_query(query, n=50)
    results = search.get_first_n_results(query_response, n=50)
    metadata = search.get_transcript_metadata(results)
    for res, data in zip(results, metadata):
        res["transcript"] = str("...") + res["transcript"] + str("...")
        res["podcast_name"] = data["podcast_name"]
        res["podcast_description"] = data["podcast_description"]
        res["publisher"] = data["publisher"]
        res["episode_name"] = data["episode_name"]
        res["episode_description"] = data["episode_description"]
        res["image"] = data["image"]

        m, s = divmod(res["starttime"], 60)
        h, m = divmod(m, 60)
        time_string = ""
        if h != 0:
            time_string += f"{int(h)}h:"
        time_string += f"{int(m)}m:"
        time_string += f"{int(s)}s"
        res["starttime"] = time_string

        url_pattern = re.compile(
            r'(^(?:http|https)://)?'  # http:// or https://
            r'(?:www\.)?'  # Optional "www." subdomain
            r'([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})'  # Domain name
            r'(?::\d+)?'  # Optional port number
            r'(?:/?|[/?]\S+)$',  # Optional path
            re.IGNORECASE
        )
        valid_url = url_pattern.match(data["link"])
        if valid_url is None:
            res["link"] = "null"
            # Query that results in top result having an invalid url.
            # big is this cat that he's enormous hip over 7 months old
        else:
            if not data["link"].startswith("http"):
                res["link"] = "//" + data["link"]
            else:
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
