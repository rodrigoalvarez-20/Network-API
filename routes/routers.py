from datetime import datetime
from utils.configs import get_gns3_config, get_gns3_ssh_config
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
            #child.expect("Password:")
            child.sendline(pwd)
        elif method == "telnet":
            child.sendline(f"telnet {routers_list[i]['ip']}") #Hacemos la conexion telnet directa
            child.expect("Username:")
            child.sendline(usr)
            child.expect("Password:")
            child.sendline(pwd)

@netapi_decorator("routers")
def get_router_protocols(child, host, log = None):
    child.sendline("terminal length 0")
    child.expect(host)
    log.info("Obteniendo protocolos del router")
    child.sendline("show ip protocol")
    child.expect(host)
    protocol_info = child.before.decode()
    #log.debug(protocol_info)
    # Regresar la lista de los protocolos validos
    if protocol_info != "":
        log.info("Se ha encontrado valores de protocolos")
        protocol_info = protocol_info.split("\n")
        routing_protocols_data = [x for x in protocol_info if x.startswith("Routing Protocol")]
        protocols_in_router = []
        for prot in routing_protocols_data:
            temp_p = prot.split("\"")
            protocols_in_router.append(temp_p[1])
        log.info(f"Protocolos encontrados: {', '.join(protocols_in_router)}")
        return protocols_in_router
    else:
        return []

@netapi_decorator("routers")
def delete_protocols_from_router(child, host, protocols_list, log = None):
    for pt_rt in protocols_list:
        log.info(f"Eliminando protocolo: {pt_rt}")
        child.sendline(f"no router {pt_rt}")
        child.expect(host)

# Esta probablemente la tenga que borrar
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
            child = pxssh.pxssh(timeout=20)
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
        child.expect(last_host['host'])
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
    con_method = request_body["method"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Modificando usuario {usr_to_update} en el router con IP: {last_host['ip']}")
    gns3_usr, gns3_pwd = get_gns3_config()
    try:
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

        child.sendline("config t")
        child.expect(last_host["host"])
        child.sendline(
            f"username {usr_to_update} privilege {privilege} password {new_pwd}")
        child.expect(last_host["host"])
        child.sendline("end")
        child.expect(last_host["host"])
        child.sendline("wr mem")
        child.expect(last_host['host'])
        child.close(force=True)
        log.info(f"Se ha terminado de modificar el usuario via {con_method}")
        return make_response({"message": "Se ha modificado el usuario en el router"}, 200)
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
    con_method = request_body["method"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Eliminando usuario {usr_to_delete} del router con IP: {last_host['ip']}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    gns3_usr, gns3_pwd = get_gns3_config()
    try:
        if con_method == "ssh":
            # Primer inicio de sesion via ssh al primer router
            child = pxssh.pxssh()
            child.login(hosts[0]["ip"], gns3_usr,
                        gns3_pwd, auto_prompt_reset=False)
        else:
            # Inicio de sesion via telnet al primer router
            child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
            child.expect("Username:")
            child.sendline(gns3_usr)
            child.expect("Password:")
            child.sendline(gns3_pwd)
            child.expect(hosts[0]['host'])

        move_into_routers(child, hosts, gns3_usr, gns3_pwd, con_method)

        child.sendline("config t")
        child.expect(last_host["host"])
        child.sendline(f"no username {usr_to_delete}")
        child.expect(last_host["host"])
        child.sendline("end")
        child.expect(last_host["host"])
        child.sendline("wr mem")
        child.expect(last_host['host'])
        child.close(force=True)
        log.info(f"Se ha eliminado el usuario del router via {con_method}")
        return make_response({"message": "Se ha eliminado el usuario en el router"}, 200)
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
    con_method = request_body["method"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Modificando protocolo en el router con IP: {last_host['ip']}")
    gns3_usr, gns3_pwd = get_gns3_config()
    try:
        if con_method == "ssh":
            # Primer inicio de sesion via ssh al primer router
            child = pxssh.pxssh()
            child.login(hosts[0]["ip"], gns3_usr,
                        gns3_pwd, auto_prompt_reset=False)
        else:
            # Inicio de sesion via telnet al primer router
            child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
            child.expect("Username:")
            child.sendline(gns3_usr)
            child.expect("Password:")
            child.sendline(gns3_pwd)
            child.expect(hosts[0]['host'])

        move_into_routers(child, hosts, gns3_usr, gns3_pwd, con_method)

        child.expect(last_host["host"])

        protocols_in_router = get_router_protocols(child, last_host["host"])
        
        child.sendline("config t")
        child.expect(last_host["host"])
        has_to_modify = len(protocols_in_router) > 0
        if has_to_modify:
            delete_protocols_from_router(child, last_host["host"], protocols_in_router)
        
        if protocol == "rip":
            log.info("Añadiendo protocolo rip")
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
        child.expect(last_host["host"])
        child.close()
        log.info(f"Se ha terminado de configurar el protocolo {protocol} con las redes {', '.join(networks)} via {con_method}")
        return make_response({"message": "Se ha modificado el protocolo existente" if has_to_modify else "Se ha anadido el protocolo"}, 200)
    except pexpect.TIMEOUT:
        log.warning(f"Tiempo de espera excedido")
        return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
    except Exception as ex:
        log.error(str(ex))
        return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)
    
@netapi_decorator("network")
def modify_router_settings(log = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    request_body = request.get_json()
    hosts = request_body["hosts"]
    hostname = request_body["hostname"] if "hostname" in request_body else None
    interfaces = request_body["interfaces"] if "interfaces" in request_body else None
    con_method = request_body["method"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Modificando la configuracion general del router con IP: {last_host['ip']}")
    gns3_usr, gns3_pwd = get_gns3_config()
    try:
        if con_method == "ssh":
            # Primer inicio de sesion via ssh al primer router
            child = pxssh.pxssh()
            child.login(hosts[0]["ip"], gns3_usr,
                        gns3_pwd, auto_prompt_reset=False)
        else:
            # Inicio de sesion via telnet al primer router
            child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
            child.expect("Username:")
            child.sendline(gns3_usr)
            child.expect("Password:")
            child.sendline(gns3_pwd)
            child.expect(hosts[0]['host'])

        move_into_routers(child, hosts, gns3_usr, gns3_pwd, con_method)

        child.expect(last_host["host"])

        # Configuramos los parametros enviados
        child.sendline("config t")
        child.expect(last_host["host"])

        expect_host = last_host["host"]

        if hostname is not None:
            log.info(f"Cambiando hostname del router {last_host['host']} a {hostname}")
            child.sendline(f'hostname {hostname}')
            expect_host = hostname
            #log.debug(last_host)
            child.expect(expect_host)
        
        if interfaces is not None:
            log.info(f"Cambiando interfaces del router {last_host['host']}")
            for interface in interfaces:
                log.info(f"Configurando interfaz {interface['name']}")
                child.sendline(f'int {interface["name"]}')
                child.expect(expect_host)
                if "shutdown" in interface:
                    log.debug(f"Se ha apagado la interfaz {interface['name']}")
                    child.sendline("shut")
                    child.expect(expect_host)
                elif "remove" in interface:
                    log.debug(f"Se ha eliminado IP de la interfaz {interface['name']}")
                    child.sendline("no ip add *")
                    child.expect(last_host["host"])
                elif "power":
                    log.debug(f"Se ha encendido la interfaz {interface['name']}")
                    child.sendline("no shut")
                    child.expect(expect_host)
                else:
                    log.debug(f"Se ha configurado la IP: {interface['ip']} en la interfaz {interface['name']}")
                    child.sendline(f'ip add {interface["ip"]} {interface["mask"]}')
                    child.sendline("no shut")
                    child.expect(expect_host)
        
        child.sendline("end")
        child.expect(expect_host)
        child.sendline("wr mem")
        child.expect(expect_host)
        child.close()
        log.info(f"Se ha terminado de configurar el router {expect_host}")
        return make_response({ "message": "Se ha aplicado la configuracion" })
    except pexpect.TIMEOUT:
        log.warning(f"Tiempo de espera excedido")
        return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
    except Exception as ex:
        log.error(str(ex))
        return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)


@netapi_decorator("network")
def activate_ssh_in_router(log = None):
    session_data = validate_session()
    if type(session_data) is Response:
        return session_data
    
    request_body = request.get_json()
    hosts = request_body["hosts"]
    last_host = hosts[len(hosts)-1]
    log.info(f"Activando SSH en el router con IP: {last_host['ip']}")
    gns3_usr, gns3_pwd = get_gns3_config()
    try:
        child = pexpect.spawn(f"telnet {hosts[0]['ip']}")
        child.expect("Username:")
        child.sendline(gns3_usr)
        child.expect("Password:")
        child.sendline(gns3_pwd)
        child.expect(hosts[0]['host'])

        move_into_routers(child, hosts, gns3_usr, gns3_pwd, "telnet")

        child.expect(last_host["host"])
        # Verificar si ya tiene  SSH

        child.sendline("sh run | s ssh")
        child.expect(last_host["host"])
        ssh_info = child.before.decode()

        if ssh_info != None:
            # Buscar si ya se tiene activado el protocolo
            if "transport input telnet ssh" in ssh_info:
                log.warning("El router ya tiene preconfigurado el protocolo SSH. Saliendo...")
                return make_response({ "message", "El router ya cuenta con conexión SSH activa" }, 200)

        # Aplicar la configuración por defecto de SSH
        usr, pwd, secret, vty = get_gns3_ssh_config()
        commands = ["config t", f"enable secret {secret}", "service password encryption", 
        "int lo0", "ip add 10.0.0.1 255.255.255.0", "no shut", 
        "crypto key generate rsa usage-keys label sshkey modulus 1024", "ip ssh rsa keypair-name sshkey", 
        "ip ssh v 2", "ip ssh time-out 30", "ip ssh authentication-retries 3", "line vty 0 15", f"password {vty}",
        "login local", "transport input ssh telnet", "exit", f"username {usr} privilege 15 {pwd}"]
        log.info(f"Configurando SSH en el router {last_host['host']} - {last_host['ip']}")
        for command in commands:
            log.warning(f"Ejecutando {command} == {last_host['host']}")
            child.sendline(command)
            child.expect(last_host["name"])
            child.expect(last_host["host"])
        
        log.info(f"Se ha terminado de configurar el acceso SSH en el router {last_host['host']}")
        return make_response({ "message": "Se ha configurado la conexión SSH en el router" }, 200)
    except pexpect.TIMEOUT:
        log.warning("Tiempo de espera de conexión excedido")
        return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
    except Exception as ex:
        log.error(str(ex))
        return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)
