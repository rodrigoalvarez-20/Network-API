
from utils.decorators import netapi_decorator

@netapi_decorator("general", "tokens")
def save_used_token(token: str, log=None, db=None):
    log.debug("Guardando token utilizada para el reestablecimiento de password")
    inserted = db.insert_one({"token": token})
    return inserted.inserted_id


@netapi_decorator("general", "tokens")
def search_used_token(token: str, log=None, db=None):
    log.debug("Buscando token en las tokens usadas")
    token_used = db.find_one({"token": token})
    return token_used
