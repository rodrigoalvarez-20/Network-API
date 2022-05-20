from crypt import methods
from flask import Flask, make_response, request
from routes.routers import activate_ssh_in_router, add_user_to_router, delete_user_from_router, list_devices_in_db, modify_router_protocol, modify_router_settings, update_user_from_router
from routes.users import change_password, delete_user, get_users, login_user, register_user, send_reset_email, update_profile
from utils.common import auth
from utils.tokens_handler import search_used_token

from utils.decorators import netapi_decorator

app = Flask(__name__)

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

app.add_url_rule("/api/routers/protocol", "modify_router_protocol", modify_router_protocol, methods=["POST"])
app.add_url_rule("/api/routers/config/modify", "modify_router_settings", modify_router_settings, methods=["POST"])
app.add_url_rule("/api/routers/config/ssh", "activate_ssh_in_router", activate_ssh_in_router, methods=["POST"])


@app.get("/api")
@netapi_decorator("general", None)
def test_api(log = None):
    log.info("Ruta principal")
    return make_response({"message": "Ok"}, 200)

@app.post("/api/auth/validate")
@netapi_decorator("users")
def validate_token_reset(log = None):
    req_body = request.get_json()
    token_data = req_body["token"]
    log.debug("Validando token de reestablecimiento de contraseña")
    
    used_token = search_used_token(token_data)
    if used_token is not None:
        return make_response({"message": "Este link ya se ha utilizado previamente"}, 400)

    token_status = auth(token_data);

    return make_response({"message": token_status["message"] if "message" in token_status else token_status["error"]}, token_status["status"])


@app.errorhandler(400)
def error_handler():
    return make_response({"error":"Recurso no encontrado"}, 400)

if __name__ == "__main__":
    app.run("0.0.0.0", 8000, True)

