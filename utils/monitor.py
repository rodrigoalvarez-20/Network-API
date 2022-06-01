#
# Esta cosa debe de monitorear los dispositivos e interfaces que esten habilitados para ello
# 1. Checar la tabla de configs, para obtener las preferencias
# 2. Obtener los dispositivos e interfaces que se pueden monitorear desde la tabla monitor
# 3. Al obtener el total de paquetes, de los 3 tipos, si estos exceden el umbral de las configuraciones (los porcentajes), enviar la notificacion
# 4. Crear la plantilla de la notificacion

# 2 funciones: Mapear Devices, mapear interfaces

# Para hacer los calculos, se debe de tener en cuenta el total de paquetes en el dispositivo, el total de paquetes recibidos en ese momento,
#

from datetime import datetime
import os
from pprint import pprint
from time import sleep
from api.utils.configs import get_snmp_config
from api.utils.decorators import netapi_decorator
from pysnmp.entity.rfc3413.oneliner import cmdgen


from api.utils.metrics  import get_monitor_configurations, get_monitored_interfaces, get_metrics_from_device
from api.utils.snmpy import snmp_get
from api.utils.notify import save_notify

@netapi_decorator("monitor", "metrics")
def save_device_metrics(ip, device, acc_data: dict, in_packets = 0, in_discards = 0, in_errors = 0, out_packets = 0, out_discards = 0, out_errors = 0, log = None, db = None):

    log.info(f"Guardando valores de metricas del dispositivo: {device}")
   
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    in_data = { "x": stamp, "y": in_packets }
    in_disc = { "x": stamp, "y": in_discards }
    in_err = { "x": stamp, "y": in_errors }
    out_data = { "x": stamp, "y": out_packets }
    out_disc = { "x":stamp, "y": out_discards }
    out_err = { "x":stamp, "y": out_errors }
    
    update_ops = { 
        "$set": { "device": device, "ip": ip}, 
        "$push": { 
            "in_packets": in_data, 
            "in_discards": in_disc, 
            "in_errors": in_err,
            "out_packets": out_data,
            "out_discards": out_disc,
            "out_errors": out_err
        }
    }

    if acc_data != {}:
        update_ops["$set"] = { **update_ops["$set"], **acc_data  }

    #print(update_ops)

    db.update_one( { "$and": [ { "device": device }, { "ip": ip } ] } , update_ops, upsert=True)

@netapi_decorator("monitor", "metrics")
def initialize_device_metrics(ip, device, inital_data: dict, log = None, db = None):

    log.info(f"Inicializando valores de metricas del dispositivo: {device}")
   
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    in_data = { "x": stamp, "y": 0 }
    in_disc = { "x": stamp, "y": 0 }
    in_err = { "x": stamp, "y": 0 }
    out_data = { "x": stamp, "y": 0 }
    out_disc = { "x":stamp, "y": 0 }
    out_err = { "x":stamp, "y": 0 }

    update_ops = { 
        "$set": { "device": device, "ip": ip, **inital_data }, 
        "$push": { 
            "in_packets": in_data, 
            "in_discards": in_disc, 
            "in_errors": in_err,
            "out_packets": out_data,
            "out_discards": out_disc,
            "out_errors": out_err
        }
    }

    db.update_one( { "$and": [ { "device": device }, { "ip": ip } ] } , update_ops, upsert=True)

@netapi_decorator("monitor")
def generate_notify(type, device, ip, rcv_pkts, pkts, log = None):
    _, rcv_dest = get_snmp_config()
    log.info("Generando nueva alerta por traspaso de limite ")
    with open(f"{os.getcwd()}/templates/packets_notify.html", "r") as template:
        msg_body = template.read()
        msg_body = msg_body.replace("{INTERFACE}", device)
        msg_body = msg_body.replace("{IP}", ip)
        msg_body = msg_body.replace("{DESCRIPTION}", f"ha superado el limite de {type}")
        msg_body = msg_body.replace("{RCV_PKTS}", rcv_pkts)
        msg_body = msg_body.replace("{PACKETS_TYPE}", type.capitalize())
        msg_body = msg_body.replace("{NO_PACKETS}", pkts)
        img_data = None
        with open(f"{os.getcwd()}/templates/error_message.png", "rb") as rt:
            img_data = rt.read()

        save_notify("monitor.service@network.ipn", rcv_dest, "Reporte de monitoreo", msg_body, img_data)

@netapi_decorator("monitor")
def monitor_service(disc_pkts_per, dmg_pkts_per, log = None):
    available_dev = get_monitored_interfaces()
    #Obtener los aprametros de limite

    if len(available_dev) == 0:
        log.info("Sin interfaces habilitadas para el monitoreo")
    elif None in [disc_pkts_per, dmg_pkts_per]:
        log.warning("No hay configuraciones de monitoreo")
    else:
        for interface in available_dev:
            ip = interface["addr"]
            dev_name = interface["interfaces"]["name"]
            # Hacer el query hacia la interfaz,via snmp
            # Primer, obtener el indice de la interfaz
            int_idx = dev_name.split("/")[0]
            #print(int_idx)
            int_idx = int(int_idx[len(int_idx) - 1]) + 1
            commands = [
                cmdgen.MibVariable("IF-MIB", "ifInOctets", int_idx),
                cmdgen.MibVariable("IF-MIB", "ifInDiscards", int_idx),
                cmdgen.MibVariable("IF-MIB", "ifInErrors", int_idx),
                cmdgen.MibVariable("IF-MIB", "ifOutOctets", int_idx),
                cmdgen.MibVariable("IF-MIB", "ifOutDiscards", int_idx),
                cmdgen.MibVariable("IF-MIB", "ifOutErrors", int_idx),
                cmdgen.MibVariable("IF-MIB", "ifOperStatus", int_idx)
            ]
            
            data = snmp_get(ip, commands)
            # Debo de validar que no sean nulos, o que si haya respuesta
            if "error" in data:
                # No se ha obtenido la informacion por falla de disponibilidad
                # No hacer nada...
                log.error(f"Ha ocurrido un error al obtener la informacion para el monitoreo de la interfaz: {dev_name}@{ip}")
                save_device_metrics(ip, dev_name, {}, -5, -5, -5, -5, -5, -5)
            else:
                device_metrics = get_metrics_from_device(ip,dev_name)
                if device_metrics is None:
                    device_metrics = {}
                # Obtener los valores iniciales para cada opcion
                INITIAL_VALUE_IN_PACKETS = device_metrics["initial_in_packets"] if "initial_in_packets" in device_metrics else 0
                INITIAL_VALUE_IN_DISC = device_metrics["initial_in_disc_packets"] if "initial_in_disc_packets" in device_metrics else 0
                INITIAL_VALUE_IN_ERR = device_metrics["initial_in_err_packets"] if "initial_in_err_packets" in device_metrics else 0

                INITIAL_VALUE_OUT_PACKETS = device_metrics["initial_out_packets"] if "initial_out_packets" in device_metrics else 0
                INITIAL_VALUE_OUT_DISC = device_metrics["initial_out_disc_packets"] if "initial_out_disc_packets" in device_metrics else 0
                INITIAL_VALUE_OUT_ERR = device_metrics["initial_out_err_packets"] if "initial_out_err_packets" in device_metrics else 0


                router_in_pkts = int(data[f"IF-MIB::ifInOctets.{int_idx}"] / 84) - INITIAL_VALUE_IN_PACKETS # Se divide en 84 por el tam de los paquetes de TCP
                router_in_disc_pkts = int(data[f"IF-MIB::ifInDiscards.{int_idx}"]) - INITIAL_VALUE_IN_DISC
                router_in_err_pkts = int(data[f"IF-MIB::ifInErrors.{int_idx}"]) - INITIAL_VALUE_IN_ERR
                router_out_pkts = int(data[f"IF-MIB::ifOutOctets.{int_idx}"] / 84) - INITIAL_VALUE_OUT_PACKETS # Se divide en 84 por el tam de los paquetes de TCP
                router_out_disc_pkts = int(data[f"IF-MIB::ifOutDiscards.{int_idx}"]) - INITIAL_VALUE_OUT_DISC
                router_out_err_pkts = int(data[f"IF-MIB::ifOutErrors.{int_idx}"]) - INITIAL_VALUE_OUT_ERR
                # Obtenemos los datos guardados
                
                if device_metrics == {}:
                    #No se han encontrado registros, insertar valores por default (los iniciales de la interfaz), para inicializar
                    log.debug(f"Inicializando metricas de la interfaz: {dev_name}@{ip}")
                    initial_params = {
                        "initial_in_packets": router_in_pkts,
                        "initial_in_disc_packets": router_in_disc_pkts,
                        "initial_in_err_packets": router_in_err_pkts,
                        "initial_out_packets": router_out_pkts,
                        "initial_out_disc_packets": router_out_disc_pkts,
                        "initial_out_err_packets": router_out_err_pkts,
                        "acum_in_packets": 0,
                        "acum_in_disc_packets": 0,
                        "acum_in_err_packets": 0,
                        "acum_out_packets": 0,
                        "acum_out_disc_packets": 0,
                        "acum_out_err_packets": 0
                    }
                    pprint(initial_params)
                    initialize_device_metrics(ip, dev_name, initial_params)
                else:
                    #Registros existentes, realizar la manipulacion necesaria
                    # Pueden ser nulos (Primera vez)
                    mib_interface_status = f"IF-MIB::ifOperStatus.{int_idx}"
                    if data[mib_interface_status] == 2:
                        # Si la interfaz tiene un status de 2, significa que esta apagada, insertar Nulos
                        log.debug(f"La interfaz: {dev_name}@{ip} se encuentra apagada/inaccesible")
                        save_device_metrics(ip, dev_name, {}, -5, -5, -5, -5, -5, -5)
                    else: 
                        # Acumulados
                        acc_in_pkts = device_metrics["acum_in_packets"]
                        acc_in_disc = device_metrics["acum_in_disc_packets"]
                        acc_in_err = device_metrics["acum_in_err_packets"]
                        acc_out_pkts = device_metrics["acum_out_packets"]
                        acc_out_disc = device_metrics["acum_out_disc_packets"]
                        acc_out_err = device_metrics["acum_out_err_packets"]

                        act_rcv = router_in_pkts - acc_in_pkts # Total de paquetes recibidos en el intervalo de tiempo definido, con este hago las validaciones para las notificaciones
                        acc_in_pkts += act_rcv

                        act_in_disc_pkts = router_in_disc_pkts - acc_in_disc
                        acc_in_disc += act_in_disc_pkts

                        act_in_err_pkts = router_in_err_pkts - acc_in_err
                        acc_in_err += act_in_err_pkts

                        act_out = router_out_pkts - acc_out_pkts
                        acc_out_pkts += act_out

                        act_out_disc_pkts = router_out_disc_pkts - acc_out_disc
                        acc_out_disc += act_out_disc_pkts

                        act_out_err_pkts = router_out_err_pkts - acc_out_err
                        acc_out_err += act_out_err_pkts

                        # Total de paquetes es el act, validar que (disc_pkts * 100 / act_rcv) < parametro de configuracion
                        if act_rcv > 0:
                            if int(act_in_disc_pkts * 100 / act_rcv) >= disc_pkts_per:
                                #Mandar la notificacion de que el total de paquetes descartados ha pasado el limite
                                log.warning(f"La interfaz {dev_name}@{ip} ha sobrepasado el limite de paquetes descartados")
                                generate_notify("paquetes descartados", dev_name, ip, act_rcv, act_in_disc_pkts)
                            
                            if int(act_in_err_pkts * 100 / act_rcv) >= dmg_pkts_per:
                                #Mandar la notificacion de que el total de paquetes con errores ha pasado el limite
                                log.warning(f"La interfaz {dev_name}@{ip} ha sobrepasado el limite de paquetes con errores")
                                generate_notify("paquetes con errores", dev_name, ip, act_rcv, act_in_err_pkts)

                        log.info(f"Guardando datos de la interfaz {dev_name}@{ip}")
                        acc_data = {
                            "acum_in_packets": acc_in_pkts,
                            "acum_in_disc_packets": acc_in_disc,
                            "acum_in_err_packets": acc_in_err,
                            "acum_out_packets": acc_out_pkts,
                            "acum_out_disc_packets": acc_out_disc,
                            "acum_out_err_packets": acc_out_err
                        }
                        save_device_metrics(ip, dev_name, acc_data, act_rcv, act_in_disc_pkts, act_in_err_pkts, act_out, act_out_disc_pkts, act_out_err_pkts)


@netapi_decorator("monitor")
def run_service(log = None):
    log.warning("Iniciando servicio de monitoreo")
    interface_interval, disc_pkts_per, dmg_pkts_per, _ = get_monitor_configurations()
    while(True):
        monitor_service(disc_pkts_per, dmg_pkts_per)
        log.info(f"Monitor esperando {interface_interval} segundos...")
        sleep(interface_interval)

if __name__ == "__main__":
    run_service()
