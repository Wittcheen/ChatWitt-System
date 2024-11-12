# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions
import requests, os
from interactions.models.internal.tasks import IntervalTrigger

from utils.yaml_file import server_id, id_map

USER = "Sjippi"

TWITCH_EMBED = interactions.Embed(
    color = int("0x2f3136", 0),
    description = ("<:chatwitt:1048944473675137054>  | ChatWitt - Stream |  <:chatwitt:1048944473675137054>\n\n"
        f"**{USER} er nu live på Twitch!**\n\n"
        "Sving forbi chatten og lad os have det sjovt!\n"
        "_Tryk på knappen for at se med på streamen._"
    )
)

STREAM_LINK_BUTTON = interactions.Button(
    style = interactions.ButtonStyle.LINK,
    label = "Stream Link", url = f"https://twitch.tv/{USER.lower()}"
)

class TwitchNotification(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.listen()
    async def on_startup(self):
        self.check_for_stream.start()
        global streaming
        streaming = False

    #region - TWITCH LIVE COMMAND
    @interactions.slash_command(name = "live", description = "sends out a stream notification",
        default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [server_id])
    async def live(self, ctx: interactions.SlashContext):
        await self.live_func()
        msg = await ctx.send(content = "_The stream notification has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

    #region - TWITCH LIVE FUNCTION
    async def live_func(self):
        channel = self.client.get_channel(id_map["streams_channel"])
        stream_ping = channel.guild.get_role(id_map["stream_ping_role"])
        TWITCH_EMBED.set_footer(text = "ChatWitt | Stream", icon_url = channel.guild.icon._url)
        TWITCH_EMBED.set_thumbnail(url = "https://static-cdn.jtvnw.net/jtv_user_pictures/a4d59e77-754a-4ed7-981a-62b5534f223b-profile_image-300x300.png")
        await channel.send(f"||{stream_ping.mention}||", embeds = TWITCH_EMBED, components = STREAM_LINK_BUTTON)
    #endregion

    #region - GET TWITCH OAUTH TOKEN API REQUEST
    def __get_twitch_oauth_token(self):
        token_url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": os.getenv("twitch_client_id"),
            "client_secret": os.getenv("twitch_client_secret"),
            "grant_type": "client_credentials"
        }
        try:
            response = requests.post(token_url, params = params)
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("access_token")
        except requests.exceptions.RequestException as e:
            print(f"Error getting Twitch data: {e}")
            return None
    #endregion

    #region - GET TWITCH USER LIVE API REQUEST
    def __get_twitch_user_live(self, username, token) -> bool:
        base_url = "https://api.twitch.tv/helix/streams"
        headers = {
            "Client-ID": os.getenv("twitch_client_id"),
            "Authorization": f"Bearer {token}",
        }
        params = { "user_login": username }
        try:
            response = requests.get(base_url, headers = headers, params = params)
            response_data = response.json()
            if "data" in response_data and len(response_data["data"]) > 0:
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error getting Twitch data: {e}")
            return False
    #endregion

    #region - CHECK TWITCH USER IS LIVE EVENT
    @interactions.Task.create(IntervalTrigger(minutes = 3))
    async def check_for_stream(self):
        token = self.__get_twitch_oauth_token()
        if token:
            is_live = self.__get_twitch_user_live(USER.lower(), token)
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
    TwitchNotification(client)