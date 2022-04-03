from datetime import datetime
from utils.configs import get_gns3_config
from utils.session_auth import validate_session
from utils.decorators import netapi_decorator
from flask import Response, make_response, request
import pexpect
from pexpect import pxssh

@netapi_decorator("routers")
def move_into_routers(child, routers_list, usr, pwd, method, log = None):
    """
    Funcion que permite moverse entre routers, utilizando el protocolo especificado
    @param child: Instancia de spawn o pxssh
    @param routers_list: Lista de routers que se tiene que iterar
    @param usr: Usuario por defecto de telnet y ssh
    @param pwd: Pwd por defecto de telnet y ssh
    @param method: Metodo a utilizar para la conexion (ssh o telnet)
    """
    for i in range(1,len(routers_list)): # Itera cada uno de los elementos (routers) desde 1 hasta el final
        log.info(f"Moving to {routers_list[i]['ip']}")
        if method == "ssh":
            child.sendline(f"ssh -l {usr} {routers_list[i]['ip']}") #Enviamos el comando ssh por la terminal del router
            child.expect("Password:")
            child.sendline(pwd)
        elif method == "telnet":
            child.sendline(f"telnet {routers_list[i]['ip']}") #Hacemos la conexion telnet directa
            child.expect("Username:")
            child.sendline(usr)
            child.expect("Password:")
            child.sendline(pwd)


@netapi_decorator("network", "devices")
def list_devices_in_db(log = None, db = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    log.info("Obteniendo todos los dispositivos en la DB")
    devices_in_db = list(db.find({}, {"_id": 0}))
    return make_response({"devices": devices_in_db}, 200)

@netapi_decorator("network")
def add_user_to_router(log = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    request_body = request.get_json()
    hosts = request_body["hosts"]
    usr_to_add = request_body["username"]
    usr_pwd_to_add = request_body["pwd"]
    privilege = request_body["privilege"]
    con_method = request_body["method"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Añadiendo usuario {usr_to_add} al router con IP: {last_host['ip']}")
    gns3_usr, gns3_pwd = get_gns3_config()
    try:
        log.info(f"Enviando comandos al router: {hosts[0]['ip']}")
        if con_method == "ssh":
            # Primer inicio de sesion via ssh al primer router
            child = pxssh.pxssh()
            child.login(hosts[0]["ip"], gns3_usr, gns3_pwd, auto_prompt_reset=False)
        else:
            # Inicio de sesion via telnet al primer router
            child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
            child.expect("Username:")
            child.sendline(gns3_usr)
            child.expect("Password:")
            child.sendline(gns3_pwd)
            child.expect(hosts[0]['host'])

        move_into_routers(child, hosts, gns3_usr, gns3_pwd, con_method)

        # Empezamos a ejecutar los comandos necesarios
        child.sendline("config t")
        child.sendline(f"username {usr_to_add} privilege {privilege} password {usr_pwd_to_add}")
        child.expect(last_host['host'])
        child.sendline("end")
        child.sendline("wr mem") # Algo mejor que copy run start
        child.expect(last_host['host'])
        log.debug("Closing session")
        child.close(force=True) # Mandamos un close con force para que cierre el proceso padre, por ende tambien los hijos
        
        log.info(f"Se ha terminado de añadir el usuario via {con_method}")
        return make_response({"message": "Se ha agregado el usuario al router"}, 200)

    except pexpect.TIMEOUT:
        log.warning(f"Tiempo de espera excedido")
        return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
    except Exception as ex:
        log.error(str(ex))
        return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)

@netapi_decorator("network")
def update_user_from_router(log=None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    request_body = request.get_json()
    hosts = request_body["hosts"]
    usr_to_update = request_body["username"]
    new_pwd = request_body["pwd"]
    privilege = request_body["privilege"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Modificando usuario {usr_to_update} en el router con IP: {last_host['ip']}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    if ("ssh_usr", "ssh_pwd") in request_body:
        #Hacerlo por SSH
        pass
    else:
        #Hacerlo via telnet con la cuenta por defecto de todos los routers 
        telnet_usr, telnet_pwd = get_telnet_config()
        try:
            log.info(f"Enviando comandos al router: {hosts[0]['ip']}")
            child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
            child.expect("Username:")
            child.sendline(telnet_usr)
            child.expect("Password:")
            child.sendline(telnet_pwd)
            child.expect(hosts[0]['host'])
            # Siguientes hosts
            for i in range(1,len(hosts)):
                log.info(f"Moving to {hosts[i]['ip']}")
                child.sendline(f"telnet {hosts[i]['ip']}")
                child.expect("Username:")
                child.sendline(telnet_usr)
                child.expect("Password:")
                child.sendline(telnet_pwd)
            child.sendline("config t")
            child.expect(last_host["host"])
            child.sendline(f"username {usr_to_update} privilege {privilege} password {new_pwd}")
            child.expect(last_host["host"])
            child.sendline("end")
            child.sendline("wr mem")
            child.expect(last_host['host'])
            child.close()
            log.info(f"Se ha terminado de modificar el usuario")
            return make_response({"message": "Se ha modificado el usuario del router"}, 200)
        except pexpect.TIMEOUT:
            log.warning(f"Tiempo de espera excedido")
            return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
        except Exception as ex:
            log.error(str(ex))
            return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)

@netapi_decorator("network")
def delete_user_from_router(log=None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    request_body = request.get_json()
    hosts = request_body["hosts"]
    usr_to_delete = request_body["username"]
    usr_pwd_to_delete = request_body["pwd"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Eliminando usuario {usr_to_delete} del router con IP: {last_host['ip']}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    if ("ssh_usr", "ssh_pwd") in request_body:
        #Hacerlo por SSH
        pass
    else:
        #Hacerlo via telnet con la cuenta por defecto de todos los routers
        telnet_usr, telnet_pwd = get_telnet_config()
        try:
            log.info(f"Enviando comandos al router: {hosts[0]['ip']}")
            child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
            child.expect("Username:")
            child.sendline(telnet_usr)
            child.expect("Password:")
            child.sendline(telnet_pwd)
            child.expect(hosts[0]['host'])
            # Siguientes hosts
            for i in range(1,len(hosts)):
                log.info(f"Moving to {hosts[i]['ip']}")
                child.sendline(f"telnet {hosts[i]['ip']}")
                child.expect("Username:")
                child.sendline(telnet_usr)
                child.expect("Password:")
                child.sendline(telnet_pwd)
            child.sendline("config t")
            child.expect(last_host["host"])
            child.sendline(f"no username {usr_to_delete} password {usr_pwd_to_delete}")
            child.expect(last_host["host"])
            child.sendline("end")
            child.sendline("wr mem")
            child.expect(last_host['host'])
            child.close()
            log.info(f"Se ha terminado de eliminar el usuario")
            return make_response({"message": "Se ha eliminado el usuario del router"}, 200)
        except pexpect.TIMEOUT:
            log.warning(f"Tiempo de espera excedido")
            return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
        except Exception as ex:
            log.error(str(ex))
            return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)


@netapi_decorator("network")
def modify_router_protocol(log = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data

    request_body = request.get_json()
    hosts = request_body["hosts"]
    protocol = request_body["protocol"]
    networks = request_body["networks"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Modificando protocolo en el router con IP: {last_host['ip']}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    if ("ssh_usr", "ssh_pwd") in request_body:
        #Hacerlo por SSH
        pass
    else:
        #Hacerlo via telnet con la cuenta por defecto de todos los routers
        telnet_usr, telnet_pwd = get_telnet_config()
        try:
            log.info(f"Enviando comandos al router: {hosts[0]['ip']}")
            child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
            child.expect("Username:")
            child.sendline(telnet_usr)
            child.expect("Password:")
            child.sendline(telnet_pwd)
            child.expect(hosts[0]['host'])
            # Siguientes hosts
            for i in range(1,len(hosts)):
                log.info(f"Moving to {hosts[i]['ip']}")
                child.sendline(f"telnet {hosts[i]['ip']}")
                child.expect("Username:")
                child.sendline(telnet_usr)
                child.expect("Password:")
                child.sendline(telnet_pwd)
            
            # Router de destino
            child.sendline("terminal length 0")
            child.expect(last_host["host"])
            log.info("Obteniendo protocolos del router")
            child.sendline("show ip protocol")
            child.expect(last_host["host"])
            modified = False
            protocol_info = child.before.decode()
            child.sendline("conf t")
            child.expect(last_host["host"])
            if protocol_info != "":
                log.info("Se ha encontrado valores de protocolos")
                protocol_info = protocol_info.split("\n")
                routing_protocols_data = [x for x in protocol_info if x.startswith("Routing Protocol")]
                protocols_in_router = []
                for prot in routing_protocols_data:
                    temp_p = prot.split(" ")[3]
                    temp_p = temp_p.replace("\r", "")
                    temp_p = temp_p.replace("\"", "")
                    protocols_in_router.append(temp_p)
                
                modified = len(protocols_in_router) > 0
                log.info(f"Protocolos encontrado: {', '.join(protocols_in_router)}")
                for pt_rt in protocols_in_router:
                    log.info(f"Eliminando protocolo: {pt_rt}")
                    child.sendline(f"no router {pt_rt}")
                    child.expect(last_host["host"])

            if protocol == "rip":
                log.info("Anadiendo protocolo rip")
                child.sendline("router rip")
                child.sendline("ver 2")
            if protocol.startswith("ospf") or protocol.startswith("eigrp"):
                log.info(f"Anadiendo protocolo {protocol}")
                child.sendline(f"router {protocol}")
                child.expect(last_host["host"])

            for net in networks:
                child.sendline(f"net {net}")
                child.expect(last_host["host"])

            child.sendline("end")
            child.expect(last_host["host"])
            child.sendline("wr mem")
            child.close()
           
            return make_response({"message": "Se ha modificado el protocolo existente" if modified else "Se ha anadido el protocolo"}, 200)
        except pexpect.TIMEOUT:
            log.warning(f"Tiempo de espera excedido")
            return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
        except Exception as ex:
            log.error(str(ex))
            return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)
