from configparser import ConfigParser
import os
from utils.common import decrypt_data

parser = ConfigParser()

route = f"{os.getcwd()}/config.cfg"

#TODO Agregar un logger

def_msg_err = "Entradas incompletas del archivo de configuracion"

def get_mongo_config():
    if not parser.read(route):
        print(def_msg_err)
    if parser.has_option("MONGO", "host") and parser.has_option("MONGO", "user") and parser.has_option("MONGO", "pwd") and parser.has_option("MONGO", "db"):
        usr = decrypt_data(parser.get("MONGO", "user"))
        pwd = decrypt_data(parser.get("MONGO", "pwd"))
        host = parser.get("MONGO", "host")
        db = parser.get("MONGO", "db")
        return usr, pwd, host, db
    else:
        print(def_msg_err + " [MONGO]")


if __name__ == "__main__":
    # Reservado para pruebas
    pass
