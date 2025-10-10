from pymongo import MongoClient

def get_db():
    client = MongoClient('mongodb://root:rootpassword@localhost:27017/')
    db = client['worlds_earthcam']
    return db
