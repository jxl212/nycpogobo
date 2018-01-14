import os, sys, re, collections, datetime
import discord
import logging
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
from termcolor import cprint, colored
from utils import *

logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.WARNING)

client = discord.Client()

message_pattern = re.compile(r'.*?\*\*(?P<name>\w+)\*\*\s\((?P<iv>\d+)\%\)\s\-\s\(CP\:\s(?P<cp>\d+)\)\s-\s\(Level\:\s(?P<level>\d+)\).*\*\*Until\*\*\: (?P<time>\d\d\:\d\d\:\d\d)(?P<AMPM>\w\w).*IV\*\*\: (?P<atk>\d+) \- (?P<def>\d+) \- (?P<sta>\d+).*\*\*Gender\*\*: (?P<gender>\w+)?')
google_map_pattern = re.compile(r'\*\*Google Map\*\*: \<https\://maps\.google\.com/maps\?q\=(?P<lat_lon>.*)\>')
nycpokemap_pattern = re.compile(r'\*\*Map\*\*: \<https\://nycpokemap\.com\#.*\>')


async def send_discord_channel_embeded_message(guild_name, channel_name, embeded_text):
	c = discord.utils.get(client.get_all_channels(), guild__name=guild_name, name=str(channel_name))
	if c != None :
		await c.send(embed=embeded_text)
	else:
		cprint("Error for guild: {} for channel: {}".format(guild_name,str(channel_name)),"red")

async def process_message_for_discord(msg,iv,level):
	iv = int(iv) if iv else None
	level = int(level) if level else None
	if iv and iv >= 90 and iv < 100 and msg.channel.name == "iv90":
		channel_name="iv90"
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)
	if iv and iv == 100 and msg.channel.name == "iv100":
		channel_name="iv100"
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)
	if iv and iv == 0:
		channel_name="iv0"
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)
	if level and level >= 20 and level <= 30:
		channel_name = 'min-level-20'
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)
	if level and level >= 30:
		channel_name = 'min-level-30'
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)

@client.event
async def on_ready():
	print('Logged in as '+colored(client.user.name,attrs=['bold'])+' (ID:'+str(client.user.id)+')')
	print('Connected to '+colored(str(len(set(client.get_all_channels()))),attrs=['bold'])+' channels from guilds:'+', '.join([colored("{name} ({id})".format(name=s.name,id=str(s.id)),attrs=['bold']) for s in client.guilds]))

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
		if get_name(message).lower() in [channel.name for channel in message.guild.channels]:
			return

	boro=str(None)
	lat,lon=get_lat_lon_from_message(message)


	if lat != None and lon != None:
		boro = str(get_boro_from(lat=lat,lon=lon))

	neighborhood=str(get_neighborhood_from(lat,lon))

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

	name=get_name(message)
	nycpokemap_link = get_nycpokemap_url(message)
	gmap_link = get_googlmap_url(message)



	embed = discord.Embed(title=name, description=content, url=nycpokemap_link, color=0x000000)


	url_str=""
	level=m['level'] if m and 'level' in m.keys() else 0
	if name == 'Egg':
		level = get_raid_level(message)
		if level == "4":
			url_str="https://pro-rankedboost.netdna-ssl.com/wp-content/uploads/2017/06/Pokemon-GO-Rare-Egg-Yellow.png"
		elif level == "5":
			url_str="https://pro-rankedboost.netdna-ssl.com/wp-content/uploads/2017/06/Pokemon-GO-Legendary-Egg-120x120.png"
		else:
			first_line = message.content.split("\n")[0].lstrip().rstrip()
			cprint(first_line,"red")
	elif name:
		url_str='https://rankedboost.com/wp-content/plugins/ice/pokemon/'+name+'-Pokemon-Go.png'

	if url_str != "":
		embed.set_thumbnail(url=url_str)

	print(name, "{}%".format(int(m['iv'])), level, nycpokemap_link)
	color=0x00000
	if int(m['iv']) == 100:
		color|=0xD1C10F
	if int(m['level']) >= 30:
		color|=0x17479F
	if int(m['level']) >= 20 and int(m['iv']) >= 90:
		color|=0xAE1B25

	embed.color=color # color_from_message(message)

	is_raid=str(message.channel.name).startswith('raid')
	if neighborhood in ["washington-heights","fort-george"]:
		if is_raid:
			channel_name="raids"
			return await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)

		channel_name=neighborhood
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)

		process_message_for_groupme(msg,m['iv'],level)
		await process_message_for_discord(msg,m['iv'],level)

	if boro.lower() in ["manhattan"] and (is_raid == False):
		channel_name="manhattan"
		content="**{}**\n{}".format(neighborhood,content)
		embed.add_field(name="Area", value=neighborhood, inline=False)
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)


client.run(os.environ.get('TOKEN'), bot=False)
