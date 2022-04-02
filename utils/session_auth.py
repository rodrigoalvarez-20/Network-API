from flask import make_response, request
from utils.common import auth
from utils.decorators import netapi_decorator


@netapi_decorator("users")
def validate_session(log=None):
    log.info("Validando sesion de usuario")
    if "Authorization" not in request.headers:
        return make_response({"error": "Encabezado no encontrado"}, 400)

    auth_stat = auth(request.headers["Authorization"])
    if auth_stat["status"] != 200:
        return make_response({"error": auth_stat["error"]}, 401)

    return auth_stat
