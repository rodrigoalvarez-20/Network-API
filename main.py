from crypt import methods
from flask import Flask, make_response
from routes.routers import add_user_to_router, delete_user_from_router, list_devices_in_db, update_user_from_router
from routes.users import delete_user, login_user, register_user, update_profile

from utils.decorators import netapi_decorator

app = Flask(__name__)

app.add_url_rule("/app/users/register", "register_user", register_user, methods=["POST"])
app.add_url_rule("/app/users/login", "login_user", login_user, methods=["POST"])
app.add_url_rule("/app/users", "update_profile", update_profile, methods=["PATCH"])
app.add_url_rule("/app/users", "delete_user", delete_user, methods=["DELETE"])

app.add_url_rule("/routers/users/add", "add_user_to_router", add_user_to_router, methods=["POST"])
app.add_url_rule("/routers/users/modify", "update_user_from_router", update_user_from_router, methods=["POST"])
app.add_url_rule("/routers/users/delete", "delete_user_from_router", delete_user_from_router, methods=["DELETE"])
app.add_url_rule("/routers", "list_devices_in_db", list_devices_in_db, methods=["GET"])

@app.get("/")
@netapi_decorator("general", None)
def test_api(log = None):
    log.info("Ruta principal")
    return make_response({"message": "Ok"}, 200)


@app.errorhandler(400)
def error_handler():
    return make_response({"error":"Recurso no encontrado"}, 400)

if __name__ == "__main__":
    app.run("127.0.0.1", 8000, True)

