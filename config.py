# from configparser import ConfigParser
import os, re, collections
from pymongo import MongoClient

def load_config():
    # parser=ConfigParser()
    mongodb_user=os.environ.get("MONGO_USER")
    mongodb_pass=os.environ.get("MONGO_PASS")

    mongo_client = MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
    db = mongo_client.nyc

    ret=db.config.find_one({ "_id": {"$exists":True} },{"_id":False})
    ret2=db.pokemons.find   ({ "_id": {"$exists":True} },{"_id":False})
    # parser.read_dict({"DEFAULT":ret})
    # for i in parser['DEFAULT'].items():
    #     print(i)
    return ret,ret2

# def update_db():
#     parser=ConfigParser()
#     mongodb_user=os.environ.get("MONGO_USER")
#     mongodb_pass=os.environ.get("MONGO_PASS")
#
#     mongo_client = MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
#     db = mongo_client.nyc
#
#     db.config.replace_one({ "_id": {"$exists":True} },Config['DEFAULT'])
#     return

Config, ConfigPokemons = load_config()
