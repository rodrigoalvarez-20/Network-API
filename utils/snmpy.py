
import sys
from api.utils.configs import get_gns3_config
from pysnmp.entity.rfc3413.oneliner import cmdgen

SYSNAME = '1.3.6.1.2.1.1.5.0'

#host = '192.168.1.254'

usr, pwd = get_gns3_config()

auth = cmdgen.UsmUserData(userName=usr, authKey=pwd, authProtocol=cmdgen.usmHMACMD5AuthProtocol, privKey=pwd, privProtocol=cmdgen.usmDESPrivProtocol)

def send_snmp_get_cmd(host, oid):
    
    cmdGen = cmdgen.CommandGenerator()
    #cmdgen.MibVariable(SYSNAME)
    errorIndication, errorStatus, _, varBinds = cmdGen.getCmd(auth, cmdgen.UdpTransportTarget((host, 161)), oid)
    
    
    if errorIndication:
        print("In error")
        print(varBinds)
        print(errorStatus)
        return None

    print(varBinds[0][1])

    for oid, val in varBinds:
        print(oid.prettyPrint(), val.prettyPrint())

if __name__ == "__main__":
    send_snmp_get_cmd("192.168.1.254", SYSNAME)