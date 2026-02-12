from flask_socketio import SocketIO, join_room
from UnrealPhase1 import active_turns, start_game, advance_game, currentScene, idUser, voiceId
from emotionGameQueries import get_active_emotion
#------------------------------------------------------------------
import os
import mysql.connector
#------------------------------------------------------------------
def connect()->object:
    return mysql.connector.connect(
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PASSWORD'), 
        database=os.getenv('DB_NAME'),
        host=os.getenv('DB_HOST', 'localhost') )
#------------------------------------------------------------------
sio = SocketIO(cors_allowed_origins="*")
#------------------------------------------------------------------
def init_socket_events(app):

    sio.init_app(app)
    #--------------------------------------------------------------
    # testing 
    @sio.on("connect")
    def on_connect():
        print("player connected")

    @sio.on("ping")
    def ping(data=None):
        sio.emit("pong", "HELLO_FROM_FLASK")

    @sio.on("get_cur_emotion")
    def getCurEmotion(data=None):
        db = connect()
        cursor = db.cursor()
        cursor.execute("""
            SELECT e.emotion
            FROM emotion_guess_game g
            JOIN emotion e ON e.idEmotion = g.idEmotion
            WHERE g.idUser = 1
                AND g.idNPC = 1
                AND g.active = 1
            LIMIT 1;
        """)
        emotion = cursor.fetchone()
        print('current emotion from backend', emotion)
        sio.emit("send_cur_emotion", emotion)

    
    #--------------------------------------------------------------
    # can update this in the future to get 
    # the player & scene data from unreal
    @sio.on("register_user")
    def register_user(data=None):
        join_room(f"user:{idUser}")   # ← THIS WAS MISSING
        start_game(sio=sio)
    #--------------------------------------------------------------
    # from unreal socket emit event
    # get the player's input
    @sio.on("player_input")
    def on_player_input(data):
        turn = active_turns[idUser]
        advance_game(turn, data["player_text"], data["last_npc_text"], sio=sio)
        #--------------------------------------------------------------
    # from unreal socket emit event
    # get the player's input
    @sio.on("player_stepped_away")
    def on_player_input(data):
        turn = active_turns[idUser]
        advance_game(turn, data["player_text"], data["last_npc_text"], sio=sio)