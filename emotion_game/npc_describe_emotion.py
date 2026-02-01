from emotion_game.build_agreed_prompt import build_agreed_prompt
from phase_2_queries import update_NPC_user_memory_query
from streamNPCresponse.streamTextResponse import streamResponse
from flask import jsonify
from llm_client import client
from sockets import socketio
from turnContext import EmotionGameTurn


def npc_describe_emotion(turn: EmotionGameTurn) -> str:
    try:
        # intro prompt for emotional eq game
        turn.prompt = build_agreed_prompt(turn)
        # stream response from openAI
        turn.last_npc_text = streamResponse(turn,client=client)
        # debug
        print("\nNPC DESCRIBE EMOTION RESPONSE: ", turn.last_npc_text)
        # update npcs kb with its own response
        turn.npc_memory = f"[You just responded to {turn.player_name} with:] '{turn.last_npc_text}'"
        update_NPC_user_memory_query(turn)

        socketio.emit(
            "npc_responded",
            {"text": turn.last_npc_text},
            room=f"user:{turn.idUser}")
        
        print("\n LAST NPC RESPONSE", turn.last_npc_text)

        return jsonify({
            "success": True,
            "npc_text": turn.last_npc_text
        }), 200
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500