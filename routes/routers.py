from copyreg import constructor
from datetime import datetime
import json
from pprint import pprint

from api.utils.configs import get_gns3_config, get_gns3_ssh_config, get_snmp_config
from api.utils.mapping import get_ip_from_local_address, send_command
from api.utils.routing import connect_to_router, execute_commands
from api.utils.session_auth import validate_session
from api.utils.decorators import netapi_decorator
from api.utils.response import netapi_response
from api.monitor import start_mapping
from flask import Response, request


@netapi_decorator("network", "network_map")
def display_network(log=None, db=None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    log.info("Obteniendo topologia de red desde la DB")

    network_schema = list(db.find({}, {"_id": 0}))[0]

    monitor_data = json.loads(get_monitor_config().data)["configs"]

    if len(monitor_data) > 0:
        for r in monitor_data:
            act_dev = r["device"]
            act_ints: list = r["interfaces"] if "interfaces" in r else []
            act_status = r["status"]
            if act_dev in network_schema:
                network_schema[act_dev]["monitor_status"] = act_status

                if len(act_ints) > 0:
                    for i, dev in enumerate(network_schema[act_dev]["interfaces"]):
                        matchs = [x for x in act_ints if x["name"] == dev["interface"]]
                        if len(matchs) > 0:
                            network_schema[act_dev]["interfaces"][i]["monitor_status"] = matchs[0]["status"]

    # with open("topo_map.json", "r") as t:
    #    network_schema = json.loads(t.read())

    return netapi_response({"schema": network_schema}, 200)

# VERSION 2

#@netapi_decorator("network")


@netapi_decorator("network", "monitor")
def modify_router_config(log=None, db=None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    request_body = request.get_json()

    usr, pwd, secret, vty = get_gns3_ssh_config()

    original_name = request_body["original_name"]

    ip_list = request_body["route"]
    method = request_body["method"]

    access_ip = ip_list[len(ip_list)-1]

    router_conn = connect_to_router(ip_list, method)

    if type(router_conn) == dict:
        return netapi_response(router_conn, 500)

    send_command(router_conn, "config t")

    if "hostname" in request_body:
        # Actualizar el hostname del dispositivo
        log.info(f"Actualizado nombre del dispositivo: {original_name}")
        new_name = request_body["hostname"]
        send_command(router_conn, f"hostname {new_name}")
        # Actualizar el documento de monitor, ya que puede haber una coincidencia
        db.update_one({"device": original_name}, {"$set": { "device": new_name }})

    if "interfaces" in request_body:
        log.info(f"Cambiando interfaces del router {original_name}")
        interfaces = request_body["interfaces"]
        for interface in interfaces:
            log.info(f"Configurando interfaz {interface['interface']}")
            send_command(router_conn, f"int {interface['interface']}")
            if "shutdown" in interface and interface["shutdown"] == True:
                log.debug(f"Se ha apagado la interfaz {interface['interface']}")
                send_command(router_conn, "shut")
            elif "remove" in interface and interface["remove"] == True:
                log.debug(
                    f"Se ha eliminado IP de la interfaz {interface['interface']}")
                send_command(router_conn, "no ip add *")
            elif "power" in interface and interface["power"] == True:
                log.debug(f"Se ha encendido la interfaz {interface['interface']}")
                send_command(router_conn, "no shut")
            else:
                log.debug(
                    f"Se ha configurado la IP: {interface['ip']} en la interfaz {interface['interface']}")
                send_command(
                    router_conn, f'ip add {interface["ip"]} {interface["mask"]}')
                send_command(router_conn, "no shut")

        send_command(router_conn, "exit")

    if "ssh_v2" in request_body:
        activate = bool(request_body["ssh_v2"])
        if activate == True:
            commands = [f"enable secret {secret}", "service password encryption",
                        "int lo0", "ip add 1.0.0.1 255.255.255.0", "no shut",
                        "crypto key generate rsa usage-keys label sshkey modulus 1024", "ip ssh rsa keypair-name sshkey",
                        "ip ssh v 2", "ip ssh time-out 30", "ip ssh authentication-retries 3", "line vty 0 15", f"password {vty}",
                        "login local", "transport input ssh telnet", "exit", f"username {usr} privilege 15 {pwd}"]

            log.info(
                f"Configurando SSH en el router {original_name} - {access_ip}")
        else:
            commands = ["line vty 0 15", "transport input telnet", "exit"]
            log.warning(
                f"Eliminando el protocolo SSH-v2 en el router {original_name}")

        execute_commands(router_conn, commands, original_name)

    log.info(
        f"Se ha terminado de configurar los cambios al SSH en el router {original_name}")

    if "snmp-v3" in request_body:
        group = get_snmp_config()
        activate = bool(request_body["snmp-v3"])
        if activate == True:
            usr, pwd, secret, vty = get_gns3_ssh_config()
            inets = get_ip_from_local_address(["192.168.100.0"])
            ips = ["2".join(x.rsplit("0", 1)) for x in inets]
            commands = [f"snmp-server group {group} v3 auth", f"snmp-server user {usr} {group} v3 auth md5 {pwd} priv des56 {pwd}",
                        "snmp-server enable traps"]
            for ip in ips:
                commands.append(
                    f"snmp-server host {ip} {usr} alarms config cpu eigrp ospf snmp")
                commands.append(
                    f"snmp-server host {ip} informs version 2c {usr} alarms config cpu eigrp ospf snmp")

            log.info(
                f"Configurando SNMP-V3 en el router {original_name} - {access_ip}")
        else:
            commands = ["no snmp-server"]
            log.warning(f"Eliminando el SNMP-V3 en el router {original_name}")

        execute_commands(router_conn, commands, original_name)

        log.info(
            f"Se ha terminado de configurar los cambios en el SNMP del router {original_name}")

    send_command(router_conn, "exit")
    send_command(router_conn, "wr mem")

    start_mapping()

    return netapi_response({"message": "Se ha actualizado la configuracion del router"}, 200)


@netapi_decorator("network", "monitor")
def config_monitor(log=None, db=None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    request_body = request.get_json()

    if "device" in request_body:
        device = request_body["device"]
        status = bool(request_body["monitor"])
        params = {
            "device": device,
            "status": status
        }

        if "interfaces" in request_body:
            params["interfaces"] = request_body["interfaces"]

        db.update_one({"device": device}, {"$set": params}, upsert=True)

        return netapi_response({"message": "Se ha actualizado la configuración de monitoreo"}, 200)
    else:
        return netapi_response({"message": "No se han realizado cambios en la configuración de monitoreo"}, 200)


@netapi_decorator("network", "monitor")
def get_monitor_config(log=None, db=None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    configs = list(db.find({}, {"_id": 0}))

    return netapi_response({"configs": configs}, 200)
