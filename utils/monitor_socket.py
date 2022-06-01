from api.utils.decorators import netapi_decorator

@netapi_decorator("monitor", "configs")
def update_selected_metrics_interface(device, ip, log = None, db = None):
    log.info("Actualizando interfaz seleccionada a mostrar metricas")
    db.update_many({}, {"$set": { "selected_interface": {"device": device, "ip": ip} }}, upsert=True)
