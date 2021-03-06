
from datetime import datetime
import os
from api.utils.configs import get_general_config
from flask import Response, request
from api.utils.common import  generate_login_token, generate_restore_pwd_token, send_email_message
from api.utils.tokens_handler import save_used_token
from api.utils.decorators import netapi_decorator
from pymongo import ReturnDocument
from bson.objectid import ObjectId

from api.utils.session_auth import validate_session
from api.utils.response import netapi_response
from utils.notify import save_notify

@netapi_decorator("users", "users")
def register_user(log=None, db=None):
    req_body = request.get_json()
    usr_data = {
        "name": req_body["name"],
        "last_name": req_body["last_name"],
        "email": req_body["email"],
        "password": req_body["password"],
        "type": req_body["type"]
    }
    log.info(f"Tratando de registrar un usuario: {usr_data}")

    # Verificar que no exista en la base de datos
    usr_in_db = db.find_one({"email": usr_data["email"]})
    if usr_in_db is not None:
        log.info(f"Usuario ya existente {usr_data['email']}")
        return netapi_response({"error": "El usuario ya se ha registrado"}, 400)
    else:
        # Insertar usuario
        usr = db.insert_one(usr_data)
        log.info(f"Usuario registrado: {usr.inserted_id}")
        return netapi_response({"message": "Se ha creado el usuario"}, 201)

@netapi_decorator("users", "users")
def login_user(log=None, db=None):
    req_body = request.get_json()
    email = req_body["email"]
    password = req_body["password"]

    log.info(f"Intento de inicio de sesion: {email}")

    # Verificar que no exista en la base de datos

    usr_in_db = db.find_one({"email": email})
    if usr_in_db is not None:
        log.debug(f"Verificando credenciales")
        if password == usr_in_db["password"]:
            # Generar token
            log.info(f"Inicio de sesion correcto: {email}")
            token = generate_login_token(str(usr_in_db["_id"]), email)
            return netapi_response({"message": "Inicio de sesion correcto", "token": token, "name": usr_in_db["name"], "last_name": usr_in_db["last_name"]}, 200)

        else:
            log.info(f"Credenciales incorrectas: {email}")
            return netapi_response({"error": "Credenciales incorrectas"}, 400)
    else:
        log.info(f"Credenciales incorrectas: {email}")
        return netapi_response({"error": "Credenciales incorrectas"}, 400)

@netapi_decorator("users", "users")
def get_users(email : str = None, log = None, db = None ):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    if email:
        users = list(db.find({"email": {"$regex": email}}, {"_id": 0}))
    else:
        users = list(db.find({}, {"_id": 0}))

    return netapi_response({"users": users}, 200)

@netapi_decorator("users", "users")
def send_reset_email(log=None, db=None):
    req_body = request.get_json()
    email = req_body["email"]

    log.info(
        f"Solicitando el reestablecimiento de contrase??a del usuario: {email}")

    usr_in_db = db.find_one({"email": email})
    _, _, ch, cp, _ = get_general_config()
    log.debug(f"Infomacion del usuario solicitando reestablecimiento de contrase??a: {usr_in_db}")
    if usr_in_db is not None:
        log.debug("Generando Token de restauraci??n")
        rest_tk = generate_restore_pwd_token(email)
        reset_link = f"http://{ch}:{cp}/services/restore?tk={rest_tk}"
        body_msg = ""
        log.debug("Abriendo template")
        with open(f"{os.getcwd()}/templates/reset_password.html", "r") as template:
            body_msg = template.read()
        
        body_msg = body_msg.replace("{email}", email)
        body_msg = body_msg.replace("{url}", reset_link)
        body_msg = body_msg.replace("{sentAt}", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
        logo_image = None
        with open(f"{os.getcwd()}/templates/logo.png", "rb") as logo:
            logo_image = logo.read()

        save_notify("servicio_network@noreply.ipn.mx", email, "Reestablecimiento de contrase??a", body_msg, logo_image)

        #send_email_message("servicio-network@noreply.mx", email, "Reestablecimiento de contrase??a", body_msg, logo_image)
        log.info("Se ha enviado correctamente el email")
        return netapi_response({"message":"Se ha enviado el correo de reestablecimiento"}, 200)
    else:
        log.info(f"Usuario {email} no encontrado")
        return netapi_response({"error": "No se ha encontrado un usuario con el correo especificado"}, 400)

@netapi_decorator("users", "users")
def update_profile(log=None, db=None):
    # Validar request
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    usr_id = ObjectId(session_data["id"])

    req_body = request.get_json()
    usr_data = {
        "name": req_body["name"],
        "last_name": req_body["last_name"],
        "type": req_body["type"]
    }


    updated = db.find_one_and_update({"_id": usr_id}, {"$set": usr_data}, return_document=ReturnDocument.AFTER)
    if updated is not None:
        log.info(f"Se ha actualizado la informacion del usuario: {usr_id}")
        return netapi_response({"message": "Se ha actualizado el perfil"}, 200)
    else:
        log.error(f"Ha ocurrido un error al actualizar la informaci??n del usuario: {usr_id}")
        return netapi_response({"error": "Ha ocurrido un error actualizado el perfil"}, 500)

@netapi_decorator("users", "users")
def change_password(log = None, db = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    email = session_data["email"]

    req_body = request.get_json()
    hsh_pwd = req_body["password"]
    usr_modify = db.find_one_and_update({"email": email}, {"$set": {"password": hsh_pwd} }, return_document=ReturnDocument.AFTER)
    save_used_token(request.headers["Authorization"])
    if not usr_modify:
        return netapi_response({"error": "El usuario no se ha encontrado en la base de datos"}, 400)

    log.info(f"Se ha actualizado el password del usuario: {email}")
    return netapi_response({"message": "Se ha actualizado la contrase??a"}, 200)

@netapi_decorator("users", "users")
def delete_user(log=None, db=None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    req_body = request.get_json()
    email = req_body["email"]
    usr_del = db.find_one_and_delete({"email": email})
    if not usr_del:
        return netapi_response({"error": "No se ha encontrado el usuario"}, 404)
    log.warning(f"Se ha eliminado el usuario: {email}")
    return netapi_response({"message": "Se ha eliminado el usuario"}, 200)
