import interactions

import yaml
with open("./botconfig.yaml") as config_file:
    data = yaml.safe_load(config_file)

RULES_ENG = interactions.Embed(
    color = int("0x2f3136", 0),
    description = "<:chatwitt:1048944473675137054>  | ChatWitt - Rules |  <:chatwitt:1048944473675137054>\n\n" +
    ":flag_us: | **§1 Name and Avatar**\n" +
    "> • 1.1 - Faking other people, especially staff members is forbidden.\n" +
    "> • 1.2 - Racist, perverted or sexist names & avatars are strictly forbidden.\n\n"
    ":flag_us: | **§2 Language usage**\n" +
    "> • 2.1 - Use english when communicating with others, exept in the danish (chat-dk) channel.\n" +
    "> • 2.2 - Threats of any kind are prohibited.\n" +
    "> • 2.3 - Insults, spam or other inappropriate behavior in any form are strictly prohibited.\n\n" +
    ":flag_us: | **§3 General Behavior**\n" +
    "> • 3.1 - The voices of other persons may only be recorded with their consent.\n" +
    "> • 3.2 - Any publication of private data is strictly prohibited.\n" +
    "> • 3.3 - Channel hopping (the constant changing of channels) is forbidden.\n" +
    "> • 3.4 - Taking advantage of tickets is forbidden, e.g. using the ticket without needing it.\n" +
    "> • 3.5 - Report rule-breaking behavior you seen, to any staff member."
)
RULES_DK = interactions.Embed(
    color = int("0x2f3136", 0),
    description = "<:chatwitt:1048944473675137054>  | ChatWitt - Rules |  <:chatwitt:1048944473675137054>\n\n" +
    ":flag_dk: | **§1 Navn og Logo**\n" +
    "> • 1.1 - Det er forbudt at forfalske andre mennesker, især staffs.\n" +
    "> • 1.2 - Racistiske, perverse eller sexistiske navne & logo'er er strengt forbudt.\n\n"
    ":flag_dk: | **§2 Sprogbrug**\n" +
    "> • 2.1 - Brug engelsk når du kommunikerer med andre, undtagen i den danske (chat-dk) kanal.\n" +
    "> • 2.2 - Trusler af enhver art er forbudt.\n" +
    "> • 2.3 - Fornærmelser, spam eller anden upassende adfærd i enhver form er strengt forbudt.\n\n" +
    ":flag_dk: | **§3 Generel Adfærd**\n" +
    "> • 3.1 - Andre personers stemmer må kun optages med deres samtykke.\n" +
    "> • 3.2 - Enhver offentliggørelse af private data er strengt forbudt.\n" +
    "> • 3.3 - Kanalhop (det konstante skift af kanaler) er forbudt.\n" +
    "> • 3.4 - At benytte sig af tickets er forbudt, f.eks. bruge tickets uden brug af det.\n" +
    "> • 3.5 - Rapportér regelbrudsadfærd du har set, til enhver staff."
)

NEWS_PING_BUTTON = interactions.Button(
    style = interactions.ButtonStyle.SECONDARY,
    emoji = interactions.Emoji(name = "\U0001F514"),
    label = "News Ping",
    custom_id = "news_ping_button"
)
STREAM_PING_BUTTON = interactions.Button(
    style = interactions.ButtonStyle.SECONDARY,
    emoji = interactions.Emoji(name = "\U0001F3A5"),
    label = "Stream Ping",
    custom_id = "stream_ping_button"
)
BUTTON_ROW = interactions.ActionRow(
    components = [NEWS_PING_BUTTON, STREAM_PING_BUTTON]
)

class ServerCommands(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    # RULES COMMAND
    @interactions.extension_command(default_member_permissions = interactions.Permissions.ADMINISTRATOR, scope = data["server_id"])
    async def rules(self, ctx: interactions.CommandContext):
        """Posts all the rules into this channel"""
        await ctx.get_channel()
        RULES_ENG.set_footer(text = "ChatWitt | Rules", icon_url = ctx.guild.icon_url)
        RULES_ENG.set_thumbnail(url = ctx.guild.icon_url)
        RULES_DK.set_footer(text = "ChatWitt | Rules", icon_url = ctx.guild.icon_url)
        RULES_DK.set_thumbnail(url = ctx.guild.icon_url)
        await ctx.channel.send(embeds = RULES_DK)
        await ctx.channel.send(embeds = RULES_ENG)
        await ctx.send("The rules was postet into this channel.", ephemeral = True)

    # REACT ROLES COMMAND
    @interactions.extension_command(default_member_permissions = interactions.Permissions.ADMINISTRATOR, scope = data["server_id"])
    async def reactroles(self, ctx: interactions.CommandContext):
        """Returns the react roles message"""
        await ctx.get_channel()
        news_ping = await interactions.get(self.client, interactions.Role, object_id = data["news_ping_role_id"])
        stream_ping = await interactions.get(self.client, interactions.Role, object_id = data["stream_ping_role_id"])
        react_roles = interactions.Embed(
            color = int("0x2f3136", 0),
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - React Roles |  <:chatwitt:1048944473675137054>\n\n" +
            "**Reaction Roles**\n\n" + f"• {news_ping.mention}\n" +
            '> Press the button "\U0001F514 News Ping" to get notification pings.\n\n'
            f"• {stream_ping.mention}\n" +
            '> Press on the button "\U0001F3A5 Stream Ping" to get stream pings,\n> when Sjippi is live on Twitch.\n\n' +
            "_You can press again, to remove the role from yourself._"
        )
        react_roles.set_footer(text = "ChatWitt | React Roles", icon_url = ctx.guild.icon_url)
        react_roles.set_thumbnail(url = ctx.guild.icon_url)
        await ctx.channel.send(embeds = react_roles, components = BUTTON_ROW)
        await ctx.send("Sended the react roles message to this channel.", ephemeral = True)
    @interactions.extension_component("news_ping_button")
    async def news_ping_button(self, ctx: interactions.CommandContext):
        if data["news_ping_role_id"] in ctx.author.roles:
            await ctx.author.remove_role(data["news_ping_role_id"])
            await ctx.send('You removed the "News Ping" role from yourself!', ephemeral = True)
        elif data["news_ping_role_id"] not in ctx.author.roles:
            await ctx.author.add_role(data["news_ping_role_id"])
            await ctx.send('You claimed the "News Ping" role.', ephemeral = True)
    @interactions.extension_component("stream_ping_button")
    async def stream_ping_button(self, ctx: interactions.CommandContext):
        if data["stream_ping_role_id"] in ctx.author.roles:
            await ctx.author.remove_role(data["stream_ping_role_id"])
            await ctx.send('You removed the "Stream Ping" role from yourself!', ephemeral = True)
        elif data["stream_ping_role_id"] not in ctx.author.roles:
            await ctx.author.add_role(data["stream_ping_role_id"])
            await ctx.send('You claimed the "Stream Ping" role.', ephemeral = True)

def setup(client):
    ServerCommands(client)