import os
from cryptography.fernet import Fernet
import random
import jwt
from datetime import datetime, timezone, timedelta
from keyring import get_password


enc_pwd = get_password("network_api_service", "net_admin")
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

def generate_login_token(id: str, email : str):
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

def auth(token: str):
    try:
        with open(pKey, "r", encoding="utf-8") as key:
            decoded = jwt.decode(token, key.read(), algorithms=["RS256"])
            return {"status": 200, **decoded}
    except jwt.ExpiredSignatureError:
        return { "status": 401, "error": "La token ha expirado" }
    except jwt.PyJWTError as error:
        print(error)
        return {"status": 401, "error": str(error)}

if __name__ == "__main__":
    # Espacio reservado para pruebas
    pass
