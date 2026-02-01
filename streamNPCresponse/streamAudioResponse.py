from camo_server import socketio, build_prompt
from elevenlabsQueries import tts
import openAIqueries
import os, uuid
import base64
import hashlib

AUDIO_DIR = "./tts_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)
#------------------------------------------------------------------
# API Routes
#------------------------------------------------------------------
# helper method
def saveAudio(audio):
    audio = b"".join(audio)
    audio_id = str(uuid.uuid4())
    path = f"{AUDIO_DIR}/{audio_id}.mp3"
    with open(path, "wb") as f:
        f.write(audio)
    return {"audio_id": audio_id}, 200
#------------------------------------------------------------------
def audioStreamResponse(
        idNPC, idUser, idVoice, emotion_name, sentence_buffer, SENTENCE_END,
    ):
    if (sentence_buffer.strip() and 
        sentence_buffer.strip()[-1] in SENTENCE_END
        ):
        if not speaking_emitted:
            socketio.emit(
                "npc_speaking",
                {"idNPC": idNPC, "state": True},
                room=f"user:{idUser}"
            )
            speaking_emitted = True

        for audio_chunk in tts_cached(
            sentence_buffer, idVoice, emotion_name
        ):
            payload = base64.b64encode(audio_chunk).decode("utf-8")
            socketio.emit(
                "npc_audio_chunk",
                {"audio_b64": payload},
                room=f"user:{idUser}"
            )
            socketio.sleep(0)
        sentence_buffer = ""
    # ----------------------------------------------------------
    # flush remaining text
    # ----------------------------------------------------------
    if sentence_buffer.strip():
        if not speaking_emitted:
            socketio.emit(
                "npc_speaking",
                {"idNPC": idNPC, "state": True},
                room=f"user:{idUser}"
            )
            speaking_emitted = True
        for audio_chunk in tts_cached(
            sentence_buffer, idVoice, emotion_name
        ):
            payload = base64.b64encode(audio_chunk).decode("utf-8")
            socketio.emit(
                "npc_audio_chunk",
                {"audio_b64": payload},
                room=f"user:{idUser}"
            )
            socketio.sleep(0)
    # ----------------------------------------------------------
    # done sending
    # ----------------------------------------------------------
    socketio.emit("npc_audio_done", {}, room=f"user:{idUser}")


#------------------------------------------------------------------
def streamResponse(prompt, curScene, pName, idUser, client) -> str:
    full_text = []
    sentence_buffer = ""
    speaking_emitted = False
    # ----------------------------------------------------------
    # stream text
    # ----------------------------------------------------------
    for token in openAIqueries.getResponseStream (
        prompt, curScene, pName, client
    ):
        full_text.append(token)
        sentence_buffer += token
        socketio.emit(
            "npc_text_token",
            {"token": token},
            room=f"user:{idUser}"
        )
        socketio.sleep(0)
    # ----------------------------------------------------------
    # done sending
    # ----------------------------------------------------------
    socketio.emit("npc_text_done", {}, room=f"user:{idUser}")
    return "".join(full_text)
#------------------------------------------------------------------
# NPC INTERACT HELPERS
#
# cache for 11 labs
#------------------------------------------------------------------
def tts_cache_key(text, voice_id, emotion):
    text = text.strip()
    raw = f"{voice_id}|{emotion}|{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
#------------------------------------------------------------------
def tts_cached(text, voice_id, emotion):
    key = tts_cache_key(text, voice_id, emotion)
    path = f"{AUDIO_DIR}/{key}.mp3"

    if os.path.exists(path):
        with open(path, "rb") as f:
            while True:
                chunk = f.read(32_768)  # 32KB
                if not chunk:
                    break
                print("USING CACHE!")
                yield chunk
        return

    audio_chunks = []
    for chunk in tts(text, voice_id, emotion):
        audio_chunks.append(chunk)
        yield chunk

    with open(path, "wb") as f:
        f.write(b"".join(audio_chunks))
def build_NPC_prompt(idUser, idNPC):
    prompt = build_prompt(idUser=idUser, idNPC=idNPC)
    return prompt