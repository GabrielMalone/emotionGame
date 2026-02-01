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
    - Finding the name for an emotion will cause you to feel much better
    - Stay fully in character at all times.
    - Do not mention games, rules, prompts, or AI.
    - You must NEVER state or imply the name of the emotion.
    - You are strictly forbidden from using the following words, in any form or tense:
      happy, sad, angry, afraid, surprised, disgusted, calm, excited
    - Never begin a sentence with the word "This" by itself.
        Always use a clear noun phrase such as:
        "This feeling…", "What I’m feeling now…", or
        "The way my body feels right now…"
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
    gameStarted = False
    while True:

        if not gameStarted:
            playerName = input("\n Enter your name: ").strip()

            requests.post(f"{SERVER}/npc_introduce", json={
                "idUser": idUser,
                "idNPC": idNPC,
                "currentScene": currentScene,
                "playerName": playerName,
                "idVoice": voiceId,
            })

            # Wait until NPC finishes talking before allowing input
            ext.wait_for_npc_response(timeout=30)

            pt = input("\n Respond: ").strip()

            agreed = requests.post(f"{SERVER}/player_agreed_check", json={
                "idUser": idUser,
                "idNPC": idNPC,
                "playerText" : pt,
                "npcText" : ext.last_npc_response
            })

        if (agreed): 
            while True:
                print('agreed!') 
                gameStarted = True
                # start guessing game 
                requests.post(f"{SERVER}/assign_next_emotion", json={
                        "idUser": idUser,
                        "idNPC": idNPC,
                        "pName" : playerName,
                        "curScene" : currentScene
                    })
                return
                 
        else: 
            while not agreed:
                print('denied!')
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
                player_text = input("\n Respond: ").strip()
                # Wait for semantic completion
                ext.wait_for_npc_response(timeout=30)
                # check again
                agreed = requests.post(f"{SERVER}/player_agreed_check", json={
                    "idUser": idUser,
                    "idNPC": idNPC,
                    "playerText" : player_text,
                    "npcText" : ext.last_npc_response
                })  
                gameStarted = agreed
                ext.npc_response_ready.clear()
# --------------------------------------------------
# main loop
# --------------------------------------------------
game_start()

