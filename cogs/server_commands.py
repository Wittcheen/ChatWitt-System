import interactions

import yaml
with open("./server_ids.yaml") as config_file:
	server_ids = yaml.safe_load(config_file)

NEWS_PING_BUTTON = interactions.Button(
	style = interactions.ButtonStyle.SECONDARY,
	emoji = interactions.PartialEmoji(name = "\U0001F514"),
	label = "News Ping",
	custom_id = "news_ping_button"
)
STREAM_PING_BUTTON = interactions.Button(
	style = interactions.ButtonStyle.SECONDARY,
	emoji = interactions.PartialEmoji(name = "\U0001F3A5"),
	label = "Stream Ping",
	custom_id = "stream_ping_button"
)
BUTTON_ROW = interactions.ActionRow(
	*[NEWS_PING_BUTTON, STREAM_PING_BUTTON]
)

class ServerCommands(interactions.Extension):
	def __init__(self, client):
		self.client: interactions.Client = client

	#region - SSM | PARENT COMMAND
	@interactions.slash_command(name = "ssm", description = "(Send Server Message) - writes the chosen message",
		default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [server_ids["server_id"]])
	@interactions.slash_option(name = "command", description = "choose the server message that it should send", opt_type = interactions.OptionType.STRING, required = True,
		choices = [interactions.SlashCommandChoice(name = "reactroles", value = "reactroles")])
	async def ssm(self, ctx: interactions.SlashContext, command: str):
		if command == "reactroles":
			await ServerCommands.reactroles(self, ctx)
	#endregion

	#region - REACT ROLES COMMAND
	async def reactroles(self, ctx: interactions.SlashContext):
		news_ping = ctx.guild.get_role(server_ids["news_ping_role_id"])
		stream_ping = ctx.guild.get_role(server_ids["stream_ping_role_id"])
		react_roles = interactions.Embed(
			color = int("0x2f3136", 0),
			description = "<:chatwitt:1048944473675137054>  | ChatWitt - React Roles |  <:chatwitt:1048944473675137054>\n\n" +
			"**Reaction Roles**\n\n" +
			f"• {news_ping.mention}\n" +
			'> Press the button "\U0001F514 News Ping" to get notification pings.\n\n'
			f"• {stream_ping.mention}\n" +
			'> Press on the button "\U0001F3A5 Stream Ping" to get stream pings,\n> when Sjippi is live on Twitch.\n\n' +
			"_You can press again, to remove the role from yourself._"
		)
		react_roles.set_footer(text = "ChatWitt | React Roles", icon_url = ctx.guild.icon._url)
		react_roles.set_thumbnail(url = ctx.guild.icon._url)
		await ctx.channel.send(embeds = react_roles, components = BUTTON_ROW)
		message = await ctx.send(content = "Done.", ephemeral = True)
		await ctx.delete(message.id)
	@interactions.component_callback("news_ping_button")
	async def news_ping_button(self, ctx: interactions.ComponentContext):
		if server_ids["news_ping_role_id"] in ctx.author.roles:
			await ctx.author.remove_role(server_ids["news_ping_role_id"])
			await ctx.send('You removed the "News Ping" role from yourself!', ephemeral = True)
		elif server_ids["news_ping_role_id"] not in ctx.author.roles:
			await ctx.author.add_role(server_ids["news_ping_role_id"])
			await ctx.send('You claimed the "News Ping" role.', ephemeral = True)
	@interactions.component_callback("stream_ping_button")
	async def stream_ping_button(self, ctx: interactions.ComponentContext):
		if server_ids["stream_ping_role_id"] in ctx.author.roles:
			await ctx.author.remove_role(server_ids["stream_ping_role_id"])
			await ctx.send('You removed the "Stream Ping" role from yourself!', ephemeral = True)
		elif server_ids["stream_ping_role_id"] not in ctx.author.roles:
			await ctx.author.add_role(server_ids["stream_ping_role_id"])
			await ctx.send('You claimed the "Stream Ping" role.', ephemeral = True)
	#endregion

def setup(client):
	ServerCommands(client)