import os, sys, re, collections, datetime
import discord
import logging
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
from termcolor import cprint, colored
from utils import *
from poke_stats import *



logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.WARNING)

client = discord.Client()

message_pattern = re.compile(r'.*?\*\*(?P<name>\w+)\*\*\s\((?P<iv>\d+)\%\)\s\-\s\(CP\:\s(?P<cp>\d+)\)\s-\s\(Level\:\s(?P<level>\d+)\).*\*\*Until\*\*\: (?P<time>\d\d\:\d\d\:\d\d)(?P<AMPM>\w\w).*IV\*\*\: (?P<atk>\d+) \- (?P<def>\d+) \- (?P<sta>\d+).*\*\*Gender\*\*: (?P<gender>\w+)?')
google_map_pattern = re.compile(r'\*\*Google Map\*\*: \<https\://maps\.google\.com/maps\?q\=(?P<lat_lon>.*)\>')
nycpokemap_pattern = re.compile(r'\*\*Map\*\*: \<https\://nycpokemap\.com\#.*\>')

async def reload_config(msg):
	load_config_from_db(msg)
	print(Config)

async def send_config_to_sender(msg):
	txt=str(Config)
	print(Config)
	await msg.channel.send(txt)

async def get_min_iv(msg):
	txt="Min IV: " + str(Config['min_iv'])
	await msg.channel.send(txt)

async def get_min_level(msg):
	txt="Min Level: " + str(Config['min_level'])
	await msg.channel.send(txt)

async def set_min_iv(msg):
	new_value=message.clean_content.split(" ")[1]
	print("set_min_iv", new_value)
	Config['min_iv']=int(new_value)
	update_db()

async def set_min_level(msg):
	new_value=message.clean_content.split(" ")[1]
	print("set_min_level", new_value)
	Config['min_level']=int(new_value)
	update_db()

commands={
    "!reload":reload_config,
    "!info":send_config_to_sender,
	"!get min_iv":get_min_iv,
	"!set min_iv":set_min_iv,
	"!get min_level":get_min_level,
	"!set min_level":set_min_level
}

async def send_discord_channel_embeded_message(guild_name, channel_name, embeded_text):
	c = discord.utils.get(client.get_all_channels(), guild__name=guild_name, name=str(channel_name))
	if c != None :
		await c.send(embed=embeded_text)
	else:
		cprint("Error for guild: {} for channel: {}".format(guild_name,str(channel_name)),"red")

async def process_message_for_discord(msg,embed,iv,level):
	iv = int(iv) if iv else -1
	level = int(level) if level else -1
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
	print('Connected to '+colored(str(len(set(client.get_all_channels()))),attrs=['bold'])+' channels from guilds:'+', '.join([colored("{name}".format(name=s.name,id=str(s.id)),attrs=['bold']) for s in client.guilds]))

@client.event
async def on_message(message):
	if message.clean_content in commands.keys():
		print(cmd)
		await commands[message.clean_content](message)
		return

	if message.guild == None:
		return

	if message.guild.name != "NYCPokeMap":
		return

	if message.channel == None:
		return

	if message.channel.name in ["general","info","rules","token-needed","rais-chat","iv100"]:
		return


	the_message_data=MessageContent()
	the_message_data.parse(message)

	# boro=str(None)
	# lat,lon=get_lat_lon_from_message(message)
	# name=get_name(message)
	# nycpokemap_link = get_nycpokemap_url(message)
	# gmap_link = get_googlmap_url(message)
	# iv=get_iv(message)
	if the_message_data.name.lower() in message.channel.name:
		if the_message_data.iv >= 90:
			print("ignoring " + the_message_data.name, the_message_data.iv ," cause double post prevention?")
			return
	# level=get_level(message)
	# gender=get_gender(message)
	is_raid=str(message.channel.name).startswith('raid')
	# weather=get_weather_boosted(message)
	# if lat != None and lon != None:
	# 	boro = str(get_boro_from(lat=lat,lon=lon))
    #
	# neighborhood=str(get_neighborhood_from(lat,lon))
	# stats=get_atk_def_sta(message)
	# txt=", ".join((\
	# 	name,
	# 	colored("{}% ({})".format(iv,stats),attrs=['bold']),
	# 	colored(str(level),attrs=['bold']),
	# 	colored(gender,"green" if gender not in ["",None,"None"] else None, attrs=['bold']),
	# 	boro, neighborhood,
	# 	colored(weather, "blue" if is_weather_boosted(message) else None), nycpokemap_link))
    #


	content = message.clean_content
	content = content.split("\n")[:-3]
	content = "\n".join(content)
	content = re.sub(r'\[.*\]\s?','',content)
	content = re.sub(r'\n+','\n',content)
	content = content.replace("**L30+ ","**")
	embed = discord.Embed(title=the_message_data.name, description=content, url=nycpokemap_link, color=0x000000)

	url_str=""
	if the_message_data.name == 'Egg':
		# level = get_raid_level(message)
		if the_message_data.egg_level == 4:
			url_str="https://pro-rankedboost.netdna-ssl.com/wp-content/uploads/2017/06/Pokemon-GO-Rare-Egg-Yellow.png"
		elif the_message_data.egg_level == 5:
			url_str="https://pro-rankedboost.netdna-ssl.com/wp-content/uploads/2017/06/Pokemon-GO-Legendary-Egg-120x120.png"
		else:
			first_line = message.content.split("\n")[0].lstrip().rstrip()
			cprint(first_line,"red")
	elif the_message_data.name:
		url_str='https://rankedboost.com/wp-content/plugins/ice/pokemon/'+name+'-Pokemon-Go.png'

	if url_str != "":
		embed.set_thumbnail(url=url_str)

	color=0x00000
	if the_message_data.iv == 100:
		color|=0xD1C10F
	if the_message_data.level >= 30:
		color|=0x17479F
	if the_message_data.level >= 20 and the_message_data.iv >= 90:
		color|=0xAE1B25

	embed.color=color # color_from_message(message)





	if the_message_data.neighborhood in ["washington-heights","fort-george","highbridge-park"]:
		if is_raid:
			channel_name="raids"
			return await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)

		pokestats.update(the_message_data.name)
		# txt=", ".join((name, "{}%".format(iv), str(level), "(f:{})".format(pokestats.spawn_per_hour(name)), boro, neighborhood, str(is_raid), str(get_weather_boosted(message)), nycpokemap_link))
		print(the_message_data)

		channel_name=the_message_data.neighborhood
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)

		process_message_for_groupme(the_message_data)
		await process_message_for_discord(message,embed,the_message_data.iv,the_message_data.level)

	if the_message_data.boro.lower() in ["manhattan"] and (is_raid == False):
		channel_name="manhattan"
		content="**{}**\n{}".format(the_message_data.neighborhood,content)
		embed.add_field(name="Area", value=the_message_data.neighborhood, inline=False)
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, embed)


client.run(os.environ.get('TOKEN'), bot=False)
