import logging
import os
from functools import wraps
from api.database.mongo import get_mongo_client
from datetime import datetime
from pathlib import Path

from api.utils.configs import get_mongo_config

LOGS_PATH = f"{Path.home()}/logs"

if not os.path.isdir(LOGS_PATH):
    os.makedirs(LOGS_PATH)

routes = {
    "network": f"{LOGS_PATH}/network/netapi_network",
    "users": f"{LOGS_PATH}/users/netapi_users",
    "general": f"{LOGS_PATH}/general/netapi_general",
    "mapping": f"{LOGS_PATH}/mapping/netapi_mapper_service",
    "monitor": f"{LOGS_PATH}/mapping/netapi_monitor_service",
}


def netapi_decorator(log_alias = "general", tb_alias = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if log_alias is not None:
                    path_to_log = routes[log_alias] if log_alias in routes else routes["general"]
                    if not os.path.isdir(f"{LOGS_PATH}/{log_alias}"):
                        os.makedirs(f"{LOGS_PATH}/{log_alias}")
                    path_to_log += f"_{datetime.now().strftime('%Y_%m_%d')}.log"
                    logging.basicConfig(
                    format="=== %(asctime)s::%(levelname)s::%(funcName)s === %(message)s", filename=path_to_log, level=logging.DEBUG)
                    log = logging.getLogger("network_api")
                    kwargs["log"] = log

                if tb_alias is not None:
                    mongo_con = get_mongo_client()
                    _,_,_, db = get_mongo_config()
                    kwargs["db"] = mongo_con[db][tb_alias]

            except Exception as ex:
                print(f"Ha ocurrido un error en el decorador: {ex}")
                exit(1)
            return func(*args, **kwargs)
        return wrapper
    return decorator
