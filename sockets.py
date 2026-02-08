from flask_socketio import SocketIO, join_room
from UnrealPhase1 import active_turns, start_game, advance_game, currentScene, idUser, voiceId

sio = SocketIO(cors_allowed_origins="*")

def init_socket_events(app):

    sio.init_app(app)
    #--------------------------------------------------------
    # testing 
    @sio.on("connect")
    def on_connect():
        print("player connected")
    
    @sio.on("ping")
    def ping(data=None):
        sio.emit("pong", "HELLO_FROM_FLASK")
    #--------------------------------------------------------
    # can update this in the future to get 
    # the player & scene data from unreal
    @sio.on("register_user")
    def register_user(data=None):
        join_room(f"user:{idUser}")   # ← THIS WAS MISSING
        start_game(sio=sio)
    #--------------------------------------------------------
    # from unreal socket emit event
    # get the player's input
    @sio.on("player_input")
    def on_player_input(data):
        turn = active_turns[idUser]
        advance_game(turn, data["player_text"], data["last_npc_text"], sio=sio)