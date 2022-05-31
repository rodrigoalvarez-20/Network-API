import json
from flask import Flask, request
from flask_cors import CORS

from api.utils.response import netapi_response
from api.utils.decorators import netapi_decorator
from api.utils.logger_socket import get_logger_output, get_logger_prefs, save_logger_prefs
from api.utils.configs import get_general_config
from api.utils.metrics  import get_monitor_configurations, get_monitored_interfaces, get_metrics_from_device
from api.routes.configurations import get_all_app_config, update_configs
from api.routes.routers import config_monitor, display_network, get_mib_info, get_monitor_config, modify_router_config, modify_users_in_router, update_mib_info, update_router_protocols
from api.routes.users import change_password, delete_user, get_users, login_user, register_user, send_reset_email, update_profile
from api.utils.common import auth
from api.utils.tokens_handler import search_used_token


from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)

ah, ap, ch, cp, _ = get_general_config()

socketio = SocketIO(app, cors_allowed_origins=[f"http://{ch}:{cp}", "http://192.168.100.141:3000"],
                    always_connect=True, async_mode="threading")


#Seccion de usuarios de aplicacion
app.add_url_rule("/api/app/users/register", "register_user", register_user, methods=["POST"])
app.add_url_rule("/api/app/users/login", "login_user", login_user, methods=["POST"])
app.add_url_rule("/api/app/users", "update_profile", update_profile, methods=["PATCH"])
app.add_url_rule("/api/app/users", "delete_user", delete_user, methods=["DELETE"])
app.add_url_rule("/api/app/users", "get_users", get_users, methods=["GET"])
app.add_url_rule("/api/app/users/request_reset", "send_reset_email", send_reset_email, methods=["POST"])
app.add_url_rule("/api/app/users/password", "change_password", change_password, methods=["POST"])

# Seccion de configuraciones de la aplicacion y monitores
app.add_url_rule("/api/app/configurations", "get_all_app_config", get_all_app_config, methods=["GET"])
app.add_url_rule("/api/app/configurations", "update_configs", update_configs, methods=["POST"])

# Seccion de routers
app.add_url_rule("/api/routers/graph", "display_network", display_network, methods=["GET"])
app.add_url_rule("/api/routers/config", "modify_router_config", modify_router_config, methods=["PATCH"])
app.add_url_rule("/api/routers/users", "modify_users_in_router", modify_users_in_router, methods=["POST"])
app.add_url_rule("/api/routers/protocol", "update_router_protocols", update_router_protocols, methods=["POST"])

app.add_url_rule("/api/routers/monitor", "config_monitor", config_monitor, methods=["POST"])
app.add_url_rule("/api/routers/monitor", "get_monitor_config", get_monitor_config, methods=["GET"])


app.add_url_rule("/api/routers/mib/<host>", "get_mib_info", get_mib_info, methods=["GET"])
app.add_url_rule("/api/routers/mib/<host>", "update_mib_info", update_mib_info, methods=["POST"])

#app.add_url_rule("/api/routers/protocol", "modify_router_protocol", modify_router_protocol, methods=["POST"])

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

    token_status = auth(token_data)

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
    save_logger_prefs(None, timer)

@socketio.on("get_log")
def send_logs_data():
    while(True):
        log_name, timer = get_logger_prefs()
        log_data = get_logger_output(log_name)
        emit("log_data", { "log": log_data, "name": log_name})
        socketio.sleep(timer)

@socketio.on("get_monitored_interfaces")
def get_monitored_data():
    while(True):
        monitored_interfaces = get_monitored_interfaces()
        emit("devices_monitoring",  monitored_interfaces )
        socketio.sleep(60)

@socketio.on("get_metrics")
def send_metrics_data(query: str):
    while(1):
        # Obtener el intervalo de actualizacion
        interval, _, _ = get_monitor_configurations()
        # Dada la query IP + Nombre dispositivo, buscar los datos
        if query is not None and query != "":
            filter = json.loads(query)
            metrics_raw = get_metrics_from_device(filter["ip"], filter["device"])
            # Parsear los datos, ya que solo quiero enviar los ultimos 20 elementos [::-1][:20]
            if metrics_raw is not None:
                data = {
                    "in_packets": metrics_raw["in_packets"][::-1][:20],
                    "in_disc": metrics_raw["in_discards"][::-1][:20],
                    "in_err": metrics_raw["in_errors"][::-1][:20],
                    "out_packets": metrics_raw["out_packets"][::-1][:20],
                    "out_disc" : metrics_raw["out_discards"][::-1][:20],
                    "out_err": metrics_raw["out_errors"][::-1][:20]
                }
                
                emit("metrics_data", data)

            else:
                emit("metrics_error", {"error": "Metricas de la interfaz inexistentes"})
        else:
            emit("metrics_error", { "error": "El valor del query es invalido" })

        socketio.sleep(interval)


@socketio.on('disconnect')
def test_disconnect():
    print('Cliente desconectado')


if __name__ == "__main__":
    socketio.run(app, ah, int(ap), debug=True)
    

