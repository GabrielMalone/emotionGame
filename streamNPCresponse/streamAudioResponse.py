from sockets import socketio
from elevenlabsQueries import tts
import os, uuid
import base64

AUDIO_DIR = "./tts_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)
#------------------------------------------------------------------
# API Routes
#------------------------------------------------------------------
#------------------------------------------------------------------
def audioStreamResponse(idNPC, idUser, idVoice, emotion_name, sentence):
    socketio.emit(
        "npc_speaking",
        {"idNPC": idNPC, "state": True},
        room=f"user:{idUser}"
    )

    for audio_chunk in tts(sentence, idVoice, emotion_name):
        payload = base64.b64encode(audio_chunk).decode("utf-8")
        socketio.emit(
            "npc_audio_chunk",
            {"audio_b64": payload},
            room=f"user:{idUser}"
        )
        socketio.sleep(0)

    socketio.emit("npc_audio_done", {}, room=f"user:{idUser}")