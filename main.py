from flask import Flask, request
from routes.routers import activate_ssh_in_router, add_user_to_router, delete_user_from_router, list_devices_in_db, modify_router_protocol, modify_router_settings, update_user_from_router, display_network
from routes.users import change_password, delete_user, get_users, login_user, register_user, send_reset_email, update_profile
from utils.common import auth
from utils.tokens_handler import search_used_token
from flask_cors import CORS, cross_origin
from utils.response import netapi_response
from utils.decorators import netapi_decorator
from utils.logger_socket import get_logger_output

from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

CORS(app)
#["http://localhost:3000"]
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"],
                    always_connect=True, async_mode="threading")


app.add_url_rule("/api/app/users/register", "register_user", register_user, methods=["POST"])
app.add_url_rule("/api/app/users/login", "login_user", login_user, methods=["POST"])
app.add_url_rule("/api/app/users", "update_profile", update_profile, methods=["PATCH"])
app.add_url_rule("/api/app/users", "delete_user", delete_user, methods=["DELETE"])
app.add_url_rule("/api/app/users", "get_users", get_users, methods=["GET"])
app.add_url_rule("/api/app/users/request_reset", "send_reset_email", send_reset_email, methods=["POST"])
app.add_url_rule("/api/app/users/password", "change_password", change_password, methods=["POST"])


app.add_url_rule("/api/routers/users/add", "add_user_to_router", add_user_to_router, methods=["POST"])
app.add_url_rule("/api/routers/users/modify", "update_user_from_router", update_user_from_router, methods=["POST"])
app.add_url_rule("/api/routers/users/delete", "delete_user_from_router", delete_user_from_router, methods=["DELETE"])
app.add_url_rule("/api/routers", "list_devices_in_db", list_devices_in_db, methods=["GET"])
app.add_url_rule("/api/routers/graph", "display_network", display_network, methods=["GET"])


app.add_url_rule("/api/routers/protocol", "modify_router_protocol", modify_router_protocol, methods=["POST"])
app.add_url_rule("/api/routers/config/modify", "modify_router_settings", modify_router_settings, methods=["POST"])
app.add_url_rule("/api/routers/config/ssh", "activate_ssh_in_router", activate_ssh_in_router, methods=["POST"])


@app.get("/api")
@netapi_decorator("general", None)
def test_api(log = None):
    log.info("Ruta principal")
    return netapi_response({"message": "Ok"}, 200)

@app.post("/api/auth/validate")
@netapi_decorator("users")
def validate_token_reset(log = None):
    req_body = request.get_json()
    token_data = req_body["token"]
    log.debug("Validando token de reestablecimiento de contraseña")
    
    used_token = search_used_token(token_data)
    if used_token is not None:
        return netapi_response({"message": "Este link ya se ha utilizado previamente"}, 400)

    token_status = auth(token_data);

    return netapi_response({"message": token_status["message"] if "message" in token_status else token_status["error"]}, token_status["status"])

@app.errorhandler(400)
def error_handler():
    return netapi_response({"error":"Recurso no encontrado"}, 400)

@socketio.on('connect')
def verify_socket_connection():
    emit('conn-resp', {'message': 'Ok'})

@socketio.on("get_log")
def test_socket(log_name):
    # Obtener el timeout de las configs en DB
    print("Solicitando: ", log_name)
    TIMEOUT = 10
    while(1):
        log_data = get_logger_output(log_name)
        emit("log_data", { "log": log_data, "name": log_name })
        socketio.sleep(TIMEOUT)

@socketio.on('disconnect')
def test_disconnect():
    print('Cliente desconectado')


if __name__ == "__main__":
    #app.run("127.0.0.1", 5000, True)
    socketio.run(app, "127.0.0.1", 5000, debug=True)

