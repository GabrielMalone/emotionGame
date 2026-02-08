
from elevenlabsQueries import tts
import os
import base64

AUDIO_DIR = "./tts_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)
#------------------------------------------------------------------
# API Routes
#------------------------------------------------------------------
#------------------------------------------------------------------
def audioStreamResponse(idNPC, idUser, idVoice, emotion_name, sentence, sio):
    sio.emit(
        "npc_speaking",
        {"idNPC": idNPC, "state": True},
        room=f"user:{idUser}"
    )

    for audio_chunk in tts(sentence, idVoice, emotion_name):
        payload = base64.b64encode(audio_chunk).decode("utf-8")
        sio.emit(
            "npc_audio_chunk",
            {"audio_b64": payload},
            room=f"user:{idUser}"
        )
        sio.sleep(0)

    sio.emit("npc_audio_done", {}, room=f"user:{idUser}")