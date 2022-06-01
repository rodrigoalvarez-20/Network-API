from datetime import datetime
import os
import subprocess
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

from api.utils.configs import get_gns3_config, get_snmp_config
from api.utils.decorators import netapi_decorator
from api.utils.notify import save_notify

snmp_engine = engine.SnmpEngine()

usr, pwd = get_gns3_config()

excluded_oids = [ "1.3.6.1.4.1.9.9.43","1.3.6.1.4.1.9.9.138"]

config.addTransport(snmp_engine, udp.domainName + (1,),
                    udp.UdpTransport().openServerMode(("0.0.0.0", 162)))

config.addV1System(snmp_engine, "asr_network", "asr_network")

# config.addV3User(snmpEngine, userName=usr,
#    authKey=pwd, privKey=pwd, authProtocol=config.usmHMACMD5AuthProtocol,
#    privProtocol=config.usmDESPrivProtocol
#    )

def translate(oid):
    return subprocess.Popen(['snmptranslate', oid ],  stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0].decode().replace("\n", "")


@netapi_decorator("network", "email_queue")
def traps_cb(engine, data_2, ctx_id, ctx_name, var_binds, data, db = None, log = None):
    exec_context = engine.observer.getExecutionContext('rfc3412.receiveMessage:request')
    log.info("Se ha recibido una notificacion SNMP")
    sender = '@'.join([str(x) for x in exec_context['transportAddress']])
    version =  exec_context['securityModel']
    group_name = exec_context['securityName']
    
    send_notify = True
    lines = [ f"{translate(name.prettyPrint())} == {name.prettyPrint()} == {val.prettyPrint()}\n" for name, val in var_binds ]
    for ex in excluded_oids:
        if  ex.find(lines[2].split(" == ")[1]) >= 0:
            send_notify = False
            break 
    
    if send_notify:
        _, rcvs = get_snmp_config()
        with open(f"{os.getcwd()}/templates/trap_message.html", "r") as template:
            body = template.read()
            oid_data = lines[2].split(" == ")[1].split(".")
            oid_data[len(oid_data)-2] = "x"
            oid_data[len(oid_data)-1] = "x"
            body = body.replace("{IP}", sender.split("@")[0])
            body = body.replace("{IP_GROUP}", sender)
            body = body.replace("{VERSION}", str(version))
            body = body.replace("{GROUP}", str(group_name))
            body = body.replace("{OID}", ".".join(oid_data))
            body = body.replace("{OIDT}", lines[3].split(" == ")[0])
            if "9.9.41" in lines[2]:
                # Es de tipo notificacion de interfaz
                body = body.replace("{TRAP_HEADER}", "SYSLog Cisco Interface")
                body = body.replace("{DESC}", lines[5].split(" == ")[2])   
            elif "9.9.43" in lines[2] or "1.3.6.1.2.1.14" in lines[2]:
                #Se ha realizado cambios en los protocolos de enrutamiento
                body = body.replace("{TRAP_HEADER}", "Cisco routing/config modify")
                body = body.replace("{DESC}", "Se ha modificado la configuracionen el router")
            else:
                #Todos los demas, yo espero que si se traduzcan correctamente (Dar un mensaje general)
                body = body.replace("{TRAP_HEADER}", "Interface management")
                body = body.replace("{DESC}", f"{lines[3].split(' == ')[2]} --> {lines[5].split(' == ')[2]}")
                
            html_lines = [ x.replace("\n", "<br/>") for x in lines ]
            body = body.replace("{RAW}", "".join(html_lines))
            body = body.replace("{sentAt}", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

            img_data = None
            with open(f"{os.getcwd()}/templates/router_email.png", "rb") as rt:
                img_data = rt.read()

            save_notify("networknotify@noreply.ipn", rcvs, "Servicio de notificaciones", body, img_data)

ntfrcv.NotificationReceiver(snmp_engine, traps_cb)

snmp_engine.transportDispatcher.jobStarted(1)
try:
    print("Escuchando Traps/Informs...")
    snmp_engine.transportDispatcher.runDispatcher()
except:
    snmp_engine.transportDispatcher.closeDispatcher()
    raise
