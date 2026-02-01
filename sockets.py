from flask_socketio import SocketIO, join_room

socketio = SocketIO(cors_allowed_origins="*")

def init_socket_events(app):

    socketio.init_app(app)

    @socketio.on("connect")
    def on_connect():
        print("player connected")

    @socketio.on("register_user")
    def register_user(data):
        idUser = data["idUser"]
        join_room(f"user:{idUser}")
        print(f"registered user {idUser}")