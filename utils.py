import os, re
import groupy
from groupy import Client
from slackclient import SlackClient
from pymongo import MongoClient
import collections
from termcolor import cprint, colored
from config import *


mongodb_user=os.environ.get("MONGO_USER")
mongodb_pass=os.environ.get("MONGO_PASS")

mongo_client = MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
db = mongo_client.nyc
if db is None:
	exit()
print("mongodb server version: "+colored(mongo_client.server_info()['version'],attrs=['bold']))
groupme_client = Client.from_token(os.environ.get('GROUPME_TOKEN'))
groupme_bot=[b for b in groupme_client.bots.list() if b.data['bot_id']=='074f9a78a1efbcf9f0d44e60a5'][0]

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def send_groupme(msg,lat=None,lon=None):
	location=None
	if lat != None and lon != None:
		location=groupy.attachments.Location(name="loc",lat=lat,lng=lon)

	content = str(msg).split("\n")
	if len(content)>3:
		content=content[:-2]
	content = "\n".join(content)
	content = re.sub(r'L30\+ ','',content)
	content = re.sub(r'\*+','',content)
	content = re.sub(r'[\<|\>]','',content)
	content = re.sub(r'Map: ','',content)
	content = re.sub(r'\n+','\n',content)
	content = re.sub(r'\[.*?\]\s?','',content)

	attachments=None
	if location != None:
		attachments=[location]
	groupme_bot.post(text=content,attachments=attachments)

def process_message_for_groupme(msg,lat,lng,iv,level=None):
	print("process_message_for_groupme({},{},{})".format(get_first_line(msg),iv,level))
	if iv == None:
		iv = -1
	iv = int(iv)

	if level == None:
		level=0
	level=int(level)

	min_level=int(config['min_level'])
	min_iv=int(config['min_iv'])
	if is_weather_boosted(msg):
		min_level+=int(config['weather_level_mod'])
		min_iv+=int(config['weather_iv_mod'])

	if (iv in [0,100]) or (iv >= min_iv and level >= min_level):
		print("	⬆︎	Sent to groupme!")
		send_groupme(msg.clean_content,lat,lng)

def send_slack(msg,lat=None,lon=None):
	slack_client.api_call("chat.postMessage",channel="general",text=re.sub(r'\*\*','`',msg))

def get_lat_lon_from_message(message):
	lat_lon = re.findall(r'\*\*Google Map\*\*: \<https\://maps\.google\.com/maps\?q\=(?P<lat>.*),(?P<lon>.*)\>',message.content)
	lat=float(0)
	lon=float(0)
	if lat_lon :
		lat = float(lat_lon[0][0])
		lon = float(lat_lon[0][1])
	return lat,lon

def get_boro_from(lat,lon):
	if None in [lat,lon]:
		return None
	boros=db.boro.find_one({ "geometry": { "$geoIntersects": { "$geometry": { "type": "Point", "coordinates": [ lon, lat ] } } } },{"properties.BoroName":1})
	if boros:
		boro = str(boros['properties']['BoroName'])
		return boro
	return None

def get_neighborhood_from(lat,lon):
	if None in [lat,lon]:
		return None
	name_field="name2"
	neighborhoods=db.neighborhoods.find_one({ "geometry": { "$geoIntersects": { "$geometry": { "type": "Point", "coordinates": [ float(lon), float(lat) ] } } } },{name_field:1})
	if neighborhoods :
		return str(neighborhoods[name_field])
	return None

def get_atk_def_sta(msg):
	d=collections.defaultdict(int)
	match = re.match(r".*?IV\*\*\: (?P<atk>\d+) \- (?P<def>\d+) \- (?P<sta>\d+)", msg.content.replace("\n"," "))
	if match:
		d=match.groupdict()
	return d

def get_attack(msg):
	d=get_atk_def_sta(msg)
	if "atk" in d:
		return int(d['atk'])
	return None

def get_first_line(msg):
	return msg.content.split("\n")[0].lstrip()

def get_name(msg):
	d=collections.defaultdict(str)
	first_line = msg.content.split("\n")[0].lstrip()
	match = re.match(r".*?\*\*(?P<name>\w+)\*\*.*?", first_line)
	if match and "name" in match.groupdict().keys():
		return match["name"]
	return

def get_nycpokemap_url(msg):
	match = re.match(r'.*<(?P<link>https\://nycpokemap\.com.*?)>\s',msg.content.replace("\n"," "))
	if match and "link" in match.groupdict().keys():
		return match['link']
	return ""

def get_googlmap_url(msg):
	match = re.match(r'.*<(?P<link>https\://maps\.google\.com.*?)>\s',msg.content.replace("\n"," "))
	if match and "link" in match.groupdict().keys():
		return match['link']
	return ""

def get_color_from_stats(a,d,s):
	color = 0x000000
	color = (((int(a)<<4 | int(d)) << 4) | int(s)) << 8
	return color

def color_from_message(msg):
	d=get_atk_def_sta(msg)
	return get_color_from_stats(d['atk'], d['def'], d['sta'])

def get_level(msg):
	key="level"
	match = re.match(r'.*\s\(Level\:\s(?P<'+key+'>\d+)\)\s',msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		return int(match[key])
	return 0
def get_raid_level(msg):
	key="level"
	match = re.match(r'.*Level\: (?P<'+key+'>\d+)',msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		return match[key]
	return ""

def get_iv(msg):
	key="iv"
	match = re.match(r".*?\*\*\s\((?P<"+key+">\d+)\%\)\s", msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		return match[key]
	return None

def get_weather_boosted(msg):
    # **Weather boosted**: None
	key="weather"
	match = re.match(r'.*\*\*Weather boosted\*\*\: (?P<'+key+'>\w+)\s',msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		return match[key]
	return ""

def is_weather_boosted(msg):
    # **Weather boosted**: None
	wb=get_weather_boosted(msg)
	is_boosted = wb not in [None, "None", ""]
	return is_boosted



def load_config_from_db(msg):
	config = load_config()
