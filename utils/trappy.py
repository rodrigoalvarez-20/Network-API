from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

from api.utils.configs import get_gns3_config
from utils.decorators import netapi_decorator

snmp_engine = engine.SnmpEngine()

usr, pwd = get_gns3_config()

config.addTransport(snmp_engine, udp.domainName + (1,),
                    udp.UdpTransport().openServerMode(("192.168.1.2", 162)))

config.addV1System(snmp_engine, "asr_network", "asr_network")

# config.addV3User(snmpEngine, userName=usr,
#    authKey=pwd, privKey=pwd, authProtocol=config.usmHMACMD5AuthProtocol,
#    privProtocol=config.usmDESPrivProtocol
#    )

@netapi_decorator("network")
def traps_cb(engine, _, ctx_id, ctx_name, var_binds, __, log = None):
    exec_context = engine.observer.getExecutionContext('rfc3412.receiveMessage:request')
    log.info("Se ha recibido una notificacion SNMP")
    print(exec_context)
    print(ctx_id.prettyPrint())
    print(ctx_name.prettyPrint())
    for name, val in var_binds:
        # Ver como obtener informacion y encolar el mensaje
        print(f"{name.prettyPrint()} = {val.prettyPrint()}")


ntfrcv.NotificationReceiver(snmp_engine, traps_cb)

snmp_engine.transportDispatcher.jobStarted(1)
try:
    print("Escuhando Traps/Informs...")
    snmp_engine.transportDispatcher.runDispatcher()
except:
    snmp_engine.transportDispatcher.closeDispatcher()
    raise
