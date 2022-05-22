# Ver por cual de las interfaces hacer la peticion, hacer la peticion a todos los Cisco Routers

# Una vez teniendo esos dispositivos iniciales, iterar en cada uno para ir armando las tablas

# Por cada dispositivo, ejecutar primero el sh ip in brief y obtener las interfaces, tanto apagadas como encendidas y su direccion IP
# Despues ejecutar el show cdp entry * para ir buscando los nombres de host, ips e interfaces que conectan

from pprint import pprint
import subprocess
from time import time
import json
import pexpect
from utils.configs import get_gns3_config
from utils.decorators import netapi_decorator

def get_ip_from_local_address(excluded):
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
    return local_nets

def get_os_in_network(segment):
    nmap =subprocess.getoutput(f"echo gns3 | sudo -S nmap -O {segment}/24")
    results = nmap.split("Nmap scan report for")
    del results[0]
    int_addr_of_routers = []
    for res in results:
        if "Cisco" in res:
            addr_text = res.split("\n")[0].split(" ")[2].replace("(", "").replace(")", "")
            int_addr_of_routers.append(addr_text)
            
    return int_addr_of_routers

@netapi_decorator("mapping")
def login_into_router(route : list, log = None):
    #log.debug("Actual map route: ", ",".join(route))
    gns3_usr, gns3_pwd = get_gns3_config()
    for i, ip in enumerate(route):
        log.debug(f"Logging to {ip}")
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

def send_command(tn : pexpect.spawn, command : str):
    tn.sendline(command)
    tn.expect("#")
    return tn.before.decode("utf8")

def get_router_hostname(tn : pexpect.spawn):
    #print("Getting router name...")
    out = send_command(tn, "sh run | s hostname")
    return out.split("\n")[1].split(" ")[1].replace("\r", "")

def get_interfaces_info(child: pexpect.spawn):
    #print("Getting interfaces info")
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
            interfaces.append({ "interface": int_data[0], "ip": int_data[1], "status": int_data[4] if int_data[4] != "administratively" else int_data[5] })

    return interfaces

def get_cdp_output(child: pexpect.spawn, mapped_devices: list, root_device : str):
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
    
    return external_devices
    
excluded_nets = ["192.168.100.0"]

@netapi_decorator("routers", "network_map")
def start_mapping(log = None, db = None):
    start = time()
    #nets = get_ip_from_local_address(excluded_nets)
    routers_net = []
    #for net in nets:
    #    routers_net += get_os_in_network(net)

    routers_net.append("10.0.0.254")
    routers_net.append("46.5.0.254")
    routers_map = {}

    actual_route = []
    hosts_maped = []
    
    routers_map = {}
    
    for router in routers_net:
        actual_route.append(router)
        tn_rt = login_into_router(actual_route) # Contiene la conexion telnet del dispositivo
        hostname = get_router_hostname(tn_rt)
        router_interfaces = get_interfaces_info(tn_rt)
        cdp_data = get_cdp_output(tn_rt, hosts_maped, hostname)
        routers_map[hostname] = { "name": hostname, "ip": router, "type": "root", "interfaces": router_interfaces}
        hosts_maped.append(hostname)
        for i,data in enumerate(cdp_data):
            #Moverse a los siguientes routers
            actual_route.append(data["address"])
            child_tn = login_into_router(actual_route)
            ch_hostname = get_router_hostname(child_tn)
            child_interfaces = get_interfaces_info(child_tn)
            
            ch_cdp = get_cdp_output(child_tn, hosts_maped, ch_hostname)

            if ch_hostname not in list(routers_map.keys()):
                last_router_ip = actual_route[len(actual_route)-2]
                root_host = ""
                for item in routers_map:
                    if routers_map[item]["ip"] == last_router_ip:
                        root_host = routers_map[item]["name"]

                routers_map[ch_hostname] = { "name": ch_hostname, "ip": data["address"], "type": "child", "parent": { "host": root_host, "ip": last_router_ip }, "route": ",".join(actual_route), "interfaces": child_interfaces}
            hosts_maped.append(ch_hostname)

            for j,c in enumerate(ch_cdp):
                cdp_data.insert(i+j+1, c)
            
            if len(ch_cdp) == 0:
                for i in range(0, len(actual_route) -1):
                    actual_route.pop()
                child_tn.close(True)
            
        if len(actual_route) != 0:
            actual_route.pop()

    end = time()

    with open("topo_map.json", "w") as f:
        f.write(json.dumps(routers_map))    

    log.debug("Se ha terminado de mapear la red")
    log.debug("Eliminando esquema anterior")
    db.delete_many({})
    log.debug("Insertando nuevo esquema")
    db.insert_one(routers_map)
            
    log.debug(f"Elapsed: {end - start}")


if __name__ == "__main__":
    start_mapping()
    
