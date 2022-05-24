from datetime import datetime
import json
import time, subprocess
from utils.decorators import routes, LOGS_PATH, netapi_decorator
from pprint import pprint

@netapi_decorator("general", None)
def get_logger_output(logname = None, log = None):
    today = datetime.now().day
    file_name = f"{routes[logname]}*{today}.log" if logname else f"{LOGS_PATH}/*/*{today}.log"
    log.info(f"Obteniendo logs: {file_name}")
    f = subprocess.getoutput(f"cat {file_name}").splitlines()

    if f[0].find("No such file or directory") != -1:
        log.warning("Archivo de logs no encontrado")
        return None

    f_fmt = list(filter(lambda x: \
        x.find("* Detected change") == -1 and \
        x.find("/socket.io/") == -1 and \
        x.find("_log_error_once") == -1, f))
    return f_fmt

@netapi_decorator("general", "configs")
def save_logger_prefs(actual_log = None, interval = None, log = None, db = None):
    prefs = {}
    if actual_log:
        prefs["actual_log"] = actual_log
    if interval:
        prefs["logs_timer"] = interval

    if db.count_documents({}) == 0:
        log.info(f"Guardando configuraciones del log: {json.dumps(prefs)}")
        db.insert_one(prefs)
    else:
        log.info(f"Actualizando configuraciones del log: {json.dumps(prefs)}")
        db.update_many({}, {"$set": prefs})


@netapi_decorator("general", "configs")
def get_logger_prefs(log = None, db = None):
    log.info("Obteniendo configuraciones de logs")
    if db.count_documents({}) == 0:
        return "general", 10
    else:
        configs = db.find({})[0]
        LOG_NAME = configs["actual_log"] if "actual_log" in configs else "general"
        TIMER = configs["logs_timer"] if "logs_timer" in configs else 5
        return LOG_NAME, TIMER
