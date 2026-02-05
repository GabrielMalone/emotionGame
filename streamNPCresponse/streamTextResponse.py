import openAIqueries
from sockets import socketio
from turnContext import EmotionGameTurn
from elevenlabsQueries import tts_cached
import base64

def streamResponse(t: EmotionGameTurn, client) -> str:
    full_text = []
    sentence_buffer = ""
    SENTENCE_END = {".", "?", "!"}
    speaking_emitted = False
    speechOn = True
    # ----------------------------------------------------------
    # stream text + audio
    # ----------------------------------------------------------
    for token in openAIqueries.getResponseStream(t, client):
        full_text.append(token)
        sentence_buffer += token

        socketio.emit(
            "npc_text_token",
            {"token": token},
            room=f"user:{t.idUser}"
        )
        socketio.sleep(0)

        if (
            speechOn
            and sentence_buffer.strip()
            and sentence_buffer.strip()[-1] in SENTENCE_END
        ):
            if not speaking_emitted:
                socketio.emit(
                    "npc_speaking",
                    {"idNPC": t.idNPC, "state": True},
                    room=f"user:{t.idUser}"
                )
                speaking_emitted = True

            for audio_chunk in tts_cached(
                sentence_buffer, t.voiceId, t.cur_npc_emotion
                ):
                payload = base64.b64encode(audio_chunk).decode("utf-8")
                socketio.emit(
                    "npc_audio_chunk",
                    {"audio_b64": payload},
                    room=f"user:{t.idUser}"
                )
                socketio.sleep(0)

            sentence_buffer = ""

    # ----------------------------------------------------------
    # flush remaining text
    # ----------------------------------------------------------
    if speechOn and sentence_buffer.strip():
        if not speaking_emitted:
            socketio.emit(
                "npc_speaking",
                {"idNPC": t.idNPC, "state": True},
                room=f"user:{t.idUser}"
            )
            speaking_emitted = True

        for audio_chunk in tts_cached(
            sentence_buffer, t.voiceId, t.cur_npc_emotion
        ):
            payload = base64.b64encode(audio_chunk).decode("utf-8")
            socketio.emit(
                "npc_audio_chunk",
                {"audio_b64": payload},
                room=f"user:{t.idUser}"
            )
            socketio.sleep(0)
    # ----------------------------------------------------------
    # done sending
    # ----------------------------------------------------------
    socketio.emit("npc_text_done", {}, room=f"user:{t.idUser}")
    socketio.emit("npc_audio_done", {}, room=f"user:{t.idUser}")
    # ----------------------------------------------------------
    # done sending
    # ----------------------------------------------------------
    return "".join(full_text)




