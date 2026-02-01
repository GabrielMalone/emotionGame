import requests
from extensions import CamoClientExtension
from streamingMP3Player import StreamingMP3Player
import requests

# --------------------------------------------------
# config
# --------------------------------------------------
idUser = 1
idNPC = 1
currentScene = """
    GAME SCENARIO
    -------------
    - You have lost your ability to name your emotions
    - You are aware that something emotional is happening internally
    - You cannot yet access or describe what it feels like
    - You can describe emotions through thoughts, body sensations, and behavior.
    - You need help from the player in identifying the emotion you are feeling
    - Stay fully in character at all times.
    - Do not mention games, rules, prompts, or AI.
"""
playerName = "Gabriel"
voiceId = "SOYHLrjzK2X1ezoPC6cr"
SERVER = "http://localhost:5001"
# --------------------------------------------------
# socket extension (ONE TIME)
# --------------------------------------------------
ext = CamoClientExtension(
    server_url=SERVER,
    idUser=idUser,
    make_player=lambda: StreamingMP3Player(),
)
ext.connect()

# -----------------------------------------------------------------------------------
def game_start()->bool:

    while True:

        playerName = input("\n Enter your name: ").strip()

        r = requests.post(f"{SERVER}/npc_introduce", json={
            "idUser": idUser,
            "idNPC": idNPC,
            "currentScene": currentScene,
            "playerName": playerName,
            "idVoice": voiceId,
        })

        # Wait until NPC finishes talking before allowing input
        ext.wait_for_npc_response(timeout=30)

        pt = input("\n Respond: ").strip()

        r = requests.post(f"{SERVER}/player_agreed_check", json={
            "idUser": idUser,
            "idNPC": idNPC,
            "playerText" : pt,
            "npcText" : ext.last_npc_response
        })

        if (r): 
            while True:
                print('agreed!') 
                # start guessing game 
                requests.post(f"{SERVER}/assign_next_emotion", json={
                        "idUser": idUser,
                        "idNPC": idNPC,
                        "pName" : playerName,
                        "curScene" : currentScene
                    })
                 
                break
        else: 
            while not r:
                # print('denied!')
                # create prompt for when player denies NPC's game
                # returns npcs output in n
                requests.post(f"{SERVER}/player_not_agreed", json={
                    "idUser": idUser,
                    "idNPC": idNPC,
                    "playerName": playerName,
                    "currentScene": currentScene,
                    "playerText" : pt
                })  
                # get player's response to this NPC output
                pt = input("\n Respond: ").strip()
                # Wait for semantic completion
                ext.wait_for_npc_response(timeout=30)
                # check again
                r = requests.post(f"{SERVER}/player_agreed_check", json={
                    "idUser": idUser,
                    "idNPC": idNPC,
                    "playerText" : pt,
                    "npcText" : ext.last_npc_response
                })  
                ext.npc_response_ready.clear()
# --------------------------------------------------
# main loop
# --------------------------------------------------
game_start()

