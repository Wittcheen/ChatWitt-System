import interactions

import yaml
with open("./server_ids.yaml") as config_file:
	server_ids = yaml.safe_load(config_file)

NEWS_MODAL = interactions.Modal(
	custom_id = "news_form",
	title = "Create a new announcement",
	*[
		interactions.InputText(style = interactions.TextStyles.SHORT, label = "Title", custom_id = "news_title", required = True, min_length = 1, max_length = 100),
		interactions.InputText(style = interactions.TextStyles.PARAGRAPH, label = "Message", custom_id = "news_message", required = True, min_length = 1, max_length = 3500)
	])
SAY_MODAL = interactions.Modal(
	custom_id = "say_form",
	title = "Send a message from the bot",
	*[
		interactions.InputText(style = interactions.TextStyles.PARAGRAPH, label = "What should the bot say?", custom_id = "say_message", required = True, min_length = 1, max_length = 3500)
	])

class RandomCommands(interactions.Extension):
	def __init__(self, client):
		self.client: interactions.Client = client

	#region - NEWS COMMAND
	async def news(self, ctx: interactions.SlashContext):
		await ctx.send_modal(modal = NEWS_MODAL)
	@interactions.modal_callback("news_form")
	async def news_modal_response(self, ctx: interactions.ModalContext, news_title: str, news_message: str):
		news_ping = ctx.guild.get_role(server_ids["news_ping_role_id"])
		embed = interactions.Embed(
			color = int("0x2f3136", 0),
			description = "<:chatwitt:1048944473675137054>  | ChatWitt - News |  <:chatwitt:1048944473675137054>\n\n" +
			f"**{news_title}**\n\n" + f"{news_message}"
		)
		embed.set_footer(text = "ChatWitt | News", icon_url = ctx.guild.icon._url)
		await ctx.channel.send(f"||{news_ping.mention}||", embeds = embed)
		message = await ctx.send(content = "Done.", ephemeral = True)
		await ctx.delete(message.id)
	#endregion

	#region - SAY COMMAND
	async def say(self, ctx: interactions.SlashContext):
		await ctx.send_modal(modal = SAY_MODAL)
	@interactions.modal_callback("say_form")
	async def say_modal_response(self, ctx: interactions.ModalContext, say_message: str):
		await ctx.channel.send(content = say_message)
		message = await ctx.send(content = "Done.", ephemeral = True)
		await ctx.delete(message.id)
	#endregion

	#region - CLEAR COMMAND
	@interactions.slash_command(name = "clear", description = "deletes the amount of messages",
		default_member_permissions = interactions.Permissions.MANAGE_MESSAGES, scopes = [server_ids["server_id"]])
	@interactions.slash_option(name = "amount", description = "write the amount to delete", opt_type = interactions.OptionType.INTEGER)
	async def clear(self, ctx: interactions.SlashContext, amount: int = 1):
		await ctx.channel.purge(deletion_limit = amount)
		message = await ctx.send(content = f"Deleted {amount} message(s) from this channel!", ephemeral = True)
		await ctx.delete(message.id)
	#endregion

def setup(client):
	RandomCommands(client)