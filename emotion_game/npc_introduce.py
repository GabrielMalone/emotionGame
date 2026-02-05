from phase_2_queries import update_NPC_user_memory_query
from streamNPCresponse.streamTextResponse import streamResponse
from emotionGameQueries import get_active_emotion
import openAIqueries
from emotion_game.build_intro_prompt import build_intro_prompt
from emotion_game.build_disagree_prompt import build_disagree_prompt
from emotion_game.get_NPC_mem import getNPCmem
from flask import request, jsonify
from llm_client import client
from sockets import socketio
from turnContext import EmotionGameTurn

#---------------------------------------------------------------------------------
def npc_introduce():
    try:

        data = request.json
        turn = EmotionGameTurn (
            player_name   = data["playerName"],
            idNPC         = data["idNPC"],
            idUser        = data["idUser"],
            current_scene = data["currentScene"],
            voiceId       = data["idVoice"]
        )
        turn.cur_npc_emotion = "worried"

        # intro prompt for emotional eq game
        turn.prompt = build_intro_prompt(turn)
        # stream response from openAI
        r = streamResponse(turn, client=client)
        # debug
        print("\nNPC INTRO RESPONSE: ", r)
        # update npcs kb with its own response
        turn.npc_memory = f"[You just responded to {turn.player_name} with:] '{r}'"
        update_NPC_user_memory_query(turn)
        socketio.emit(
            "npc_responded",
            {"text": r},
            room=f"user:{turn.idUser}")
        
        return jsonify({
            "success": True,
            "npc_text": r
        }), 200
            
    except Exception as e:

        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
    
#---------------------------------------------------------------------------------
def agree_check()-> bool:
    data = request.json
    turn = EmotionGameTurn(
        idNPC           = data["idNPC"],
        idUser          = data["idUser"],
        player_text     = data["player_text"],
        last_npc_text   = data["npcText"],
        voiceId         = data["idVoice"]
    )
    # print("\nLAST NPC RESPONSE: ", turn.last_npc_text)
    turn.npc_memory = getNPCmem(turn)
    return openAIqueries.classify_player_response_to_game_start(turn, client)
#---------------------------------------------------------------------------------
def player_disagreed():
    try:
        data = request.json
        turn = EmotionGameTurn(
            player_name     = data["playerName"],
            idNPC           = data["idNPC"],
            idUser          = data["idUser"],
            current_scene   = data["currentScene"],
            player_text     = data["player_text"],
            voiceId         = data["idVoice"]
        )

        # update NPC's mem of player's response
        turn.npc_memory = f"[Player just disagreed to play with you by saying] '{turn.player_text}'"
        mem = getNPCmem(turn)
        update_NPC_user_memory_query(turn)
        turn.npc_memory = mem
        turn.prompt = build_disagree_prompt(turn)
        turn.last_npc_text = streamResponse(turn, client=client)
        # debug
        print("\nPLAYER's DISAGREEMENT: ", turn.player_text)
        socketio.emit(
            "npc_responded",
            {"text": turn.last_npc_text},
            room=f"user:{turn.idUser}")
        
        return jsonify({"success": True}), 200
    
    except Exception as e:

        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
