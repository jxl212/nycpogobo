from configparser import ConfigParser
import os, re, collections
from pymongo import MongoClient

def load_config():
    global Config
    parser=ConfigParser()
    mongodb_user=os.environ.get("MONGO_USER")
    mongodb_pass=os.environ.get("MONGO_PASS")

    mongo_client = MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
    db = mongo_client.nyc

    ret=db.config.find_one({ "_id": {"$exists":True} },{"_id":False})
    parser.read_dict({"DEFAULT":ret})
    Config = collections.defaultdict(int)
    for k in parser['DEFAULT'].keys():
        Config[k]=parser['DEFAULT'][k]
    return Config

Config = load_config()
