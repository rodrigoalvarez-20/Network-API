
from flask import Response, request
from utils.decorators import netapi_decorator
from pymongo import ReturnDocument
from bson.objectid import ObjectId
from utils.session_auth import validate_session
from utils.response import netapi_response

@netapi_decorator("general", "configs")
def get_all_app_config(log = None, db = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

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

    req_body = request.get_json()
    actual_log = req_body["actual_log"]
    logs_timer = req_body["logs_timer"]
    map_interval = req_body["map_interval"]
    interface_interval = req_body["interface_interval"]
    lost_packets_percentage = req_body["lost_packets_percentage"]

    db.delete_many({})

    db.insert_one({ 
        "actual_log": actual_log,
        "logs_timer": int(logs_timer),
        "map_interval": int(map_interval),
        "interface_interval": int(interface_interval),
        "lost_packets_percentage": int(lost_packets_percentage)
    })

    return netapi_response({ "message": "Se han actualizado las configuraciones" }, 200)