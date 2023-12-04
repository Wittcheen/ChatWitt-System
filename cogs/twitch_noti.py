import interactions
import requests
from interactions.models.internal.tasks import IntervalTrigger

import yaml, os
with open("./server_ids.yaml") as config_file:
	server_ids = yaml.safe_load(config_file)

TWITCH_EMBED = interactions.Embed(
    color = int("0x2f3136", 0),
    description = "<:chatwitt:1048944473675137054>  | ChatWitt - Stream |  <:chatwitt:1048944473675137054>\n\n" +
    "**Sjippi is now live on Twitch!**\n\n" + f"Follow the [link](https://twitch.tv/sjippi) to watch the stream.\n" +
    "Would appreciate if you gave it a chance."
)

USER = "Sjippi"

class TwitchNoti(interactions.Extension):
	def __init__(self, client):
		self.client: interactions.Client = client

	@interactions.listen()
	async def on_startup(self):
		self.check_for_stream.start()
		global streaming
		streaming = False

	#region - TWITCH LIVE FUNCTION
	async def live_func(self):
		channel = self.client.get_channel(channel_id = server_ids["streams_channel_id"])
		stream_ping = channel.guild.get_role(server_ids["stream_ping_role_id"])
		TWITCH_EMBED.set_footer(text = "ChatWitt | Stream", icon_url = channel.guild.icon._url)
		TWITCH_EMBED.set_thumbnail(url = "https://static-cdn.jtvnw.net/jtv_user_pictures/6889a7f4-17b0-4b70-85b9-4e911a1043ae-profile_image-300x300.png")
		await channel.send(f"||{stream_ping.mention}||", embeds = TWITCH_EMBED)
	#endregion

	#region - GET TWITCH OAUTH TOKEN API REQUEST
	def get_twitch_oauth_token(self):
		token_url = "https://id.twitch.tv/oauth2/token"
		params = {
			"client_id": os.getenv('twitch_client_id'),
			"client_secret": os.getenv('twitch_client_secret'),
			"grant_type": "client_credentials"
		}
		try:
			response = requests.post(token_url, params=params)
			response.raise_for_status()
			response_data = response.json()
			return response_data.get('access_token')
		except requests.exceptions.RequestException as e:
			print(f"Error getting Twitch data: {e}")
			return None
	#endregion

	#region - GET TWITCH USER LIVE API REQUEST
	def get_twitch_user_live(self, username, token) -> bool:
		base_url = "https://api.twitch.tv/helix/streams"
		headers = {
			"Client-ID": os.getenv('twitch_client_id'),
			"Authorization": f'Bearer {token}',
		}
		params = {
			"user_login": username
		}
		try:
			response = requests.get(base_url, headers = headers, params = params)
			response_data = response.json()
			if "data" in response_data and len(response_data["data"]) > 0:
				# print(response_data)
				return True
			else:
				return False
		except requests.exceptions.RequestException as e:
			print(f"Error getting Twitch data: {e}")
			return False
	#endregion

	#region - CHECK TWITCH USER IS LIVE EVENT
	@interactions.Task.create(IntervalTrigger(minutes = 1))
	async def check_for_stream(self):
		token = self.get_twitch_oauth_token()
		if token:
			is_live = self.get_twitch_user_live(USER.lower(), token)
			global streaming
			if is_live and not streaming:
				await self.live_func()
				streaming = True
			elif not is_live and streaming:
				streaming = False
		else:
			print("Failed to get the OAuth2 token.")
	#endregion

def setup(client):
	TwitchNoti(client)