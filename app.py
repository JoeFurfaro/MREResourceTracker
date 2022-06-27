from tracker import loadTracker
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import os


app = Flask(__name__, static_folder='app/qoh/build')

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/tracker/<resource>")
def tracker(resource):
    try:
        data = loadTracker([resource])
        if data == []:
            return '',404
        return jsonify(data)
    except Exception as e:
        print(e)
        return '',500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

app.run(debug=True, host="10.99.0.146", port=9009)