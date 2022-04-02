from flask import Response, make_response, request
from utils.common import generate_login_token
from utils.decorators import netapi_decorator
import bcrypt

from utils.session_auth import validate_session

@netapi_decorator("users", "users")
def register_user(log = None, db = None):
    req_body = request.get_json()
    usr_data = {
        "name": req_body["name"],
        "last_name": req_body["last_name"],
        "email": req_body["email"],
        "password": bcrypt.hashpw(req_body["password"].encode(), bcrypt.gensalt(12)).decode(),
        "type": req_body["type"]
    }
    log.info(f"Tratando de registrar un usuario: {usr_data}")

    # Verificar que no exista en la base de datos
    usr_in_db = db.find_one({"email": usr_data["email"]})
    if usr_in_db is not None:
        log.info(f"Usuario ya existente {usr_data['email']}")
        return make_response({"error": "El usuario ya se ha registrado"}, 400)
    else:
        # Insertar usuario
        usr = db.insert_one(usr_data)
        log.info(f"Usuario registrado: {usr.inserted_id}")
        return make_response({ "message": "Se ha creado el usuario" }, 201)
    
@netapi_decorator("users", "users")
def login_user(log = None, db = None):
    req_body = request.get_json()
    email = req_body["email"]
    password = req_body["password"]
        
    log.info(f"Intento de inicio de sesion: {email}")

    # Verificar que no exista en la base de datos

    usr_in_db = db.find_one({"email": email})
    if usr_in_db is not None:
        log.debug(f"Verificando credenciales")
        if bcrypt.checkpw(password.encode(), usr_in_db["password"].encode()):
            # Generar token
            log.info(f"Inicio de sesion correcto: {email}")
            token = generate_login_token(str(usr_in_db["_id"]), email)
            return make_response({"message": "Inicio de sesion correcto", "token": token}, 200)
            
        else:
            log.info(f"Credenciales incorrectas: {email}")
            return make_response({"error": "Credenciales incorrectas"}, 400)
    else:
        log.info(f"Credenciales incorrectas: {email}")
        return make_response({ "error": "Credenciales incorrectas" }, 400)

@netapi_decorator("users", "users")
def update_profile(log = None, db = None):
    # Validar request
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    
    usr_id = session_data["id"]

    req_body = request.get_json()
    usr_data = {
        "name": req_body["name"],
        "last_name": req_body["last_name"],
        "type": req_body["type"]
    }

    db.find_one_and_update({"_id": usr_id}, {"$set": usr_data})
    log.info(f"Se ha actualizado la informacion del usuario: {usr_id}")
    return make_response({"message": "Se ha actualizado el perfil"}, 200)

@netapi_decorator("users", "users")
def delete_user(log = None, db = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    req_body = request.get_json()
    email = req_body["email"]
    usr_del = db.find_one_and_delete({"email": email})
    if not usr_del:
        return make_response({"error": "No se ha encontrado el usuario"}, 404)
    log.warning(f"Se ha eliminado el usuario: {email}")
    return make_response({"message": "Se ha eliminado el usuario"}, 200)