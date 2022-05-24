# Ver por cual de las interfaces hacer la peticion, hacer la peticion a todos los Cisco Routers

# Una vez teniendo esos dispositivos iniciales, iterar en cada uno para ir armando las tablas

# Por cada dispositivo, ejecutar primero el sh ip in brief y obtener las interfaces, tanto apagadas como encendidas y su direccion IP
# Despues ejecutar el show cdp entry * para ir buscando los nombres de host, ips e interfaces que conectan

from pprint import pprint

from time import time
import json
from utils.decorators import netapi_decorator
from utils.mapping import check_snmp_in_router, get_ip_from_local_address, get_os_in_network, get_router_protocols, get_ssh_status, \
    login_into_router, get_router_hostname, get_interfaces_info, get_cdp_output

excluded_nets = ["192.168.100.0"]

@netapi_decorator("mapping", "network_map")
def start_mapping(log = None, db = None):
    start = time()
    #nets = get_ip_from_local_address(excluded_nets)
    routers_net = []
    #for net in nets:
    #    routers_net += get_os_in_network(net)

    routers_net.append("10.0.0.254")
    routers_net.append("46.5.0.254")

    log.info("Iniciando el proceso de mapeo")
    log.info(f"Redes disponibles: {','.join(routers_net)}")

    routers_map = {}

    actual_route = []
    hosts_maped = []
    
    routers_map = {}
    
    for router in routers_net:
        actual_route.append(router)
        tn_rt = login_into_router(actual_route) # Contiene la conexion telnet del dispositivo
        hostname = get_router_hostname(tn_rt)
        router_interfaces = get_interfaces_info(tn_rt)
        # Obtener el protocolo (Listo)
        protocols_in_router = get_router_protocols(tn_rt)
        # Obtener si tiene el estado del SSH (Listo)
        ssh_status = get_ssh_status(tn_rt) 
        # Obtener el estado del SNMP
        snmp_stat = check_snmp_in_router(tn_rt)
        # Si tiene el SNMP activo, obtener la informacion
        # Me importa el OID especifico del dispositivo, hostname, contact info
        cdp_data = get_cdp_output(tn_rt, hosts_maped, hostname)
        routers_map[hostname] = { 
            "name": hostname, 
            "ip": router, 
            "ssh_v2": ssh_status,
            "snmp-v3": snmp_stat,
            "protocols": protocols_in_router,
            "type": "root", 
            "interfaces": router_interfaces, 
            
        }
        hosts_maped.append(hostname)
        for i,data in enumerate(cdp_data):
            #Moverse a los siguientes routers
            actual_route.append(data["address"])
            child_tn = login_into_router(actual_route)
            ch_hostname = get_router_hostname(child_tn)
            child_interfaces = get_interfaces_info(child_tn)

            ssh_status_child = get_ssh_status(child_tn)
            protocols_in_child_router = get_router_protocols(child_tn)
            child_snmp_stat = check_snmp_in_router(child_tn)
            
            ch_cdp = get_cdp_output(child_tn, hosts_maped, ch_hostname)

            if ch_hostname not in list(routers_map.keys()):
                last_router_ip = actual_route[len(actual_route)-2]
                root_host = ""
                for item in routers_map:
                    if routers_map[item]["ip"] == last_router_ip:
                        root_host = routers_map[item]["name"]

                routers_map[ch_hostname] = { 
                    "name": ch_hostname, 
                    "ip": data["address"], 
                    "ssh_v2": ssh_status_child, 
                    "snmp-v3": child_snmp_stat,
                    "protocols": protocols_in_child_router,
                    "interfaces": child_interfaces,
                    "route": ",".join(actual_route),
                    "type": "child", 
                    "parent": { "host": root_host, "ip": last_router_ip }
                }
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

    log.info("Se ha terminado de mapear la red")
    log.debug("Eliminando esquema anterior")
    db.delete_many({})
    log.info("Insertando nuevo esquema")
    db.insert_one(routers_map)
            
    log.info(f"Tiempo de mapeo: {end - start} segundos")


if __name__ == "__main__":
    start_mapping()
    
