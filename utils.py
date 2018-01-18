import os, re,collections, datetime
import groupy
from groupy import Client
import discord
# from slackclient import SlackClient
from pymongo import MongoClient
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
groupme_bot_id=os.environ.get('GROUPME_BOT_ID')
groupme_bot_id_test="d435bc3deb78bb4d8158d47542"
groupme_bot=[b for b in groupme_client.bots.list() if b.data['bot_id']==groupme_bot_id][0]
groupme_test_bot=[b for b in groupme_client.bots.list() if b.data['bot_id']==groupme_bot_id_test][0]

print("I found a groupme_bot named: "+colored(groupme_bot.name,attrs=['bold']))
groupme_test_bot.post(text="I am alive....!")


def groupme_test_bot_post(txt):
	groupme_test_bot.post(text=text)

def format_for_groupme(content):
	content = str(content).split("\n")
	if len(content)>3:
		content=content[:-2]
	content = "\n".join(content)
	content = re.sub(r'L30\+ ','',content)
	content = re.sub(r'\*+','',content)
	content = re.sub(r'[\<|\>]','',content)
	content = re.sub(r'Map: ','',content)
	content = re.sub(r'\n+','\n',content)
	content = re.sub(r'\[.*?\]\s?','',content)
	return content

def send_groupme(msg,lat=None,lon=None):
	location=None
	if lat != None and lon != None:
		location=groupy.attachments.Location(name="loc",lat=lat,lng=lon)

	content = format_for_groupme(msg)

	attachments=None
	if location != None:
		attachments=[location]
	groupme_bot.post(text=content,attachments=attachments)

def process_message_for_groupme(data):
	min_level=Config.getint('DEFAULT','min_level')
	min_iv=Config.getint('DEFAULT','min_iv')
	if data.weather not in [None, "None", ""]:
		min_level+=Config.getint('DEFAULT','weather_level_mod')
		min_iv+=Config.getint('DEFAULT','weather_iv_mod')
	min_iv=min(100,min_iv)
	min_level=min(35,min_level)
	# cprint('min_iv: {} iv {}'.format(min_iv,data.iv),"cyan",end = ' ')
	# cprint('min_iv: {} iv {}'.format(min_level,data.level),"cyan", end=' ')
	if (data.iv in [0,100]) or (data.iv >= min_iv and data.level >= min_level):
		cprint("	✅	Sent to groupme!","green")
		send_groupme(data._raw_content,data.lat,data.lng)
	else:
		cprint("	❌	doesn't pass requirements","white")


# def send_slack(msg,lat=None,lon=None):
# 	slack_client.api_call("chat.postMessage",channel="general",text=re.sub(r'\*\*','`',msg))

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
	return ""

def get_neighborhood_from(lat,lon):
	if None in [lat,lon]:
		return ""
	name_field="name2"
	neighborhoods=db.neighborhoods.find_one({ "geometry": { "$geoIntersects": { "$geometry": { "type": "Point", "coordinates": [ float(lon), float(lat) ] } } } },{name_field:1})
	if neighborhoods :
		return str(neighborhoods[name_field])
	return ""

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
	return -1

def get_defense(msg):
	d=get_atk_def_sta(msg)
	if "def" in d:
		return int(d['def'])
	return -1
def get_stamina(msg):
	d=get_atk_def_sta(msg)
	if "sta" in d:
		return int(d['sta'])
	return -1
def get_first_line(msg):
	return msg.content.split("\n")[0].lstrip()

def get_name(msg):
	d=collections.defaultdict(str)
	first_line = msg.content.split("\n")[0].lstrip()
	match = re.match(r".*?\*\*(?P<name>\w+)\*\*.*?", first_line)
	if match and "name" in match.groupdict().keys():
		return match["name"]
	return ""

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
	return -1
def get_raid_level(msg):
	key="level"
	match = re.match(r'.*Level\: (?P<'+key+'>\d+)',msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		return int(match[key])
	return -1

def get_iv(msg):
	key="iv"
	match = re.match(r".*?\*\*\s\((?P<"+key+">\d+)\%\)\s", msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		return int(match[key])
	return -1
def get_cp(msg):
	key="cp"
	match = re.match(r".*?\s\(CP\:\s(?P<"+key+">\d+)\)\s", msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		return int(match[key])
	return -1

def get_weather_boosted(msg):
    # **Weather boosted**: None
	key="weather"
	match = re.match(r'.*\*\*Weather boosted\*\*\: (?P<'+key+'>.*?)\s\s',msg.content.replace("\n","  "))
	if match and key in match.groupdict().keys():
		return match[key]
	return ""

def is_weather_boosted(msg):
    # **Weather boosted**: None
	wb=get_weather_boosted(msg)
	is_boosted = wb not in [None, "None", ""]
	return is_boosted

def get_gender(msg):
    # **Weather boosted**: None
	key="gender"
	match = re.match(r'.*\*\*Gender\*\*: (?P<gender>\w+)',msg.content.replace("\n"," "))
	if match and key in match.groupdict().keys():
		if match[key] == "Female":
			return "female"
		elif match[key]=='Male':
			return "male"
		elif match[key]=='None':
			return "None"
	return ""

def get_despawn_time(message):
	text=re.sub(r"\n","",message.content)
	match = re.match(r'.*?\*\*Until\*\*\: (?P<h>\d\d?):(?P<m>\d\d+?):(?P<s>\d+)(?P<AMPM>\w\w) .*?', text)
	if match:
		h=int(match['h']) + 12 if match['AMPM'] == "PM" else int(match['h'])
		if h == 24:
			h = 0
		m=int(match['m'])
		s=int(match['s'])
		ts=datetime.datetime(message.created_at.year,message.created_at.month,message.created_at.day,h,m,s)
		return ts
def get_moveset(message):
	text=re.sub(r"\n","  ",message.content)
	match = re.match(r'.*?\*\*Moveset\*\*\: (?P<quick>.*?) - (?P<charge>.*?)\s\s', text)
	if match:
		return match.groupdict()
def get_address(message):
	text=re.sub(r"\n","  ",message.content)
	match = re.match(r'.*?\*\*Address\*\*\: (?P<address>.*?)\s\s', text)
	if match:
		return match['address']

def load_config_from_db(msg):
	Config = load_config()
