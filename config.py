from configparser import ConfigParser

def load_config():
    parser=ConfigParser()
    ret=db.config.find_one({ "_id": {"$exists":True} },{"_id":False})
    parser.read_dict({"DEFAULT":ret})
    config = list(parser['DEFAULT'].items())
    return config

config = load_config()
