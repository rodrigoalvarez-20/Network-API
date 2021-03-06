from pymongo import MongoClient

from api.utils.configs import get_mongo_config

def get_mongo_client():
    usr, pwd, host, _ = get_mongo_config()
    if host == "localhost":
        return MongoClient(host,27017)
    else:
        cnstr = f"mongodb+srv://{usr}:{pwd}@{host}/db_test?retryWrites=true&w=majority"
        return MongoClient(cnstr)
    