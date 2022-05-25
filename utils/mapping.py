import json
from typing import Union
from utils.decorators import netapi_decorator
import pexpect
from pexpect import pxssh
import subprocess
from utils.configs import get_gns3_config

@netapi_decorator("mapping", None)
def get_ip_from_local_address(excluded, log = None):
    log.info("Obteniendo direcciones IP de la interfaz local")
    ip_ints = subprocess.getoutput("ifconfig | grep inet")
    ips_list =   ip_ints.split("\n")
    filtered_ips = filter(lambda x: x.find("inet6") == -1 and x.find("127.0.0.1") == -1, ips_list)
    local_nets = []
    for ip in filtered_ips:
        int_ip = ip.strip().split(" ")[1]
        addr_octets = int_ip.split(".")
        addr_octets[3] = "0"
        ip_addr = ".".join(addr_octets)
        if ip_addr not in excluded:
            local_nets.append( ".".join(addr_octets) )
    log.info(f"Direcciones IP del dispositivo {','.join(local_nets)}")
    return local_nets

@netapi_decorator("mapping", None)
def get_os_in_network(segment, log = None):
    log.info("Iniciando el proceso de sondeo en la red...")
    nmap =subprocess.getoutput(f"echo gns3 | sudo -S nmap -O {segment}/24")
    results = nmap.split("Nmap scan report for")
    del results[0]
    int_addr_of_routers = []
    for res in results:
        if "Cisco" in res:
            log.info("Router cisco encontrado")
            addr_text = res.split("\n")[0].split(" ")[2].replace("(", "").replace(")", "")
            int_addr_of_routers.append(addr_text)
    
    log.info(f"Dispositivos CISCO encontrados: {','.join(int_addr_of_routers)}")
    return int_addr_of_routers

@netapi_decorator("mapping")
def login_into_router(route : list, log = None):
    log.debug(f"Ruta actual: {','.join(route)}")
    gns3_usr, gns3_pwd = get_gns3_config()
    for i, ip in enumerate(route):
        log.info(f"Conectandose a {ip}")
        if i == 0:
            tn = pexpect.spawn(f"telnet {ip}")
        else:
            tn.sendline(f"telnet {ip}")
        tn.expect("Username:")
        tn.sendline(gns3_usr)
        tn.expect("Password:")
        tn.sendline(gns3_pwd)
        tn.expect("#")
    return tn    

def send_command(tn: Union[pexpect.spawn, pxssh.pxssh], command: str):
    tn.sendline(command)
    tn.expect("#")
    return tn.before.decode("utf8")

@netapi_decorator("mapping")
def get_ssh_status(tn: Union[pexpect.spawn, pxssh.pxssh], log = None):
    log.info("Obteniendo estado del servicio SSH en el dispositivo")
    out = send_command(tn, "sh ip ssh").split("\n")
    out.pop(0)
    ssh_stat = out[0]
    return ssh_stat.split(" ")[1] == "Enabled"

@netapi_decorator("mapping")
def get_router_protocols(tn: pexpect.spawn, log = None):
    log.info("Obteniendo protocolos del router")
    send_command(tn, "terminal length 0")
    out_lines = send_command(tn, "show ip protocol").split("\n")
    out_lines.pop(0)
    routing_protocols_data = [x for x in out_lines if x.startswith("Routing Protocol")]
    protocols_in_router = []
    for prot in routing_protocols_data:
        temp_p = prot.split("\"")
        protocols_in_router.append(temp_p[1])
    log.info(f"Protocolos encontrados: {', '.join(protocols_in_router)}")
    return protocols_in_router

@netapi_decorator("mapping")
def check_snmp_in_router(tn: pexpect.spawn, log = None):
    log.info("Obteniendo estado de SNMP en el dispositivo")
    send_command(tn,"terminal length 0")
    snmp_stat = send_command(tn, "sh snmp").split("\n")
    snmp_stat.pop(0)
    snmp_stat = snmp_stat[0].replace("\r", "").replace("%", "")
    return snmp_stat != "SNMP agent not enabled"

@netapi_decorator("mapping")
def get_router_hostname(tn : pexpect.spawn, log = None):
    log.info("Obteniendo nombre del dispositivo")
    out = send_command(tn, "sh run | s hostname")
    return out.split("\n")[1].split(" ")[1].replace("\r", "")

@netapi_decorator("mapping")
def get_interfaces_info(child: pexpect.spawn, log = None):
    log.info("Obteniendo informacion de las interfaces del dispositivo")
    child.sendline("sh ip int brief")
    child.expect("#")
    child.sendline("sh ip int brief")
    child.expect("#")
    interfaces_info : list = child.before.decode().split("\n")
    interfaces_info.pop(0)
    interfaces_info.pop(0)
    interfaces = []
    for int in interfaces_info:
        int_data =  [ str(x) for x in filter(lambda x: x != "", int.split(" ")) if str(x) != "\r"] 
        if len(int_data) > 1:
            log.debug("Interfaz encontrada")
            interfaces.append({ "interface": int_data[0], "ip": int_data[1], "status": int_data[4] if int_data[4] != "administratively" else int_data[5] })
    log.info(f"Interfaces encontradas: {json.dumps(interfaces)}")
    return interfaces

@netapi_decorator("mapping")
def get_cdp_output(child: pexpect.spawn, mapped_devices: list, root_device : str, log = None):
    log.info("Obteniendo informacion CDP del dispositivo")
    child.sendline("terminal length 0")
    child.expect("#")
    child.sendline("sh cdp entry *")
    child.expect("#")
    child.sendline("sh cdp entry *")
    child.expect("#")
    cdp_out = child.before.decode().split('-------------------------')
    external_devices = []
    for entry in cdp_out:
        if "Device ID" in entry:
            entry_lines = entry.split("\n")
            device_id = entry_lines[1].split(" ")[2].replace("\r", "")
            ip_addr = entry_lines[3].strip().split(" ")[2].replace("\r", "")
            addrs = entry_lines[5].strip().split(" ")
            interface_in = addrs[1].replace(",", "")
            interface_out = addrs[7].replace("\r", "")
            if device_id not in mapped_devices:
                external_devices.append({ "name": device_id, "address": ip_addr, "local_interface": interface_in,"external_interface": interface_out, "parent": root_device })
    log.debug(f"Dispositivos detectados: {json.dumps(external_devices)}")
    return external_devices