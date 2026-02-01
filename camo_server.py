from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from emotionGameQueries import *
from phase_2_queries import *
from elevenlabsQueries import *
import openAIqueries
import os
from sockets import socketio, init_socket_events
from llm_client import client
from emotion_game.npc_introduce import npc_introduce, agree_check, player_disagreed
from emotion_game.npc_describe_emotion import npc_describe_emotion
from emotion_game.player_guess import player_guess
from turnContext import EmotionGameTurn

#------------------------------------------------------------------
AUDIO_DIR = "./tts_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)
speechOn = False  # set to false to save 11 lab tokens
#------------------------------------------------------------------
load_dotenv()
camo = Flask(__name__)
CORS(camo)                      # allow anything to access this API
init_socket_events(camo)

#------------------------------------------------------------------
# ROUTES FOR EMOTIONS GAME
#------------------------------------------------------------------
@camo.route("/npc_introduce", methods=["POST"])  
def introduce_npc():
    return npc_introduce()
#------------------------------------------------------------------
@camo.route("/player_agreed_check", methods=["POST"])  
def player_agreed_check():
    return ("", 200) if agree_check() else ("", 400)
#------------------------------------------------------------------
@camo.route("/player_not_agreed", methods=["POST"])
def player_not_agreed():
    return player_disagreed()
#------------------------------------------------------------------
@camo.route("/player_guess", methods=["POST"])
def pl_guess():
    return ("", 200) if player_guess() else ("", 400)
#------------------------------------------------------------------
@camo.route("/assign_next_emotion", methods=["POST"])
def assign_n_e():

    data = request.json

    turn = EmotionGameTurn(
        idNPC=data["idNPC"],
        idUser=data["idUser"],
        current_scene=data["curScene"],
        player_name=data["pName"],
        game_started=data["game_started"]
    )

    emotion = assign_next_emotion(turn)
    turn.cues = openAIqueries.get_cues_for_emotion(emotion=emotion, client=client)
    npc_describe_emotion(turn)

    print("\nEMOTION ASSIGNED: ", emotion)
    print("\nCUES ASSIGNED: ", turn.cues)

    return jsonify({"status" : "success"}), 200
#------------------------------------------------------------------
# PHASE 2 ROUTES
#------------------------------------------------------------------
@camo.route("/tts_audio/<audio_id>", methods=["GET"])
def tts_audio(audio_id):
    path = f"{AUDIO_DIR}/{audio_id}.mp3"
    return send_file(path, mimetype="audio/mp3")
#------------------------------------------------------------------
@camo.route("/match_choice", methods=["POST"])      # phase 2 query 
def match_choice():
    return openAIqueries.match_choice_query(client)
#------------------------------------------------------------------
@camo.route("/update_NPC_user_mem", methods=["POST"]) 
def update_NPC_user_memory():
    data    = request.json
    idNPC  = data["idNPC"] 
    idUser = data["idUser"]
    kbText = data["kbText"]
    return update_NPC_user_memory_query(idNPC=idNPC, idUser=idUser, kbText=kbText)
#------------------------------------------------------------------
@camo.route("/get_NPC_user_mem", methods=["POST"]) 
def get_NPC_user_memory():
    data    = request.json
    idNPC  = data["idNPC"] 
    idUser = data["idUser"]
    return get_NPC_user_memory_query(idUser=idUser, idNPC=idNPC)
#------------------------------------------------------------------

if __name__ == "__main__":
    socketio.run(camo, host="0.0.0.0", port=5001, debug=True, use_reloader=True)