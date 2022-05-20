from email.mime.text import MIMEText
import smtplib
import ssl
import jwt
import random
import os, rsa
from cryptography.fernet import Fernet
from datetime import datetime, timezone, timedelta
from keyring import get_password
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey.RSA import import_key

#get_password("network_api_service", "net_admin")
enc_pwd = "wVs9pwr-aKLhVKRvv19sKU2TVpFIyOgat206qbKzlvc="
pKey = f"{os.getcwd()}/keys/public.pub"
pvKey = f"{os.getcwd()}/keys/private.key"


def encrypt_data(plain) -> str:
    f = Fernet(enc_pwd.encode())
    enc = f.encrypt(plain.encode())
    return enc.decode()

def decrypt_data(enc) -> str:
    f = Fernet(enc_pwd.encode())
    dec = f.decrypt(enc.encode())
    return dec.decode()

def encrypt_rsa_data(plain) -> str:
    with open(pKey, "rb") as p:
        public_key = rsa.PublicKey.load_pkcs1(p.read())
        return rsa.encrypt(plain.encode(), public_key)

def decrypt_rsa_data(enc) -> str:
    with open(pvKey, "rb") as p:
        private_key = import_key(p.read())
        print(private_key)
        return PKCS1_OAEP.new(private_key).decrypt(enc)

def generate_login_token(id: str, email: str):
    exp_date = datetime.now(tz=timezone.utc) + timedelta(days=1)
    payload = {
        "id": id,
        "email": email,
        "rd": random.randint(0, 1000000),
        "exp": exp_date
    }
    with open(pvKey, "r", encoding="utf-8") as key:
        tk = jwt.encode(payload, key.read(), algorithm="RS256")
        return tk

def generate_restore_pwd_token(email: str):
    exp_date = datetime.now(tz=timezone.utc) + timedelta(minutes=20)
    payload = {
        "email": email,
        "rd": random.randint(0, 1000000),
        "exp": exp_date
    }
    with open(pvKey, "r", encoding="utf-8") as key:
        tk = jwt.encode(payload, key.read(), algorithm="RS256")
        return tk

def auth(token: str):
    try:
        with open(pKey, "r", encoding="utf-8") as key:
            decoded = jwt.decode(token, key.read(), algorithms=["RS256"])
            return {"status": 200, "message": "Token correcta", **decoded}
    except jwt.ExpiredSignatureError:
        return {"status": 401, "error": "La token ha expirado"}
    except jwt.PyJWTError as error:
        print(error)
        return {"status": 401, "error": str(error)}

def send_email_message(sender: str, to: str, subject: str, body: str, image_data: str = None):
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to

    message.attach(MIMEText(body, "html"))

    if(image_data):
        msg_img = MIMEImage(image_data)
        msg_img.add_header('Content-ID', '<logo_image>')
        message.attach(msg_img)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login("rodrigoalvarez449@gmail.com", "aqcpddlpkeqroldt")
        server.sendmail(sender, to, message.as_string())


if __name__ == "__main__":
    # Espacio reservado para pruebas
    #send_email_message("rodrigoalvarez449@gmail", "paurodriguez0728@gmail.com", "Correo de prueba", "Este es un mensaje de prueba")
    pass
