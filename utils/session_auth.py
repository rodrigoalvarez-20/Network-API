from flask import request
from api.utils.common import auth
from api.utils.response import netapi_response
from api.utils.decorators import netapi_decorator


@netapi_decorator("users")
def validate_session(log=None):
    log.info("Validando sesion de usuario")
    if "Authorization" not in request.headers:
        return netapi_response({"error": "Encabezado no encontrado"}, 400)

    auth_stat = auth(request.headers["Authorization"])
    if auth_stat["status"] != 200:
        return netapi_response({"error": auth_stat["error"]}, 401)

    return auth_stat
