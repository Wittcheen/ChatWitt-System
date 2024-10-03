# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions
from utils.trie import Trie

import yaml
with open("./yaml/id_map.yaml") as config_file:
    id_map = yaml.safe_load(config_file)

INVITE_LINK = "https://discord.gg/GJyyjrurHj"

RULES_DANISH = interactions.Embed(
    color = int("0x2f3136", 0),
    description = ("<:chatwitt:1048944473675137054>  | ChatWitt - Rules |  <:chatwitt:1048944473675137054>\n\n"
        ":flag_dk: | **§1 Profil**\n"
        "> • 1.1 - Det er forbudt at forfalske identiteter, især staffs.\n"
        "> • 1.2 - Racistiske og perverse navne & logoer er ikke tilladt.\n"
        "> • 1.3 - Undgåelse af sin straf med en anden konto er forbudt.\n\n"
        ":flag_dk: | **§2 Sprogbrug**\n"
        "> • 2.1 - Alt kommunikation skal være PG-13, for et sikrer miljø.\n"
        "> • 2.2 - Trusler og chikane af enhver art er strengt forbudt.\n"
        "> • 2.3 - Fornærmelser, spam og upassende adfærd er forbudt.\n\n"
        ":flag_dk: | **§3 Generel Adfærd**\n"
        "> • 3.1 - Offentliggørelse af private data er strengt forbudt.\n"
        "> • 3.2 - Rapportér regelbrudsadfærd til enhver staff.\n"
        "> • 3.3 - Brug de relevante kanaler og hold dig til emnet.\n"
        "> • 3.4 - At lave bevidst forstyrrende støj er ikke tilladt.\n"
        "> • 3.5 - Reklamering i enhver form er strengt forbudt."
    )
)

PING_BUTTONS = interactions.ActionRow(
    *[interactions.Button(
        custom_id = "ping_button", style = interactions.ButtonStyle.SECONDARY,
        emoji = interactions.PartialEmoji(name = "\U0001F514"), label = "Ping"
    ),interactions.Button(
        custom_id = "stream_ping_button", style = interactions.ButtonStyle.SECONDARY,
        emoji = interactions.PartialEmoji(name = "\U0001F3A5"), label = "Stream Ping"
    )]
)

class ServerMessages(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

        self._messages = {
            "welcome": self.welcome,
            "rules": self.rules,
            "roles": self.roles
        }
        self.trie = Trie()
        for name in self._messages:
            self.trie.insert(name)

    #region - SSM (Send Server Message) COMMAND
    @interactions.slash_command(name = "ssm", description = "(Send Server Message) - send a server message",
        default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [id_map["server"]])
    @interactions.slash_option(name = "cmd", description = "choose the server message", opt_type = interactions.OptionType.STRING,
        required = True, autocomplete = True)
    async def ssm(self, ctx: interactions.SlashContext, cmd: str):
        handler = self._messages[cmd]
        if callable(handler):
            await handler(ctx)
        else:
            await ctx.send("Command is not callable!", ephemeral = True)

    @ssm.autocomplete("cmd")
    async def __ssm_autocomplete(self, ctx: interactions.AutocompleteContext):
        input = ctx.input_text or ""
        if not input:
            await ctx.send(choices = [
                {"name": name, "value": name} for name in self._messages
            ])
            return
        # Search the Trie for command names matching the user's input
        match = self.trie.search(input.lower())
        limit = min(25, len(self._messages), len(match))
        await ctx.send(choices = [
            {"name": name, "value": name} for name in match[:limit]
        ])
    #endregion

    #region - WELCOME COMMAND
    async def welcome(self, ctx: interactions.SlashContext):
        channel_keys = ["rules_channel", "announcement_channel", "roles_channel", "chat_channel", "mod_tickets_channel"]
        channels = { key: ctx.guild.get_channel(id_map[key]) for key in channel_keys if id_map[key] }
        await ctx.channel.send(content = ("# Velkommen til ChatWitt!\n\n"
            "Her kan du finde diverse kanaler med information og nyheder, samt kommunikere med andre medlemmer og staffs.\n"
            "Se her for at få en detaljeret oversigt over de forskellige kanaler og deres formål:\n\n"
            f"> {channels['rules_channel'].mention} Læs alle vores regler.\n"
            f"> {channels['announcement_channel'].mention} Se de seneste nyheder.\n"
            f"> {channels['roles_channel'].mention} Giv dig selv pings roller.\n> \n"
            f"> {channels['chat_channel'].mention} Skriv med andre medlemmer om hvad som helst.\n"
            f"> {channels['mod_tickets_channel'].mention} Ansøg om mod på streamen.\n\n"
            f"Discord invite link: {INVITE_LINK}"))
        msg = await ctx.send(content = "_The welcome message has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

    #region - RULES COMMAND
    async def rules(self, ctx: interactions.SlashContext):
        RULES_DANISH.set_footer(text = "ChatWitt | Rules", icon_url = ctx.guild.icon._url)
        await ctx.channel.send(embeds = RULES_DANISH)
        msg = await ctx.send(content = "_The rules has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

    #region - ROLES COMMAND MESSAGE
    async def roles(self, ctx: interactions.SlashContext):
        role_keys = ["ping_role", "stream_ping_role"]
        roles = { key: ctx.guild.get_role(id_map[key]) for key in role_keys }
        embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = ("<:chatwitt:1048944473675137054>  | ChatWitt - Roles |  <:chatwitt:1048944473675137054>\n\n"
            f"• {roles['ping_role'].mention}\n"
            '> Tryk på knappen "\U0001F514 Ping" for at få notifikations pings.\n\n'
            f"• {roles['stream_ping_role'].mention}\n"
            '> Brug knappen "\U0001F3A5 Stream Ping" for at få livestream\n> notifikationer, når Sjippi sender live på Twitch.\n\n'
            "_Du kan altid trykke igen, for at fjerne rollen fra dig selv._"
        ))
        embed.set_footer(text = "ChatWitt | Roles", icon_url = ctx.guild.icon._url)
        await ctx.channel.send(embeds = embed, components = PING_BUTTONS)
        msg = await ctx.send(content = "_The roles embed has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    @interactions.component_callback("ping_button")
    async def __ping_button(self, ctx: interactions.ComponentContext):
        if id_map["ping_role"] in ctx.author.roles:
            await ctx.author.remove_role(id_map["ping_role"])
            await ctx.send('Du fjernede "Ping" rollen fra dig selv!', ephemeral = True)
        elif id_map["ping_role"] not in ctx.author.roles:
            await ctx.author.add_role(id_map["ping_role"])
            await ctx.send('Du fik rollen "Ping".', ephemeral = True)
    @interactions.component_callback("stream_ping_button")
    async def __stream_ping_button(self, ctx: interactions.ComponentContext):
        if id_map["stream_ping_role"] in ctx.author.roles:
            await ctx.author.remove_role(id_map["stream_ping_role"])
            await ctx.send('Du fjernede "Stream Ping" rollen fra dig selv!', ephemeral = True)
        elif id_map["stream_ping_role"] not in ctx.author.roles:
            await ctx.author.add_role(id_map["stream_ping_role"])
            await ctx.send('Du fik rollen "Stream Ping".', ephemeral = True)
    #endregion

def setup(client):
    ServerMessages(client)