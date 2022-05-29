from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.proto.api import v2c

from api.utils.configs import get_gns3_config

snmpEngine = engine.SnmpEngine()

usr, pwd = get_gns3_config()

config.addTransport(snmpEngine, udp.domainName + (1,), udp.UdpTransport().openServerMode(("192.168.1.2", 162)))

config.addV1System(snmpEngine, "asr_network", "asr_network")
#config.addV1System()

#config.addV3User(snmpEngine, userName=usr,
#    authKey=pwd, privKey=pwd, authProtocol=config.usmHMACMD5AuthProtocol,
#    privProtocol=config.usmDESPrivProtocol
#    )

def cbFun(snmpEngine, stateReference, contextEngineId, contextName,
          varBinds, cbCtx):
    print("Message received")
    execContext = snmpEngine.observer.getExecutionContext('rfc3412.receiveMessage:request')
    print('#Notification from %s \n#ContextEngineId: "%s" \n#ContextName: "%s" \n#SNMPVER "%s" \n#SecurityName "%s"' % ('@'.join([str(x) for x in execContext['transportAddress']]),contextEngineId.prettyPrint(),contextName.prettyPrint(), execContext['securityModel'], execContext['securityName']))
    for name, val in varBinds:
        print(f"{name.prettyPrint()} = {val.prettyPrint()}")
        
    #pdu_count +=1

ntfrcv.NotificationReceiver(snmpEngine, cbFun)

snmpEngine.transportDispatcher.jobStarted(1)
try:
    print("Trap Listener started .....")
    snmpEngine.transportDispatcher.runDispatcher()
except:
    snmpEngine.transportDispatcher.closeDispatcher()
    raise