import interactions

import yaml
with open("./server_ids.yaml") as config_file:
	server_ids = yaml.safe_load(config_file)

TWITCH_MODAL = interactions.Modal(
    custom_id = "twitch_mod_form",
    title = "Mod Application",
    *[
        interactions.InputText(
            style = interactions.TextStyles.SHORT, label = "Twitch and IRL name:", custom_id = "user_name", required = True, min_length = 1, max_length = 100),
        interactions.InputText(
            style = interactions.TextStyles.SHORT, label = "How old are you?", custom_id = "user_age", required = True, min_length = 2, max_length = 2), 
        interactions.InputText(
            style = interactions.TextStyles.PARAGRAPH, label = "Why should YOU be mod, and do you have experience?", custom_id = "user_whyme", required = True, min_length = 100, max_length = 3000), 
        interactions.InputText(
            style = interactions.TextStyles.PARAGRAPH, label = "How long have you been following Sjippi on Twitch?", placeholder = "Optionally add an image as a link", custom_id = "user_follow", required = True, min_length = 10, max_length = 100)
    ])

CLOSE_TICKET_BUTTON = interactions.Button(
	style = interactions.ButtonStyle.SECONDARY, emoji = interactions.PartialEmoji(name = "\U0001F512"), label = "Close this ticket", custom_id = "close_ticket"
)

class Tickets(interactions.Extension):
	def __init__(self, client):
		self.client: interactions.Client = client

	#region - SEND TWITCH MOD APPLICATION MESSAGE
	async def opentickets(self, ctx: interactions.SlashContext):
		tickets_embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - Twitch Mod Application |  <:chatwitt:1048944473675137054>\n\n" + 
            "**Do you want to be mod?**\n\n" +
            "Go down and send an application, why you should be mod.\n" +
            "Fill in the form and remember to be patient with your answer.\n\n" +
            "> _Only send an application if you really want to be mod!_"
        )
		tickets_embed.set_footer(text = "ChatWitt | Twitch Mod Application", icon_url = ctx.guild.icon._url)
		tickets_embed.set_thumbnail(url = ctx.guild.icon._url)
		open_ticket = interactions.Button(
			style = interactions.ButtonStyle.SECONDARY,
			emoji = interactions.PartialEmoji(name = "\U0001F4E9"),
			label = "Click here to begin",
			custom_id = "open_ticket"
		)
		await ctx.channel.send(embeds = tickets_embed, components = open_ticket)
		message = await ctx.send(content = "Done.", ephemeral = True)
		await ctx.delete(message.id)
	#endregion

	#region - TWTICH MOD FORM MODAL
	@interactions.component_callback("open_ticket")
	async def open_ticket(self, ctx: interactions.ComponentContext):
		await ctx.send_modal(modal = TWITCH_MODAL)

	@interactions.modal_callback("twitch_mod_form")
	async def twitch_mod_modal_response(self, ctx: interactions.ModalContext, user_name: str, user_age: str, user_whyme: str, user_follow: str):
		with open("./server_ids.yaml") as config_file:
			server_ids = yaml.safe_load(config_file)
		embed = interactions.Embed(
			description = "<:chatwitt:1048944473675137054>  | ChatWitt - Twitch Mod Application |  <:chatwitt:1048944473675137054>\n\n" +
			f"**{TWITCH_MODAL.title}** - {ctx.author.mention}\n\U00002800" 
		)
		value_list = [user_name, user_age, user_whyme, user_follow]
		for i, comp in enumerate(TWITCH_MODAL.components):
			embed.add_field(name = f"*{comp.label}*", value = value_list[i], inline = False)
		embed.set_footer(text = "ChatWitt | Twitch Mod Application", icon_url = ctx.guild.icon._url)
		if await self.check_if_user_exist(ctx.author_id):
			await ctx.send("You already have a active ticket!", ephemeral = True)
		else:
			createdChannel = await ctx.guild.create_text_channel(category = server_ids["mod_tickets_category_id"], name = f'ticket-{ctx.author.username}',
			permission_overwrites = [interactions.PermissionOverwrite(id = int(ctx.author_id), type = 1, allow = interactions.Permissions.VIEW_CHANNEL),
			interactions.PermissionOverwrite(id = server_ids["everyone_role_id"], type = 0, deny = interactions.Permissions.VIEW_CHANNEL)]
			)
			self.add_user_to_file(ctx.author_id)
			await ctx.send(f"You created a ticket {createdChannel.mention}. An answer will return as fast as possible!", ephemeral = True)
			message = await createdChannel.send(embeds = embed)
			await message.reply(f"{ctx.author.mention}, remember to be patient for your answer, and if you regret your ticket, you can always close it.", components = CLOSE_TICKET_BUTTON)
			new_number = server_ids["ticket_number"] + 1
			server_ids["ticket_number"] = new_number
			with open("./server_ids.yaml", 'w') as config_file:
				yaml.dump(server_ids, config_file)
	#endregion

	#region - CLOSE TICKET BUTTONS
	@interactions.component_callback("close_ticket")
	async def close_ticket(self, ctx: interactions.ComponentContext):
		users_id = ctx.message._mention_ids[1]
		confirm_button = interactions.Button(
			style = interactions.ButtonStyle.SUCCESS, label = "Confirm", custom_id = "confirm_button"
		)
		cancel_button = interactions.Button(
			style = interactions.ButtonStyle.DANGER, label = "Cancel", custom_id = "cancel_button"
		)
		button_row = interactions.ActionRow(
			*[confirm_button, cancel_button]
		)
		await ctx.send(f"Are you sure you wan't to close <@{users_id}>'s ticket?", components = button_row)

	@interactions.component_callback("cancel_button")
	async def cancel_button(self, ctx: interactions.ComponentContext):
		await ctx.message.delete()

	@interactions.component_callback("confirm_button")
	async def confirm_button(self, ctx: interactions.ComponentContext):
		await ctx.send("This ticket is closing!", ephemeral = True)
		users_id = ctx.message._mention_ids[0]
		self.delete_user_from_file(users_id)
		await ctx.channel.delete()
	#endregion

	#region - UPDATE FILE
	def load_users_from_file(self):
		with open("./mod_applications.yaml", 'r') as file:
			users = yaml.safe_load(file)
		return users["user_ids"]

	def add_user_to_file(self, user_id):
		users_list = self.load_users_from_file()
		users_list.append(int(user_id))
		data = {"user_ids": users_list}
		with open("./mod_applications.yaml", 'w') as file:
			yaml.dump(data, file)

	def delete_user_from_file(self, user_id):
		users_list = self.load_users_from_file()
		for user in users_list:
			if user == int(user_id):
				users_list.remove(user)
				data = {"user_ids": users_list}
				with open("./mod_applications.yaml", 'w') as file:
					yaml.dump(data, file)
				return True
		return False
	
	async def check_if_user_exist(self, user_id) -> bool:
		users_list = self.load_users_from_file()
		for user in users_list:
			if user == int(user_id):
				return True
		return False
	#endregion

def setup(client):
	Tickets(client)
