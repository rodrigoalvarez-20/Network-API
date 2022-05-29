import multiprocessing
from time import sleep
import requests
from api.utils.decorators import netapi_decorator
from api.utils.common import send_email_message

from bson.objectid import ObjectId

def check_internet_status():
    url = "http://google.com"
    timeout = 5
    try:
        req = requests.get(url, timeout=timeout)
        return True
    except (requests.ConnectionError, requests.Timeout) as ex:
        return False

@netapi_decorator("general", "emails_queue")
def save_notify(remitente, destino, asunto, mensaje, imagen, log = None, db = None):
    log.info("Guardando email en DB")
    db.insert_one({
        "sender": remitente,
        "to": destino,
        "subject": asunto,
        "body": mensaje,
        "image": imagen
    })

    log.info("Se ha guardado el email")

@netapi_decorator("general", "emails_queue")
def notify_service(log = None, db = None):
    while(True):
        if(check_internet_status()):
            # Conexion activa, enviar los correos
            pending_emails = list(db.find({}).limit(10))
            emails_sent = []
            if(len(pending_emails) == 0):
                log.info("Sin emails pendientes")
            else:
                for email in pending_emails:
                    sender = email["sender"]
                    dest = email["to"]
                    sub = email["subject"]
                    body = email["body"]
                    img_data = email["image"]
                    log.info(f"Enviando email: {str(email['_id'])}")
                    send_email_message(sender, dest, sub, body, img_data)
                    emails_sent.append( ObjectId(email["_id"]))
                log.info(f"Emails enviados: {len(emails_sent)}")
                db.delete_many({ "_id": { "$in": emails_sent } })
            sleep(10)
        else:
            # La conexion no esta activa, seguir esperando
            log.info("Sin conexion a internet, esperando 5 segundos")
            sleep(5)
            
def notify_daemon():
    emails_pr = multiprocessing.Process(target=notify_service)
    emails_pr.start()
    print("Notify Process started")

if __name__ == "__main__":
    notify_daemon()
