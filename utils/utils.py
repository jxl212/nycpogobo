import groupy

from groupy import Client
from slackclient import SlackClient

groupme_client = Client.from_token(os.environ.get('GROUPME_TOKEN'))
groupme_client = Client.from_token(os.environ.get('GROUPME_TOKEN'))
groupme_bot=[b for b in groupme_client.bots.list() if b.data['bot_id']=='074f9a78a1efbcf9f0d44e60a5'][0]

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
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
def get_name(msg):
	d=collections.defaultdict(str)
	first_line = str(msg.content).lstrip().split("\n")[0]
	match = re.match(r".*?\*\*(?P<name>\w+)\*\*", first_line)
	if match:
		d=match.groupdict()

	return d['name']

def get_nycpokemap_url(msg):
	match = re.match(r'.*(?P<link>https\://nycpokemap\.com.*?)\s?',msg.content.replace("\n"," "))
	if match and "link" in match.groupdict().keys():
		return match['link']
	return ""

def get_googlmap_url(msg):
	match = re.match(r'.*(?P<link>https\://maps\.google\.com.*?)\s?',msg.content.replace("\n"," "))
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
