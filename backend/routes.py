from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health", methods=["GET"])
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count", methods=["GET"])
def count():
    """return length of data"""
    count = db.songs.count_documents({})
    return jsonify(count=count), 200

@app.route("/song", methods=["GET"])
def songs():
    """Return all songs"""
    results = db.songs.find({})
    return json_util.dumps({"songs": list(results)}), 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    """Return a specific song by id"""
    song = db.songs.find_one({"id": id})
    if song:
        return json_util.dumps(song), 200
    return jsonify({"message": "song with id not found"}), 404

@app.route("/song", methods=["POST"])
def create_song():
    """Create a new song"""
    song_in = request.get_json()
    
    # Check if song with this id already exists
    song = db.songs.find_one({"id": song_in["id"]})
    if song:
        return jsonify({"Message": f"song with id {song_in['id']} already present"}), 302
    
    # Add the new song to the data list
    result = db.songs.insert_one(song_in)
    return json_util.dumps({"inserted id": result.inserted_id}), 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    """Update an existing song"""
    song_in = request.get_json()
    
    # Find and update the song
    song = db.songs.find_one({"id": id})
    if song:
        result = db.songs.update_one({"id": id}, {"$set": song_in})
        if result.modified_count == 0:
            return jsonify({"message": "song found, but nothing updated"}), 200
        else:
            updated_song = db.songs.find_one({"id": id})
            return json_util.dumps(updated_song), 201
    
    # Song not found
    return jsonify({"message": "song not found"}), 404

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    """Delete a song by id"""
    # Find and delete the song
    result = db.songs.delete_one({"id": id})
    if result.deleted_count > 0:
        return "", 204
    
    # Song not found
    return jsonify({"message": "song not found"}), 404
