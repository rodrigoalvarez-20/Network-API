from datetime import datetime
import json

from utils.configs import get_gns3_config, get_gns3_ssh_config
from utils.mapping import send_command
from utils.routing import connect_to_router
from utils.session_auth import validate_session
from utils.decorators import netapi_decorator
from utils.response import netapi_response
from flask import Response, request
import pexpect
from pexpect import pxssh

@netapi_decorator("network","network_map")
def display_network(log = None, db = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    log.info("Obteniendo topologia de red desde la DB")

    #network_schema = list(db.find({}, {"_id": 0}))[0]
    
    with open("topo_map.json", "r") as t:
        network_schema = json.loads(t.read())
    
    return netapi_response({"schema": network_schema}, 200)


# VERSION 2

@netapi_decorator("network", "network_map")
def modify_router_config(log = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    request_body = request.get_json()

    # El body contiene la version actualizada del router seleccionado
    # y las acciones a realizar en sus respectivos campos
    # hostname, interfaces, protocolos
    # La ruta viene en un arreglo de IP´s
    # conn_method puede ser SSH o telnet
    # La conexión se intentará hacer via SSH de manera automatica
    update_router = request_body["router"]

    ip_list = request_body["route"]
    method = request_body["method"]

    router_conn = connect_to_router(ip_list, method)

    if type(router_conn) == object:
        return netapi_response(router_conn, 500)
    send_command(router_conn, "config t")
    if "hostname" in request_body:
        # Actualizar el hostname del dispositivo
        log.info(f"Actualizado nombre del dispositivo: {update_router['name']}")
        new_name = request_body["hostname"]
        send_command(router_conn, f"hostname {new_name}")
    
    if "interfaces" in request_body:
        log.info(f"Cambiando interfaces del router {update_router['name']}")
        interfaces = request_body["interfaces"]
        for interface in interfaces:
            log.info(f"Configurando interfaz {interface['name']}")
            send_command(router_conn, f"int {interface['name']}")
            if "shutdown" in interface:
                log.debug(f"Se ha apagado la interfaz {interface['name']}")
                send_command(router_conn, "shut")
            elif "remove" in interface:
                log.debug(f"Se ha eliminado IP de la interfaz {interface['name']}")
                send_command(router_conn, "no ip add *")
            elif "power" in interface:
                log.debug(f"Se ha encendido la interfaz {interface['name']}")
                send_command(router_conn, "no shut")
            else:
                log.debug(f"Se ha configurado la IP: {interface['ip']} en la interfaz {interface['name']}")
                send_command(router_conn, f'ip add {interface["ip"]} {interface["mask"]}')
                send_command(router_conn, "no shut")

    # Actualizar el elemento

    



