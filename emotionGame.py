import requests
from extensions import CamoClientExtension
from streamingMP3Player import StreamingMP3Player
import requests

# -----------------------------------------------------------------------------------
# config
# -----------------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------------
# socket extension
# -----------------------------------------------------------------------------------
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
        # ---------------------------------------------------------------------------
        #   introduction branch
        # ---------------------------------------------------------------------------
        if not gameStarted:
            playerName = input("\n Enter your name: ").strip()

            requests.post(f"{SERVER}/npc_introduce", json={
                "idUser"        : idUser,
                "idNPC"         : idNPC,
                "currentScene"  : currentScene,
                "playerName"    : playerName,
                "idVoice"       : voiceId,
            })

            # Wait until NPC finishes talking before allowing input
            ext.wait_for_npc_response(timeout=30)

            player_text = input("\n Respond: ").strip()

            agreed = requests.post(f"{SERVER}/player_agreed_check", json={
                "idUser"        : idUser,
                "idNPC"         : idNPC,
                "playerText"    : player_text,
                "npcText"       : ext.last_npc_response
            })
        # ---------------------------------------------------------------------------
        # agreed to play branch
        # ---------------------------------------------------------------------------
        if (agreed): 

            while True:
                # start guessing game 
                requests.post(f"{SERVER}/assign_next_emotion", json={
                        "idUser"        : idUser,
                        "idNPC"         : idNPC,
                        "pName"         : playerName,
                        "curScene"      : currentScene,
                        "game_started"  : gameStarted
                    })
                # Wait until NPC finishes talking before allowing input
                ext.wait_for_npc_response(timeout=30)
                # get player's guess for NPC's current emotion
                player_text = input("\n\n Respond: ").strip()
                gameStarted = True
                ext.npc_response_ready.clear()
                # check the guess
                isGuessCorrect = requests.post(f"{SERVER}/player_guess", json={
                        "idUser"        : idUser,
                        "idNPC"         : idNPC,
                        "playerName"    : playerName,
                        "currentScene"  : currentScene,
                        "player_text"   : player_text,
                        "npcText"       : ext.last_npc_response,
                        "game_started"  : gameStarted
                    })
                # -------------------------------------------------------------------
                # correct guess branch
                # -------------------------------------------------------------------
                while isGuessCorrect:
                    print("\n\nCORCORRECT GUESS!\n\n")

                    # updated the npc_describe_emotion prompt to be more descriptive 
                    # about why an answer was correct and how now the npc feels better
                    # that they can put a name to this emotion

                    # then updated backend score counting
                    # track score in turnContext too ?
                # -------------------------------------------------------------------
                # incorrect guess branch
                # -------------------------------------------------------------------
                while not isGuessCorrect:
                    print("\n\nINCORRECT GUESS!\n\n")
                    # get player's guess for NPC's current emotion
                    player_text = input("\n Respond: ").strip()
                    isGuessCorrect = requests.post(f"{SERVER}/player_guess", json={
                        "idUser"        : idUser,
                        "idNPC"         : idNPC,
                        "playerName"    : playerName,
                        "currentScene"  : currentScene,
                        "player_text"   : player_text,
                        "npcText"       : ext.last_npc_response
                    })
        # ---------------------------------------------------------------------------
        # refused to play branch
        # ---------------------------------------------------------------------------          
        else: 
            while not agreed:
                
                print('\nDENIED!\n')
                # create prompt for when player denies NPC's game
                # returns npcs output in n
               
                requests.post(f"{SERVER}/player_not_agreed", json={
                    "idUser"        : idUser,
                    "idNPC"         : idNPC,
                    "playerName"    : playerName,
                    "currentScene"  : currentScene,
                    "playerText"    : player_text
                })  
                
                # get player's response to this NPC output
                player_text = input("\n Respond: ").strip()
                # Wait for semantic completion
                ext.wait_for_npc_response(timeout=30)
                
                # check again
                agreed = requests.post(f"{SERVER}/player_agreed_check", json={
                    "idUser"        : idUser,
                    "idNPC"         : idNPC,
                    "playerText"    : player_text,
                    "npcText"       : ext.last_npc_response
                })  
                gameStarted = agreed
                ext.npc_response_ready.clear()
# -----------------------------------------------------------------------------------
# main loop
# -----------------------------------------------------------------------------------
game_start()

