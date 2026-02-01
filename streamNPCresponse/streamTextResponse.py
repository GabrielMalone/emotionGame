import openAIqueries
from sockets import socketio
from turnContext import EmotionGameTurn

def streamResponse(t: EmotionGameTurn, client) -> str:
    full_text = []
    sentence_buffer = ""
    speaking_emitted = False
    # ----------------------------------------------------------
    # stream text
    # ----------------------------------------------------------
    for token in openAIqueries.getResponseStream (t, client):
        full_text.append(token)
        sentence_buffer += token
        socketio.emit(
            "npc_text_token",
            {"token": token},
            room=f"user:{t.idUser}"
        )
        socketio.sleep(0)
    # ----------------------------------------------------------
    # done sending
    # ----------------------------------------------------------
    socketio.emit("npc_text_done", {}, room=f"user:{t.idUser}")
    return "".join(full_text)