from api.utils.configs import get_gns3_config, get_snmp_config
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp import hlapi

#"1.3.6.1.2.1.1.1",
#"1.3.6.1.2.1.1.2",
#"1.3.6.1.2.1.1.3",
#"1.3.6.1.2.1.1.4",
#"1.3.6.1.2.1.1.5",
#"1.3.6.1.2.1.1.6"
COMMANDS = {
    "DESC": "1.3.6.1.2.1.1.1.0",
    "ID": "1.3.6.1.2.1.1.2.0",
    "UPTIME": "1.3.6.1.2.1.1.3.0",
    "CONTACT": "1.3.6.1.2.1.1.4.0",
    "NAME": "1.3.6.1.2.1.1.5.0",
    "LOCATION": "1.3.6.1.2.1.1.6.0"
}

usr, pwd = get_gns3_config()
group, _ = get_snmp_config()

hlapi.UsmUserData(usr, 
    authKey=pwd, 
    privKey=pwd,
    authProtocol=hlapi.usmHMACMD5AuthProtocol,
    privProtocol=hlapi.usmDESPrivProtocol)

def snmp_get(target, oids, credentials = hlapi.CommunityData(group), port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]

def snmp_set(target, value_pairs, credentials = hlapi.CommunityData(group), port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.setCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_value_pairs(value_pairs)
    )
    return fetch(handler, 1)[0]

def construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types

def fetch(handler, count):
    result = []
    for _ in range(count):
        try:
            error_indication, error_status, error_index, var_binds = next(handler)
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    itm_name = var_bind[0].prettyPrint()
                    items[itm_name] = cast(var_bind[1])
                result.append(items)
            else:
                #return [{"error": str(error_indication)}]
                raise RuntimeError('SNMP error: {0}'.format(error_indication))
        except StopIteration:
            break
    return result

def construct_value_pairs(list_of_pairs):
    pairs = []
    for key, value in list_of_pairs.items():
        pairs.append(hlapi.ObjectType(hlapi.ObjectIdentity(key), value))
    return pairs

def cast(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        try:
            return float(value)
        except (ValueError, TypeError):
            try:
                return str(value)
            except (ValueError, TypeError):
                pass
    return value

if __name__ == "__main__":
    #print(snmp_get("128.0.0.254", ["1.3.6.1.2.1.1.4.0"]))
    print(snmp_set("128.0.0.254", {"1.3.6.1.2.1.1.4.0": "test Value"}))
    print(snmp_get("128.0.0.254", ["1.3.6.1.2.1.1.4.0"]))
    #snmp_set("128.0.0.254", {COMMANDS["CONTACT"]: "Router admin", COMMANDS["LOCATION"]: "Lab-2"})
    #print(snmp_get("128.0.0.254", [COMMANDS["CONTACT"], COMMANDS["LOCATION"]]))