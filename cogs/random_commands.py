import interactions

import yaml
with open("./botconfig.yaml") as config_file:
    data = yaml.safe_load(config_file)

NEWS_MODAL = interactions.Modal(
    custom_id = "news_form",
    title = "Create a new announcement",
    components = [
        interactions.TextInput(style = interactions.TextStyleType.SHORT, label = "Title", custom_id = "news_title", required = True, min_length = 1, max_length = 100),
        interactions.TextInput(style = interactions.TextStyleType.PARAGRAPH, label = "Message", custom_id = "news_message", required = True, min_length = 1, max_length = 3500)
    ])
SAY_MODAL = interactions.Modal(
    custom_id = "say_form",
    title = "Send a message as the bot",
    components = [
        interactions.TextInput(style = interactions.TextStyleType.PARAGRAPH, label = "What should the bot say?", custom_id = "say_message", required = True, min_length = 1, max_length = 3500)
    ])

TWITCH_EMBED = interactions.Embed(
    color = int("0x2f3136", 0),
    description = "<:chatwitt:1048944473675137054>  | ChatWitt - Stream |  <:chatwitt:1048944473675137054>\n\n" +
    "**Sjippi is now live on Twitch!**\n\n" + f"Follow the [link](https://twitch.tv/sjippi) to watch the stream.\n" +
    "Would appreciate if you gave it a try."
)

class RandomCommands(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    # NEWS COMMAND
    @interactions.extension_command(default_member_permissions = interactions.Permissions.ADMINISTRATOR, scope = data["server_id"])
    async def news(self, ctx: interactions.CommandContext):
        """Get the bot to sent the news"""
        await ctx.popup(NEWS_MODAL)
    @interactions.extension_modal("news_form")
    async def news_modal_response(self, ctx: interactions.CommandContext, news_title: str, news_message: str):
        await ctx.get_channel()
        news_ping = await interactions.get(self.client, interactions.Role, object_id = data["news_ping_role_id"])
        embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - News |  <:chatwitt:1048944473675137054>\n\n" +
            f"**{news_title}**\n\n" + f"{news_message}"
        )
        embed.set_footer(text = "ChatWitt | News", icon_url = ctx.guild.icon_url)
        await ctx.channel.send(f"||{news_ping.mention}||", embeds = embed)
        await ctx.send("Successfully send out the news to this channel.", ephemeral = True)

    # TWITCH LIVE COMMAND
    @interactions.extension_command(default_member_permissions = interactions.Permissions.KICK_MEMBERS, scope = data["server_id"])
    async def live(self, ctx: interactions.CommandContext):
        """Sends a twitch livestream notification"""
        await ctx.get_channel()
        stream_ping = await interactions.get(self.client, interactions.Role, object_id = data["stream_ping_role_id"])
        TWITCH_EMBED.set_footer(text = "ChatWitt | Stream", icon_url = ctx.guild.icon_url)
        TWITCH_EMBED.set_thumbnail(url = "https://static-cdn.jtvnw.net/jtv_user_pictures/6889a7f4-17b0-4b70-85b9-4e911a1043ae-profile_image-300x300.png")
        await ctx.channel.send(f"||{stream_ping.mention}||", embeds = TWITCH_EMBED)
        await ctx.send("A twitch livestream notification was send to this channel.", ephemeral = True)

    # SAY COMMAND
    @interactions.extension_command(default_member_permissions = interactions.Permissions.ADMINISTRATOR, scope = data["server_id"])
    async def say(self, ctx: interactions.CommandContext):
        """Get the bot to say something"""
        await ctx.popup(SAY_MODAL)
    @interactions.extension_modal("say_form")
    async def say_modal_response(self, ctx: interactions.CommandContext, say_message: str):
        await ctx.send("Sending a message from the bot..", ephemeral = True)
        await ctx.get_channel()
        await ctx.channel.send(say_message)

    # CLEAR COMMAND
    @interactions.extension_command(default_member_permissions = interactions.Permissions.MANAGE_MESSAGES, scope = data["server_id"])
    @interactions.option(description = "Write the amount to delete")
    async def clear(self, ctx: interactions.CommandContext, number: int = 1):
        """Clears the amount of messages"""
        channel = await ctx.get_channel()
        await channel.purge(amount = number)
        await ctx.send(f"Deleted {number} message(s) from this channel!", ephemeral=True)

def setup(client):
    RandomCommands(client)