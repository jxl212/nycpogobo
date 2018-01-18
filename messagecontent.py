import re, collections, datetime
import discord
from utils import *


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
		self.embed=None
		self.make_embed_from_message()
		self.original_channel_name="{}".format(message.channel.name).lower()


	def make_embed_from_message(self):
		content = self._raw_content
		content = content.split("\n")[:-3]
		content = "\n".join(content)
		content = re.sub(r'\[.*\]\s?','',content)
		content = re.sub(r'\n+','\n',content)
		content = content.replace("**L30+ ","**")
		self.embed = discord.Embed(title=self.name, description=content, url=self.nycpokemap_url, color=0x000000)
		self.embed.add_field(name=self.boro, value=self.neighborhood, inline=False)
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
		txt=colored("{}".format(self.name).ljust(15), attrs=['bold'] if self.iv > 90 and self.attack==15 else []).rjust(15)

		if not self.is_raid():
			txt+=" "+colored("{}%".format(self.iv).rjust(5), attrs=['bold'] if self.iv > 90 else [])
			txt+=" "+colored("({:>2} / {:>2} / {:>2})".format(self.attack,self.defense,self.stamina), attrs=['bold'] if self.attack == 15 else [])
			txt+=" "+colored("{}".format(self.level).ljust(3),attrs=['bold'] if self.level > 30 else [])
		else:
			txt+= " level "+colored("{}".format(self.egg_level),attrs=['bold'])

		txt+=" {:10}".format(self.gender if self.gender: else "")
		txt+=" {:15}".format(self.boro)
		txt+=" {:20.20}".format(self.neighborhood)
		txt+=" "+colored("{:<15}".format(self.weather), "blue" if self.weather not in [None,"None",""] else None)
		txt+=" {:10}".format(self.original_channel_name)
		txt+=" {}".format(self.nycpokemap_url)
		if self.iv > 90 and self.attack == 15 and self.level > 30:
			txt = colored(re.sub(r"\x1b\[\d+m","",txt),"yellow",attrs=['bold','reverse'])
		return txt



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
