from configparser import ConfigParser
import os
from api.utils.common import decrypt_data

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

def get_gns3_config():
    if not parser.read(route):
        print(def_msg_err)
    if parser.has_option("GNS3", "usr") and parser.has_option("GNS3", "pwd"):
        usr = decrypt_data(parser.get("GNS3", "usr"))
        pwd = decrypt_data(parser.get("GNS3", "pwd"))
        return usr, pwd
    else:
        print(def_msg_err + " [GNS3]")

def get_gns3_ssh_config():
    if not parser.read(route):
        print(def_msg_err)
    if parser.has_option("GNS3", "usr") and parser.has_option("GNS3", "pwd") and parser.has_option("GNS3", "secret") and parser.has_option("GNS3", "vty"):
        usr = decrypt_data(parser.get("GNS3", "usr"))
        pwd = decrypt_data(parser.get("GNS3", "pwd"))
        secret = decrypt_data(parser.get("GNS3", "secret"))
        vty = decrypt_data(parser.get("GNS3", "vty"))
        return usr, pwd, secret, vty
    else:
        print(def_msg_err + " [GNS3 SSH]")


def get_general_config():
    if not parser.read(route):
        print(def_msg_err)
    if parser.has_option("GENERAL", "api_host") and parser.has_option("GENERAL", "api_port") \
        and parser.has_option("GENERAL", "client_host") \
            and parser.has_option("GENERAL", "client_port") \
            and parser.has_option("GENERAL", "excluded_networks"):
        ah = parser.get("GENERAL", "api_host")
        ap = parser.get("GENERAL", "api_port")
        ch = parser.get("GENERAL", "client_host")
        cp = parser.get("GENERAL", "client_port")
        ex_nets = parser.get("GENERAL", "excluded_networks").split(";")
        return ah, ap, ch, cp, ex_nets
    else:
        print(def_msg_err + " [GENERAL]")

def get_snmp_config():
    if not parser.read(route):
        print(def_msg_err)
    if parser.has_option("SNMP", "group") and parser.has_option("SNMP", "notify_rcvs"):
        group = parser.get("SNMP", "group")
        rcvs = parser.get("SNMP", "notify_rcvs")
        return group, rcvs
    else:
        print(def_msg_err + " [SNMP]")


if __name__ == "__main__":
    # Reservado para pruebas
    pass
