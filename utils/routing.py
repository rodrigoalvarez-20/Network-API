import pexpect
from utils.configs import get_gns3_config
from utils.decorators import netapi_decorator
from pexpect import pxssh


@netapi_decorator("network")
def move_into_routers(child, ip_list: list, method, usr, pwd, log=None):
    """
    Funcion que permite moverse entre routers, utilizando el protocolo especificado
    @param child: Instancia de spawn o pxssh
    @param routers_list: Lista de routers que se tiene que iterar
    @param usr: Usuario por defecto de telnet y ssh
    @param pwd: Pwd por defecto de telnet y ssh
    @param method: Metodo a utilizar para la conexion (ssh o telnet)
    """
    # Itera cada uno de los elementos (routers) desde 1 hasta el final
    for i in range(1, len(ip_list)):  
        log.info(f"Conectandose a router: {ip_list[i]}")
        if method == "ssh":
            # Enviamos el comando ssh por la terminal del router
            child.sendline(f"ssh -l {usr} {ip_list[i]}")
            #child.expect("Password:")
            child.sendline(pwd)
        elif method == "telnet":
            # Hacemos la conexion telnet directa
            child.sendline(f"telnet {ip_list[i]}")
            child.expect("Username:")
            child.sendline(usr)
            child.expect("Password:")
            child.sendline(pwd)


@netapi_decorator("network")
def connect_to_router(ip_list: list, method: str, log = None):
    log.info(f"Estableciendo conexion con el router: {ip_list[len(ip_list)-1]}")
    gns3_usr, gns3_pwd = get_gns3_config()
    try:
        if method == "ssh":
            # Primer inicio de sesion via ssh al primer router
            child = pxssh.pxssh()
            child.login(ip_list[0], gns3_usr,
                        gns3_pwd, auto_prompt_reset=False)
        else:
            # Inicio de sesion via telnet al primer router
            child = pexpect.spawn(f"telnet {ip_list[0]}")
            child.expect("Username:")
            child.sendline(gns3_usr)
            child.expect("Password:")
            child.sendline(gns3_pwd)
            child.expect("#")

        if len(ip_list) > 1:
            move_into_routers(child, ip_list, method, gns3_usr, gns3_pwd)

        return child
    except pexpect.TIMEOUT:
        log.warning(f"Tiempo de espera excedido")
        return { "error": "Tiempo de espera de conexión con el dispostivo excedido" }
    except Exception as ex:
        log.error(str(ex))
        return {"error":"Ha ocurrido un error al conectar con el dispositivo"}
