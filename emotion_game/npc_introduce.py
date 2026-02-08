from phase_2_queries import update_NPC_user_memory_query
from streamNPCresponse.streamTextResponse import streamResponse
from emotionGameQueries import get_active_emotion
import openAIqueries
from emotion_game.build_intro_prompt import build_intro_prompt
from emotion_game.build_disagree_prompt import build_disagree_prompt
from emotion_game.get_NPC_mem import getNPCmem
from flask import request, jsonify
from llm_client import client
from turnContext import EmotionGameTurn
from emotion_game.player_guess import player_guess
#------------------------------------------------------------------
import os
import mysql.connector
from turnContext import EmotionGameTurn
#------------------------------------------------------------------
def connect()->object:
    return mysql.connector.connect(
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PASSWORD'), 
        database=os.getenv('DB_NAME'),
        host=os.getenv('DB_HOST', 'localhost') )
#---------------------------------------------------------------------------------
def npc_introduce(turn: EmotionGameTurn, sio):

    db = connect()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
        CASE
            WHEN COUNT(*) > 0
            AND COUNT(*) = SUM(guessed_correctly = 1)
            THEN 1
            ELSE 0
        END AS all_emotions_guessed_correctly
        FROM emotion_guess_game
        WHERE idUser = %s
        AND idNPC = %s;
    """, (turn.idUser, turn.idNPC))
    gameOver = cursor.fetchone()

    if gameOver["all_emotions_guessed_correctly"] == 1:
        turn.game_over = True
        player_guess(turn, sio)
        return
        
    # start out worried for this scenario
    turn.cur_npc_emotion = "worried"
    # intro prompt for emotional eq game
    turn.prompt = build_intro_prompt(turn)
    # stream response from openAI
    r = streamResponse(turn, client=client, sio=sio)
    # debug
    print("\nNPC INTRO RESPONSE: ", r)
    # update npcs kb with its own response
    turn.npc_memory = f"[You just greeted {turn.player_name} with:] '{r}'"
    update_NPC_user_memory_query(turn)
    sio.emit(
        "npc_responded",
        {"text": r},
        room=f"user:{turn.idUser}")

#---------------------------------------------------------------------------------
def agree_check(turn: EmotionGameTurn)-> bool:
    turn.npc_memory = getNPCmem(turn)
    return openAIqueries.classify_player_response_to_game_start(turn, client)
#---------------------------------------------------------------------------------
def player_disagreed(turn: EmotionGameTurn, sio):
    
    # update NPC's mem of player's response
    turn.npc_memory = f"[Player just disagreed to play with you by saying] '{turn.player_text}'"
    mem = getNPCmem(turn)
    update_NPC_user_memory_query(turn)
    turn.npc_memory = mem
    turn.prompt = build_disagree_prompt(turn)
    turn.last_npc_text = streamResponse(turn, client=client, sio=sio)
    print("\nPLAYER's DISAGREEMENT: ", turn.player_text)
    sio.emit(
        "npc_responded",
        {"text": turn.last_npc_text},
        room=f"user:{turn.idUser}")
