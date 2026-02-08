from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os

from sockets import sio, init_socket_events
from llm_client import client
import openAIqueries
from emotionGameQueries import *
from phase_2_queries import *

# --------------------------------------------------
load_dotenv()
AUDIO_DIR = "./tts_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)

camo = Flask(__name__)
CORS(camo)
init_socket_events(camo)

# --------------------------------------------------
# UTILITY ROUTES (keep these)
# --------------------------------------------------
@camo.route("/tts_audio/<audio_id>", methods=["GET"])
def tts_audio(audio_id):
    return send_file(f"{AUDIO_DIR}/{audio_id}.mp3", mimetype="audio/mp3")

@camo.route("/match_choice", methods=["POST"])
def match_choice():
    return openAIqueries.match_choice_query(client)

@camo.route("/update_NPC_user_mem", methods=["POST"])
def update_NPC_user_memory():
    data = request.json
    return update_NPC_user_memory_query(
        idNPC=data["idNPC"],
        idUser=data["idUser"],
        kbText=data["kbText"]
    )

@camo.route("/get_NPC_user_mem", methods=["POST"])
def get_NPC_user_memory():
    data = request.json
    return get_NPC_user_memory_query(
        idUser=data["idUser"],
        idNPC=data["idNPC"]
    )

# --------------------------------------------------
if __name__ == "__main__":
    sio.run(camo, host="0.0.0.0", port=5001, debug=True)