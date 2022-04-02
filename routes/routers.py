from datetime import datetime
from utils.session_auth import validate_session
from utils.decorators import netapi_decorator
from flask import Response, make_response, request
import pexpect

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
    host = request_body["host"]
    ip = request_body["ip"]
    usr_to_add = request_body["username"]
    usr_pwd_to_add = request_body["pwd"]
    privilege = request_body["privilege"]
    log.info(f"Añadiendo usuario {usr_to_add} al router con IP: {ip}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    if ["ssh_usr", "ssh_pwd"] in request_body:
        #Hacerlo por SSH
        pass
    else:
        #Hacerlo via telnet con la cuenta por defecto de todos los routers 
        telnet_usr = request_body["telnet_usr"]
        telnet_pwd = request_body["telnet_pwd"]
        prompt = f"{host}#"
        try:
            log.info("Enviando comandos al router")
            child = pexpect.spawn(f"telnet {ip}")
            child.expect("Username:")
            child.sendline(telnet_usr)
            child.expect("Password:")
            child.sendline(telnet_pwd)
            child.expect(prompt)
            child.send(f"username {usr_to_add} privilege {privilege} password {usr_pwd_to_add}")
            child.expect(prompt)
            child.sendline("end")
            child.sendline("copy run start")
            child.sendline("")
            child.close()
            log.info(f"Se ha terminado de añadir el usuario")
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
    host = request_body["host"]
    ip = request_body["ip"]
    usr_to_update = request_body["username"]
    new_pwd = request_body["pwd"]
    privilege = request_body["privilege"]
    log.info(f"Modificando usuario {usr_to_update} del router con IP: {ip}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    if ["ssh_usr", "ssh_pwd"] in request_body:
        #Hacerlo por SSH
        pass
    else:
        #Hacerlo via telnet con la cuenta por defecto de todos los routers
        telnet_usr = request_body["telnet_usr"]
        telnet_pwd = request_body["telnet_pwd"]
        prompt = f"{host}#"
        try:
            log.info("Enviando comandos al router")
            child = pexpect.spawn(f"telnet {ip}")
            child.expect("Username:")
            child.sendline(telnet_usr)
            child.expect("Password:")
            child.sendline(telnet_pwd)
            child.expect(prompt)
            child.send(
                f"username {usr_to_update} privilege {privilege} password {new_pwd}")
            child.expect(prompt)
            child.sendline("end")
            child.sendline("copy run start")
            child.sendline("")
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
    host = request_body["host"]
    ip = request_body["ip"]
    usr_to_delete = request_body["username"]
    usr_pwd_to_delete = request_body["pwd"]
    log.info(f"Eliminando usuario {usr_to_delete} del router con IP: {ip}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    if ["ssh_usr", "ssh_pwd"] in request_body:
        #Hacerlo por SSH
        pass
    else:
        #Hacerlo via telnet con la cuenta por defecto de todos los routers
        telnet_usr = request_body["telnet_usr"]
        telnet_pwd = request_body["telnet_pwd"]
        prompt = f"{host}#"
        try:
            log.info("Enviando comandos al router")
            child = pexpect.spawn(f"telnet {ip}")
            child.expect("Username:")
            child.sendline(telnet_usr)
            child.expect("Password:")
            child.sendline(telnet_pwd)
            child.expect(prompt)
            child.send(f"no username {usr_to_delete} password {usr_pwd_to_delete}")
            child.expect(prompt)
            child.sendline("end")
            child.sendline("copy run start")
            child.sendline("")
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
    host = request_body["host"]
    ip = request_body["ip"]
    protocol = request_body["protocol"]
    log.info(f"Modificando protocolo en el router: {ip}")
    # Verificar si se va a hacer por SSH y en el caso, obtener las credenciales
    if ["ssh_usr", "ssh_pwd"] in request_body:
        #Hacerlo por SSH
        pass
    else:
        #Hacerlo via telnet con la cuenta por defecto de todos los routers
        telnet_usr = request_body["telnet_usr"]
        telnet_pwd = request_body["telnet_pwd"]
        prompt = f"{host}#"
        try:
            log.info("Enviando comandos al router")
            child = pexpect.spawn(f"telnet {ip}")
            child.expect("Username:")
            child.sendline(telnet_usr)
            child.expect("Password:")
            child.sendline(telnet_pwd)
            child.expect(prompt)
            log.info("Determinando los protocolos activos")
            child.sendline("show ip route")
            child.expect(prompt)
            sh_ip_rt = child.before.decode()

            

            #child.send(f"config t")
            child.expect(prompt)
            child.sendline("")


            child.sendline("end")
            child.sendline("copy run start")
            child.sendline("")
            child.close()
            log.info(f"Se ha terminado de añadir el usuario")
            return make_response({"message": "Se ha agregado el usuario al router"}, 200)
        except pexpect.TIMEOUT:
            log.warning(f"Tiempo de espera excedido")
            return make_response({"error": "Tiempo de espera en el router excedido"}, 500)
        except Exception as ex:
            log.error(str(ex))
            return make_response({"error": "Ha ocurrido un error al ejecutar el comando"}, 500)
