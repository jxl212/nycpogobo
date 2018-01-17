import os, re, datetime
import groupy
from groupy import Client
import discord
from slackclient import SlackClient
from pymongo import MongoClient
import collections
from termcolor import cprint, colored

from config import *


class MessageContent:
	"""docstring for McessageContent."""

	__slots__ = ("_raw_content", "lat", "lng",
	"boro", "neighborhood", "name",
	"iv", "level", "cp", "gender",
	"attack", "stamina", "defense",
	"weather", "egg_level",
	"despawn_time", "moveset",
	"address", "nycpokemap_url","embed",
	"original_channel_name")

	def __init__(self,message):
		self.parse(message)


	def parse(self,message):
		self._raw_content=message.clean_content
		self.lat,self.lng = get_lat_lon_from_message(message)
		self.boro = get_boro_from(self.lat,self.lng)
		self.neighborhood = get_neighborhood_from(self.lat,self.lng)
		self.name = get_name(message)
		self.iv = get_iv(message)
		self.level = get_level(message)
		self.cp = get_cp(message)
		self.gender = get_gender(message)
		self.attack = get_attack(message)
		self.stamina = get_stamina(message)
		self.defense = get_defense(message)
		self.weather = get_weather_boosted(message)
		self.egg_level = get_raid_level(message)
		self.despawn_time = get_despawn_time(message)
		self.moveset= get_moveset(message)
		self.address=get_address(message)
		self.nycpokemap_url=get_nycpokemap_url(message)
		self.make_embed_from_message()
		self.original_channel_name=message.channel.name


	def make_embed_from_message(self):
		content = self._raw_content
		content = content.split("\n")[:-3]
		content = "\n".join(content)
		content = re.sub(r'\[.*\]\s?','',content)
		content = re.sub(r'\n+','\n',content)
		content = content.replace("**L30+ ","**")
		self.embed = discord.Embed(title=self.name, description=content, url=self.nycpokemap_url, color=0x000000)

		url_str=""
		if self.name == 'Egg':
			# level = get_raid_level(message)
			if self.egg_level == 4:
				url_str="https://pro-rankedboost.netdna-ssl.com/wp-content/uploads/2017/06/Pokemon-GO-Rare-Egg-Yellow.png"
			elif self.egg_level == 5:
				url_str="https://pro-rankedboost.netdna-ssl.com/wp-content/uploads/2017/06/Pokemon-GO-Legendary-Egg-120x120.png"
			else:
				first_line = self._raw_content.split("\n")[0].lstrip().rstrip()
				cprint(first_line,"red")
		elif self.name:
			url_str='https://rankedboost.com/wp-content/plugins/ice/pokemon/'+self.name+'-Pokemon-Go.png'

		if url_str != "":
			self.embed.set_thumbnail(url=url_str)

		color=0x00000
		if self.iv == 100:
			color|=0xD1C10F
		if self.level >= 30:
			color|=0x17479F
		if self.level >= 20 and self.iv >= 90:
			color|=0xAE1B25

		self.embed.color=color # color_from_message(message)


	def __str__(self):
		return ", ".join((\
			"{}".format(self.name),
			colored("{}% ({}-{}-{})".format(self.iv,self.attack,self.defense,self.stamina),attrs=['bold']),
			colored(str(self.level),attrs=['bold']),
			colored(self.gender,"green" if self.gender not in ["",None,"None"] else None, attrs=['bold']),
			"{}".format(self.boro),
			"{}".format(self.neighborhood),
			colored("{}".format(self.weather), "blue" if self.weather not in [None,"None",""] else None),
			"{}".format(self.nycpokemap_url)
			)
		)


	def get_formated_embed_content(self):
		return "{}".format(
			"\n".join((\
				"{}".format(self.name),
				colored("{}% ({}-{}-{})".format(self.iv,self.attack,self.defense,self.stamina),attrs=['bold']),
				colored("{}".format(self.level),attrs=['bold']),
				colored("{}".format(self.gender),"green" if self.gender not in ["",None,"None"] else None, attrs=['bold']),
				"{}".format(self.boro), "{}".format(self.neighborhood),
				colored("{}".format(self.weather), "blue" if self.weather not in [None,"None",""] else None),
				"{}".format(self.nycpokemap_url)
				)
			)
		)

	def is_raid(self):
		return self.original_channel_name.startswith('raid')



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

def process_message_for_groupme(data):
	print("process_message_for_groupme " + str(data))

	min_level=Config.getint('DEFAULT','min_level')
	min_iv=Config.getint('DEFAULT','min_iv')
	if data.weather not in [None, "None", ""]:
		min_level+=Config.getint('DEFAULT','weather_level_mod')
		min_iv+=Config.getint('DEFAULT','weather_iv_mod')

	if (data.iv in [0,100]) or (data.iv >= min_iv and data.level >= min_level):
		print("	⬆︎	Sent to groupme!")
		send_groupme(data._raw_content,data.lat,data.lng)

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
			return "🚺"
		elif match[key]=='Male':
			return "🚹"
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
