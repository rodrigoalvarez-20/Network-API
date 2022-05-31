from api.utils.decorators import netapi_decorator


@netapi_decorator("monitor", "configs")
def get_monitor_configurations(log=None, db=None):
    log.info("Obteniendo las configuraciones guardadas")
    configs = list(db.find({}))

    if len(configs) == 0:
        log.warning("Aun no hay configuraciones guardadas para el monitoreo")
        return None, None, None
    else:
        configs = configs[0]
        interface_interval = 10
        disc_pkts_per = 10
        dmg_pkts_per = 10

        if "interface_interval" in configs:
            interface_interval = int(configs["interface_interval"])

        if "lost_packets_percentage" in configs:
            disc_pkts_per = int(configs["lost_packets_percentage"])

        if "damaged_packets_percentage" in configs:
            dmg_pkts_per = int(configs["damaged_packets_percentage"])

        return interface_interval, disc_pkts_per, dmg_pkts_per


@netapi_decorator("monitor", "monitor")
def get_monitored_interfaces(log=None, db=None):
    pipeline = [
        {
            "$project": {"_id": 0}
        },
        {
            "$match": {"interfaces.status": True}
        },
        {
            "$unwind": "$interfaces"
        },
        {
            "$match": {"interfaces.status": True}
        }
    ]
    mon_list = list(db.aggregate(pipeline))

    return mon_list


@netapi_decorator("monitor", "metrics")
def get_metrics_from_device(ip, device, log=None, db=None):
    log.info(f"Obteniendo metricas del dispositivo: {device}")
    return db.find_one({"$and": [{"device": device}, {"ip": ip}]})
