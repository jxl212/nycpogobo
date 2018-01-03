import os, sys
import discord
import logging
import os
import datetime
import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import platform
import re
import collections
import pprint
from pymongo import MongoClient
from termcolor import cprint, colored
import groupy
from groupy import Client
from slackclient import SlackClient


logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.WARNING)
    
client = discord.Client()
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
groupme_client = Client.from_token(os.environ.get('GROUPME_TOKEN'))
mongodb_user=os.environ.get("MONGO_USER")
mongodb_pass=os.environ.get("MONGO_PASS")

mongo_client = MongoClient("mongodb+srv://{}:{}@cluster0-m6kv9.mongodb.net/nyc".format(mongodb_user,mongodb_pass))
client = discord.Client()
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
groupme_client = Client.from_token(os.environ.get('GROUPME_TOKEN'))
groupme_bot=[b for b in groupme_client.bots.list() if b.data['bot_id']=='074f9a78a1efbcf9f0d44e60a5'][0]
print("mongodb guild version: "+colored(mongo_client.server_info()['version'],attrs=['bold']))

db = mongo_client.nyc
if db is None:
	exit()


chat_channels = collections.defaultdict(int)
message_pattern = re.compile(r'.*?\*\*(?P<name>\w+)\*\*\s\((?P<iv>\d+)\%\)\s\-\s\(CP\:\s(?P<cp>\d+)\)\s-\s\(Level\:\s(?P<level>\d+)\).*\*\*Until\*\*\: (?P<time>\d\d\:\d\d\:\d\d)(?P<AMPM>\w\w).*IV\*\*\: (?P<atk>\d+) \- (?P<def>\d+) \- (?P<sta>\d+).*\*\*Gender\*\*: (?P<gender>\w+)?')
google_map_pattern = re.compile(r'\*\*Google Map\*\*: \<https\://maps\.google\.com/maps\?q\=(?P<lat_lon>.*)\>')
nycpokemap_pattern = re.compile(r'\*\*Map\*\*: \<https\://nycpokemap\.com\#.*\>')


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

def send_slack(msg,lat=None,lon=None):
	slack_client.api_call("chat.postMessage",channel="general",text=re.sub(r'\*\*','`',msg))

		

@client.event
async def on_ready():
	print('Logged in as '+colored(client.user.name,attrs=['bold'])+' (ID:'+str(client.user.id)+')')
	print('Connected to '+colored(str(len(set(client.get_all_channels()))),attrs=['bold'])+' channels from guilds:'+', '.join([colored("{name} ({id})".format(name=s.name,id=str(s.id)),attrs=['bold']) for s in client.guilds]))
	

	
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
	match = re.match(r".*?IV\*\*\: (?P<atk>\d+) \- (?P<def>\d+) \- (?P<sta>\d+)", str(msg))
	if match:
		d=match.groupdict()
		
	return d
def get_name(msg):
	d=collections.defaultdict(str)
	match = re.match(r".*?\*\*(?P<name>\w+)\*\* \(", str(msg))
	if match:
		d=match.groupdict()
		
	return d['name']

def get_color_from_stats(a,d,s):
	color = 0x000000
	color = (((int(a)<<4 | int(d)) << 4) | int(s)) << 8
	return color

def color_from_message(msg):
	d=get_atk_def_sta(msg)
	return get_color_from_stats(d['atk'], d['def'], d['sta'])

@client.event
async def on_message(message):
	if message.guild == None:
		return
	
	if message.guild.name != "NYCPokeMap":
		return

	if message.channel == None:
		return

	if message.channel.name in ["general","info","rules","token-needed","rais-chat"]:
		return

	if message.channel.name in ["cp2500","iv90","iv100"]:
		if get_name(message.clean_content).lower() in [channel.name for channel in message.guild.channels]:
			return
	
	boro=str(None)
	lat,lon=get_lat_lon_from_message(message)
	

	if lat != None and lon != None:
		boro = str(get_boro_from(lat=lat,lon=lon))

	neighborhood=None
	
	neighborhood=get_neighborhood_from(lat,lon)
		
	m=collections.defaultdict(int)
	matches = message_pattern.match(message.content.replace("\n"," "))
	if matches:
		m=matches

	content = message.clean_content
	content = content.split("\n")[:-3]
	content = "\n".join(content)
	content = re.sub(r'\[.*\]\s?','',content)
	content = re.sub(r'\n+','\n',content)
	content = content.replace("**L30+ ","**")

	# content = "```md\n{name} ({iv}%) lvl: {level}, until: {t}{xm}\n```".format(name=m['name'], iv=m['iv'], level=m['level'], t=m['time'],xm=m['AMPM'])
	gender="N.A."

	if m and m['gender']=='Female':
		gender = "♀"
	elif m and m['gender']=='Male':
		gender = "♂"

	# match = nycpokemap_pattern.findall(message.content.replace("\n",""))
	match = re.findall(r'\<https\://nycpokemap\.com.*?\>',message.content.replace("\n"," "))
	map_link = str(match)
	nycpokemap_link = ""
	if match!=None:
		map_link = re.sub(r'[\<|\>]','',match[0])
		nycpokemap_link=map_link

	match = re.findall(r'\<https\://maps\.google\.com.*?\>',message.content.replace("\n"," "))
	gmap_link = str(match)
	if match!=None:
		gmap_link = re.sub(r'[\<|\>]','',match[0])
		

	txt = ""
	if m :
		txt = "{}".format(gender + " " + m['name']+ " " +  "({}%)".format(m['iv'])+ " " +  m['level']+ " " +  m['time'] + m['AMPM'] +" ")
	# else :
	txt = message.channel.name,"["+str(boro) + "/" +str(neighborhood) + "] - {}{}".format(txt, map_link)
	ctxt = colored(txt,"white")
	
	embed = discord.Embed(title=m['name'], description=content, color=0x000000)
	
	if len(nycpokemap_link) > 0 :
		embed.url=nycpokemap_link
	if m['name']:
		embed.set_thumbnail(url="https://rankedboost.com/wp-content/plugins/ice/pokemon/{}-Pokemon-Go.png".format(m['name']))
	color=0x00000
	
	if int(m['iv']) == 100:
		color|=0xD1C10F
	if int(m['level']) >= 30:
		color|=0x17479F
	if int(m['level']) >= 20 and int(m['iv']) >= 90:
		color|=0xAE1B25

	embed.color=color # color_from_message(message)

	
	if  str(neighborhood) in ["washington-heights","fort-george"]:
		c=None
		if str(message.channel.name).startswith('raid'):
			c = discord.utils.get(client.get_all_channels(), guild__name='PoGoWHeights', name=str("raids"))
			if c != None :
				ctxt = colored(txt,"white")
				await c.send(embed=embed)
			else:
				cprint("Error for channel {}".format("raids"),"red")
		else:
			
			c = discord.utils.get(client.get_all_channels(), guild__name='PoGoWHeights', name=str(neighborhood))
			if c != None :
				ctxt = colored(txt,"blue")
				await c.send(embed=embed)
			else:
				cprint("Error for channel {}".format(neighborhood),"red")

			if int(m['iv'])>=80 and int(m['level'])>=20:
				send_groupme(message.clean_content,lat,lon)


			if int(m['iv']) in range(90,99) and message.channel.name == "iv90":
				c=None
				channel_name="iv90"
				c = discord.utils.get(client.get_all_channels(), guild__name='PoGoWHeights', name=channel_name)
				if c != None:
					await c.send(embed=embed)
				else:
					cprint("Error for channel {}".format(channel_name),"red")
			if int(m['iv'])==100 and message.channel.name == "iv100":
				c=None
				channel_name="iv100"
				c = discord.utils.get(client.get_all_channels(), guild__name='PoGoWHeights', name=channel_name)
				if c != None:
					await c.send(embed=embed)
				else:
					cprint("Error for channel {}".format(channel_name),"red")
			
			if int(m['level']) in range (20,29) :
				channel_name = 'min-level-20'
				c = discord.utils.get(client.get_all_channels(), guild__name='PoGoWHeights', name=channel_name)
				if c != None:
					await c.send(embed=embed)
				else:
					cprint("Error for channel {}".format(channel_name),"red")
			if int(m['level'])>=30 :
				channel_name = 'min-level-30'
				c = discord.utils.get(client.get_all_channels(), guild__name='PoGoWHeights', name=channel_name)
				if c != None:
					await c.send(embed=embed)
				else:
					cprint("Error for channel {}".format(channel_name),"red")

	
	c=None
	if str(message.channel.name).startswith('raid'):
		return
	else:
		c_name="manhattan"
		content="**{}**\n{}".format(neighborhood,content)
		embed.add_field(name="Area", value=str(neighborhood), inline=False)
		c = discord.utils.get(client.get_all_channels(), guild__name='PoGoWHeights', name=c_name)
		if c != None :
			await c.send(embed=embed)

		else:
			cprint("Error for channel {}".format(c_name),"red")


client.run(os.environ.get('TOKEN'), bot=False)