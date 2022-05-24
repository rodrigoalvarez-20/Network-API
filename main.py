from crypt import methods
from flask import Flask, request
from database.mongo import get_mongo_client
from routes.configurations import get_all_app_config, update_configs
from routes.routers import activate_ssh_in_router, add_user_to_router, delete_user_from_router, list_devices_in_db, modify_router_protocol, modify_router_settings, update_user_from_router, display_network
from routes.users import change_password, delete_user, get_users, login_user, register_user, send_reset_email, update_profile
from utils.common import auth
from utils.configs import get_mongo_config
from utils.tokens_handler import search_used_token
from flask_cors import CORS
from utils.response import netapi_response
from utils.decorators import netapi_decorator
from utils.logger_socket import get_logger_output, get_logger_prefs, save_logger_prefs

from flask_socketio import SocketIO, emit
import time

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

CORS(app)
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"],
                    always_connect=True, async_mode="threading")


app.add_url_rule("/api/app/users/register", "register_user", register_user, methods=["POST"])
app.add_url_rule("/api/app/users/login", "login_user", login_user, methods=["POST"])
app.add_url_rule("/api/app/users", "update_profile", update_profile, methods=["PATCH"])
app.add_url_rule("/api/app/users", "delete_user", delete_user, methods=["DELETE"])
app.add_url_rule("/api/app/users", "get_users", get_users, methods=["GET"])
app.add_url_rule("/api/app/users/request_reset", "send_reset_email", send_reset_email, methods=["POST"])
app.add_url_rule("/api/app/users/password", "change_password", change_password, methods=["POST"])

app.add_url_rule("/api/app/configurations", "get_all_app_config", get_all_app_config, methods=["GET"])
app.add_url_rule("/api/app/configurations", "update_configs", update_configs, methods=["POST"])


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
    log_name, timer = get_logger_prefs()
    emit('conn-resp', {'message': 'Ok', "log_name": log_name, "interval": timer})

@socketio.on("update_selected_log_prefs")
def update_selected_log(actual):
    save_logger_prefs(actual, None)

@socketio.on("update_timer_logs_prefs")
def update_timer_log(timer):
    print(timer)
    save_logger_prefs(None, timer)

@socketio.on("get_log")
def send_logs_data():
    while(1):
        log_name, timer = get_logger_prefs()
        log_data = get_logger_output(log_name)
        emit("log_data", { "log": log_data, "name": log_name})
        socketio.sleep(timer)

@socketio.on('disconnect')
def test_disconnect():
    print('Cliente desconectado')


if __name__ == "__main__":
    #app.run("127.0.0.1", 5000, True)
    socketio.run(app, "127.0.0.1", 5000, debug=True)

