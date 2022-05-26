
import json
from flask import Response, request
from api.utils.decorators import netapi_decorator
from pymongo import ReturnDocument
from bson.objectid import ObjectId
from api.utils.session_auth import validate_session
from api.utils.response import netapi_response

config_params = ["actual_log", "logs_timer", "map_interval", \
    "interface_interval", "device_interval", \
    "received_packets_percentage", "lost_packets_percentage", \
    "damaged_packets_percentage", "device_mon", "int_mon" ]

@netapi_decorator("general", "configs")
def get_all_app_config(log = None, db = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    log.info("Obteniendo las configuraciones guardads")
    configs = list(db.find({}, {"_id": 0}))

    if len(configs) > 0:
        return netapi_response({ "configs": configs[0] }, 200)
    else:
        return netapi_response({ "error": "No se ha encontrado datos de configuración" }, 404)

@netapi_decorator("general", "configs")
def update_configs(log = None, db = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    log.info("Agregando/Actualizando configuraciones de la aplicacion")
    req_body = request.get_json()
    params = {}
    
    for p in config_params:
        if p in req_body:
            params[p] = req_body[p] if p in ["actual_log", "device_mon", "int_mon"] else int(req_body[p])
    
    
    configs_in_db = list(db.find())
    log.info(f"Valores a actualizar: {json.dumps(params)}")
    if len(configs_in_db) == 0:
        db.insert_one(params)
        return netapi_response({"message": "Se ha creado la entrada de configuraciones"}, 200)
    else:
        db.update_one({ "_id": configs_in_db[0]["_id"] }, { "$set": params })
        return netapi_response({ "message": "Se han actualizado las configuraciones" }, 200)