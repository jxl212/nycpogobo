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

# async def send_config_to_sender(msg):
# 	txt=str(Config)
# 	print(Config)
# 	await msg.channel.send(txt)
#
# async def get_min_iv(msg):
# 	txt="Min IV: " + str(Config['min_iv'])
# 	await msg.channel.send(txt)
#
# async def get_min_level(msg):
# 	txt="Min Level: " + str(Config['min_level'])
# 	await msg.channel.send(txt)
#
# async def set_min_iv(msg):
# 	new_value=message.clean_content.split(" ")[1]
# 	print("set_min_iv", new_value)
# 	Config['min_iv']=int(new_value)
# 	update_db()
#
# async def set_min_level(msg):
# 	new_value=message.clean_content.split(" ")[1]
# 	print("set_min_level", new_value)
# 	Config['min_level']=int(new_value)
# 	update_db()
#
# commands={
#     "!reload":reload_config,
#     "!info":send_config_to_sender,
# 	"!get min_iv":get_min_iv,
# 	"!set min_iv":set_min_iv,
# 	"!get min_level":get_min_level,
# 	"!set min_level":set_min_level
# }

async def send_discord_channel_embeded_message(guild_name, channel_name, embeded_text):
	c = discord.utils.get(client.get_all_channels(), guild__name=guild_name, name=str(channel_name))
	if c != None :
		await c.send(embed=embeded_text)
	else:
		cprint("Error for guild: {} for channel: {}".format(guild_name,str(channel_name)),"red")

async def process_message_for_discord(data):

	if data.iv >= 90 and data.iv < 100:
		channel_name="iv90"
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, data.embed)
		if data.original_channel_name != "iv90":
			print("should we be ignoring ? " + data.name, data.iv, data.original_channel_name ," cause double post prevention?")
	elif data.iv == 100:
		channel_name="iv100"
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, data.embed)
		if data.original_channel_name != "iv100":
			print("should we be ignoring ? " + data.name, data.iv, data.original_channel_name ," cause double post prevention?")
	elif data.iv == 0:
		channel_name="iv0"
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, data.embed)
	if data.level >= 20 and data.level < 30:
		channel_name = 'min-level-20'
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, data.embed)
	elif data.level >= 30:
		channel_name = 'min-level-30'
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, data.embed)

@client.event
async def on_ready():
	print('Logged in as '+colored(client.user.name,attrs=['bold'])+' (ID:'+str(client.user.id)+')')
	print('Connected to '+colored(str(len(set(client.get_all_channels()))),attrs=['bold'])+' channels from guilds:'+', '.join([colored("{name}".format(name=s.name,id=str(s.id)),attrs=['bold']) for s in client.guilds]))

@client.event
async def on_message(message):
	# if message.clean_content in commands.keys():
	# 	print(cmd)
	# 	await commands[message.clean_content](message)
	# 	return

	if message.guild == None:
		return

	if message.guild.name != "NYCPokeMap":
		return

	if message.channel == None:
		return

	if message.channel.name in ["general","info","rules","token-needed","rais-chat"]:
		return

	the_message_data=MessageContent(message)

	if the_message_data.neighborhood in ["washington-heights","fort-george","highbridge-park"]:
		if the_message_data.is_raid():
			channel_name="raids"
			return await send_discord_channel_embeded_message('PoGoWHeights', channel_name, the_message_data.embed)

		pokestats.update(the_message_data.name)
		# txt=", ".join((name, "{}%".format(iv), str(level), "(f:{})".format(pokestats.spawn_per_hour(name)), boro, neighborhood, str(is_raid), str(get_weather_boosted(message)), nycpokemap_link))
		print(the_message_data)

		channel_name=the_message_data.neighborhood
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, the_message_data.embed)

		process_message_for_groupme(the_message_data)
		await process_message_for_discord(the_message_data)

	if the_message_data.boro.lower() in ["manhattan"] and (the_message_data.is_raid() == False):
		channel_name="manhattan"
		# content="**{}**\n{}".format(the_message_data.neighborhood,content)
		the_message_data.embed.add_field(name="Area", value=the_message_data.neighborhood, inline=False)
		await send_discord_channel_embeded_message('PoGoWHeights', channel_name, the_message_data.embed)


client.run(os.environ.get('TOKEN'), bot=False)
