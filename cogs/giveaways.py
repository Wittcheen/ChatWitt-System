from dataclasses import dataclass
import interactions
import datetime, time
from cogs.database import Database
import asyncio

import yaml
with open("./server_ids.yaml") as config_file:
	server_ids = yaml.safe_load(config_file)

@dataclass
class Giveaway:
	prize: str
	timestamp: int
	author: int
	channel_id: int
	entries: int
	user_entries: list[int]
	winners_count: int
	winners: list[int]

GIVEAWAYS: dict[int, Giveaway] = {}

GIVEAWAY_MODAL = interactions.Modal(
	custom_id = "modal_giveaway",
	title = "Create a giveaway",
	*[
		interactions.InputText(style = interactions.TextStyles.SHORT, label = "Duration", custom_id = "ga_duration", placeholder = "Ex: 10m", required = True, min_length = 2, max_length = 100),
		interactions.InputText(style = interactions.TextStyles.SHORT, label = "Count of winners", custom_id = "ga_winners", value = "1", required = True, min_length = 1, max_length = 2),
		interactions.InputText(style = interactions.TextStyles.SHORT, label = "Prize", custom_id = "ga_prize", required = True, min_length = 1, max_length = 128)
	])

GIVEAWAY_BUTTON = interactions.Button(
	style = interactions.ButtonStyle.PRIMARY,
	emoji = interactions.PartialEmoji(name = "\U0001F389"),
	custom_id = "join_giveaway"
)

class Giveaways(interactions.Extension):
	def __init__(self, client):
		self.client: interactions.Client = client

	#region - CONTINUE GIVEAWAYS ON STARTUP
	@interactions.listen()
	async def on_startup(self):
		await Database.create_pool()
		rows = await Database.get_all_giveaways()
		for row in rows:
			giveaway = Giveaway(prize = row["prize"], timestamp = row["timestamp"], author = row["author"], channel_id = row["channel_id"], entries = row["entries"], user_entries = [], winners_count = row["winners"], winners = [])
			users = await Database.get_all_entries(message_id = row["id"])
			for user in users:
				giveaway.user_entries.append(user)
			GIVEAWAYS[int(row["id"])] = giveaway
			asyncio.create_task(self.giveaway_timer(timestamp = row["timestamp"], message_id = row["id"]))
	#endregion

	#region - GIVEAWAY - PARENT COMMAND
	@interactions.slash_command(name = "giveaway", description = "start, end and delete giveaways",
		default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [server_ids["server_id"]])
	@interactions.slash_option(name = "command", description = "choose the command to use", opt_type = interactions.OptionType.STRING, required = True,
		choices = [interactions.SlashCommandChoice(name = "create", value = "create"), interactions.SlashCommandChoice(name = "end", value = "end"), 
				interactions.SlashCommandChoice(name = "reroll", value = "reroll"), interactions.SlashCommandChoice(name = "delete", value = "delete")])
	async def ssm(self, ctx: interactions.SlashContext, command: str):
		if command == "create":
			await ctx.send_modal(modal = GIVEAWAY_MODAL)
		if command == "end":
			await self.end(ctx)
		if command == "reroll":
			await self.reroll(ctx)
		if command == "delete":
			await self.delete(ctx)
	#endregion

	#region - GIVEAWAY CREATE COMMAND
	@interactions.modal_callback("modal_giveaway")
	async def modal_giveaway(self, ctx: interactions.ModalContext, ga_duration: str, ga_winners: str, ga_prize: str):
		unix_timestamp = self.get_timestamp(ga_duration)
		giveaway = Giveaway(prize = ga_prize, timestamp = unix_timestamp, author = ctx.author.id, channel_id = ctx.channel.id, entries = 0, user_entries = [], winners_count = ga_winners, winners = [])
		ga_embed = self.create_giveaway_embed(giveaway)
		ga_embed.set_footer(text = "ChatWitt | Giveaways", icon_url = ctx.guild.icon._url)
		ga_message = await ctx.channel.send(embeds = ga_embed, components = GIVEAWAY_BUTTON)
		GIVEAWAYS[int(ga_message.id)] = giveaway
		asyncio.create_task(self.giveaway_timer(timestamp = unix_timestamp, message_id = ga_message))
		data = {"id": ga_message.id, "prize": giveaway.prize, "timestamp": giveaway.timestamp, "author": giveaway.author, "channel_id": giveaway.channel_id, "entries": giveaway.entries, "winners": giveaway.winners_count, "active": 1}
		pool = await Database.get_global_pool()
		if pool._closed:
			await Database.create_pool()
		await Database.create_entries_table(message_id = ga_message.id)
		await Database.insert_row(table_name = "giveaways", data = data)
		message = await ctx.send(content = "Done.", ephemeral = True)
		await ctx.delete(message.id)
	#endregion

	#region - CREATE GIVEAWAY EMBED
	def create_giveaway_embed(self, giveaway: Giveaway) -> interactions.Embed:
		if len(giveaway.winners) == 0:
			embed = interactions.Embed(
				color = int("0x2f3136", 0),
				description = "<:ChatWitt:1048944473675137054>  | ChatWitt - Giveaways |  <:ChatWitt:1048944473675137054>\n\n" +
				f"**{giveaway.prize}**\n\n" +
				f"Ends: <t:{giveaway.timestamp}:R> <t:{giveaway.timestamp}>\n" +
				f"Created by: <@{giveaway.author}>\n" +
				f"Entries: **{giveaway.entries}**\n" +
				f"Winners: **{giveaway.winners_count}**"
			)
			return embed
		if giveaway.winners[0] == "None":
			embed = interactions.Embed(
				color = int("0x2f3136", 0),
				description = "<:ChatWitt:1048944473675137054>  | ChatWitt - Giveaways |  <:ChatWitt:1048944473675137054>\n\n" +
				f"**{giveaway.prize}**\n\n" +
				f"Ended: <t:{giveaway.timestamp}:R> <t:{giveaway.timestamp}>\n" +
				f"Created by: <@{giveaway.author}>\n" +
				f"Entries: **{giveaway.entries}**\n" +
				f"Winners: Nobody."
			)
			return embed
		else:
			winners = []
			for i in giveaway.winners:
				winners.append(f'<@{i}>')
			winners_string = " ".join(winners)
			embed = interactions.Embed(
				color = int("0x2f3136", 0),
				description = "<:ChatWitt:1048944473675137054>  | ChatWitt - Giveaways |  <:ChatWitt:1048944473675137054>\n\n" +
				f"**{giveaway.prize}**\n\n" +
				f"Ended: <t:{giveaway.timestamp}:R> <t:{giveaway.timestamp}>\n" +
				f"Created by: <@{giveaway.author}>\n" +
				f"Entries: **{giveaway.entries}**\n" +
				f"Winners: {winners_string}"
			)
			return embed
	#endregion

	#region - JOIN GIVEAWAY EVENT
	@interactions.component_callback("join_giveaway")
	async def join_giveaway(self, ctx: interactions.ComponentContext):
		if GIVEAWAYS.get(ctx.message.id):
			giveaway = GIVEAWAYS.get(ctx.message.id)
			if ctx.author.id in giveaway.user_entries:
				leave_button = interactions.Button(
					style = interactions.ButtonStyle.DANGER,
					label = "Leave the giveaway",
					custom_id = "leave_giveaway"
				)
				await ctx.send(content = f"You're already in this giveaway!  {ctx.message.jump_url}", components = leave_button, ephemeral = True)
			else:
				GIVEAWAYS[ctx.message.id].entries += 1
				GIVEAWAYS[ctx.message.id].user_entries.append(ctx.author.id)
				data = {"id": ctx.author.id, "user_name": ctx.author.display_name}
				pool = await Database.get_global_pool()
				if pool._closed:
					await Database.create_pool()
				await Database.insert_row(table_name = f"g{ctx.message.id}", data = data)
				await Database.update_entries(message_id = ctx.message.id)
				ga_embed = self.create_giveaway_embed(giveaway)
				ga_embed.set_footer(text = "ChatWitt | Giveaways", icon_url = ctx.guild.icon._url)
				await ctx.edit_origin(embeds = ga_embed, components = GIVEAWAY_BUTTON)
		else:
			await ctx.send(content = "This is an old giveaway", ephemeral = True)
	#endregion

	#region - LEAVE GIVEAWAY EVENT
	@interactions.component_callback("leave_giveaway")
	async def leave_giveaway(self, ctx: interactions.ComponentContext):
		message_id = ctx.message.content.split("/")[-1]
		if GIVEAWAYS.get(int(message_id)):
			giveaway = GIVEAWAYS.get(int(message_id))
			if ctx.author.id in giveaway.user_entries:
				GIVEAWAYS[int(message_id)].entries -= 1
				GIVEAWAYS[int(message_id)].user_entries.remove(ctx.author.id)
				pool = await Database.get_global_pool()
				if pool._closed:
					await Database.create_pool()
				await Database.delete_row(table_name = f"g{int(message_id)}", message_id = ctx.author.id)
				await Database.update_entries(message_id = int(message_id))
				ga_embed = self.create_giveaway_embed(giveaway)
				ga_embed.set_footer(text = "ChatWitt | Giveaways", icon_url = ctx.guild.icon._url)
				message = await ctx.channel.fetch_message(message_id = int(message_id))
				await message.edit(embeds = ga_embed, components = GIVEAWAY_BUTTON)
				await ctx.edit_origin(content = "You leaved this giveaway!", components = [])
			else:
				await ctx.send(content = "You aren't in this giveaway", ephemeral = True)    
		else:
			await ctx.send(content = "This is an old giveaway", ephemeral = True)
	#endregion

	#region - END GIVEAWAY COMMAND
	async def end(self, ctx: interactions.SlashContext):
		dict_values = list(GIVEAWAYS.values())
		if len(dict_values) == 0:
			await ctx.send(content = "No giveaways are running", ephemeral = True)
		else:
			select_menu = interactions.StringSelectMenu(
				custom_id = "select_ga_end",
				*[interactions.StringSelectOption(
					label = dict_values[i].prize, value = id
				) for i, id in enumerate(GIVEAWAYS)],
				placeholder = "Choose a giveaway"
			)
			await ctx.send(components = select_menu, ephemeral = True)
	#endregion

	#region - END SELECT CALLBACK
	@interactions.component_callback("select_ga_end")
	async def select_ga_end(self, ctx: interactions.ComponentContext):
			await ctx.edit_origin(content = f"Ended the giveaway: {ctx.values[0]}", components = [])
			await self.end_giveaway(value = ctx.values[0])
	#endregion

	#region - END FUNCTION
	async def end_giveaway(self, value: str):
		if GIVEAWAYS.get(int(value)):
			giveaway = GIVEAWAYS.get(int(value))
			unix_timestamp = int(time.time())
			GIVEAWAYS[int(value)].timestamp = unix_timestamp
			channel = self.client.get_channel(channel_id = giveaway.channel_id)
			pool = await Database.get_global_pool()
			if pool._closed:
				await Database.create_pool()
			giveaway.winners = await Database.random_user(message_id = int(value), limit = giveaway.winners_count)
			for winners in giveaway.winners:
				await Database.delete_row(table_name = f"g{int(value)}", message_id = winners)
			if len(giveaway.winners) == 0:
				giveaway.winners.append("None")
			await Database.update_giveaway_inactive(message_id = int(value))
			ga_embed = self.create_giveaway_embed(giveaway)
			ga_embed.set_footer(text = "ChatWitt | Giveaways", icon_url = channel.guild.icon._url)
			message = await channel.fetch_message(message_id = int(value))
			await message.edit(embeds = ga_embed, components = [])
			if giveaway.winners[0] == "None":
				await message.reply(content = f"No entries, so no one won this giveaway!")
			else:
				winners = []
				for i in giveaway.winners:
					winners.append(f'<@{i}>')
				winners_string = " ".join(winners)
				await message.reply(content = f"Congratulations {winners_string}! You won **{giveaway.prize}**!")
	#endregion

	#region - REROLL GIVEAWAY COMMAND
	async def reroll(self, ctx: interactions.SlashContext):
		dict_values = list(GIVEAWAYS.values())
		if len(dict_values) == 0:
			await ctx.send(content = "No giveaway data", ephemeral = True)
		else:
			select_menu = interactions.StringSelectMenu(
				custom_id = "select_ga_reroll",
				*[interactions.StringSelectOption(
					label = dict_values[i].prize, value = id
				) for i, id in enumerate(GIVEAWAYS)],
				placeholder = "Choose a giveaway"
			)
			select_menu_count = interactions.StringSelectMenu(
				custom_id = "select_ga_count",
				*[interactions.StringSelectOption(
					label = i+1, value = i+1
				) for i in range(10)],
				placeholder = "Choose count of reroll"
			)
			action_row = interactions.ActionRow.split_components(*[select_menu, select_menu_count], count_per_row = 1)
			await ctx.send(components = action_row, ephemeral = True)
	#endregion
	
	#region - REROLL SELECT CALLBACKS
	@interactions.component_callback("select_ga_reroll")
	async def select_ga_reroll(self, ctx: interactions.ComponentContext):
		if "reroll_var" in globals():
			message = await ctx.send(content = f'You choose "{ctx.values[0]}"', ephemeral = True)
			await ctx.delete(message.id)
			await self.reroll_func(ctx.values[0])
			await ctx.delete(ctx.message.id)
		else:
			global reroll_var
			reroll_var = ctx.values[0]
			message = await ctx.send(content = f'You choose "{ctx.values[0]}"', ephemeral = True)
			await ctx.delete(message.id)

	@interactions.component_callback("select_ga_count")
	async def select_ga_count(self, ctx: interactions.ComponentContext):
		if "reroll_var" in globals():
			message = await ctx.send(content = f'You choose "{ctx.values[0]}"', ephemeral = True)
			await ctx.delete(message.id)
			await self.reroll_func(ctx.values[0])
			await ctx.delete(ctx.message.id)
		else:
			global reroll_var
			reroll_var = ctx.values[0]
			message = await ctx.send(content = f'You choose "{ctx.values[0]}"', ephemeral = True)
			await ctx.delete(message.id)
	#endregion

	#region - DELETE GLOBAL VARIABLE
	async def del_var(self):
		if "reroll_var" in globals():
			global reroll_var
			del reroll_var
	#endregion

	#region - REROLL FUNCTION
	async def reroll_func(self, value: str):
		if len(reroll_var) > 2:
			if GIVEAWAYS.get(int(reroll_var)):
				giveaway = GIVEAWAYS.get(int(reroll_var))
				giveaway.winners = []
				channel = self.client.get_channel(channel_id = giveaway.channel_id)
				pool = await Database.get_global_pool()
				if pool._closed:
					await Database.create_pool()
				giveaway.winners = await Database.random_user(message_id = int(reroll_var), limit = value)
				for winners in giveaway.winners:
					await Database.delete_row(table_name = f"g{int(reroll_var)}", message_id = winners)
				if len(giveaway.winners) == 0:
					giveaway.winners.append("None")
				message = await channel.fetch_message(message_id = int(reroll_var))
				if giveaway.winners[0] == "None":
					await message.reply(content = f"No more entries, so no one won reroll!")
				else:
					winners = []
					for i in giveaway.winners:
						winners.append(f'<@{i}>')
					winners_string = " ".join(winners)
					await message.reply(content = f"Congratulations {winners_string}! You won **{giveaway.prize}**!")
		else:
			if GIVEAWAYS.get(int(value)):
				giveaway = GIVEAWAYS.get(int(value))
				giveaway.winners = []
				channel = self.client.get_channel(channel_id = giveaway.channel_id)
				pool = await Database.get_global_pool()
				if pool._closed:
					await Database.create_pool()
				giveaway.winners = await Database.random_user(message_id = int(value), limit = reroll_var)
				for winners in giveaway.winners:
					await Database.delete_row(table_name = f"g{int(value)}", message_id = winners)
				if len(giveaway.winners) == 0:
					giveaway.winners.append("None")
				message = await channel.fetch_message(message_id = int(value))
				if giveaway.winners[0] == "None":
					await message.reply(content = f"No more entries, so no one won reroll!")
				else:
					winners = []
					for i in giveaway.winners:
						winners.append(f'<@{i}>')
					winners_string = " ".join(winners)
					await message.reply(content = f"Congratulations {winners_string}! You won **{giveaway.prize}**!")
		await self.del_var()
	#endregion
	
	#region - DELETE GIVEAWAY COMMAND
	async def delete(self, ctx: interactions.SlashContext):
		dict_values = list(GIVEAWAYS.values())
		if len(dict_values) == 0:
			await ctx.send(content = "No giveaway data", ephemeral = True)
		else:
			select_menu = interactions.StringSelectMenu(
				custom_id = "select_ga_delete",
				*[interactions.StringSelectOption(
					label = dict_values[i].prize, value = id
				) for i, id in enumerate(GIVEAWAYS)],
				placeholder = "Choose a giveaway"
			)
			await ctx.send(components = select_menu, ephemeral = True)
	#endregion

	#region - DELETE SELECT CALLBACK
	@interactions.component_callback("select_ga_delete")
	async def select_ga_delete(self, ctx: interactions.ComponentContext):
			await self.delete_giveaway(value = ctx.values[0])
			await ctx.edit_origin(content = f"Deleted the giveaway: {ctx.values[0]}", components = [])
	#endregion

	#region - DELETE FUNCTION
	async def delete_giveaway(self, value: str):
		if GIVEAWAYS.get(int(value)):
			del GIVEAWAYS[int(value)]
			pool = await Database.get_global_pool()
			if pool._closed:
				await Database.create_pool()
			await Database.drop_entries_table(int(value))
	#endregion

	#region - DATETIME AND UNIX TIMESTAMP FUNCTIONS
	def get_timestamp(self, duration: str):
		value = ""
		timer = ""
		for i in duration:
			if(i.isdigit()):
				value += i
			else:
				timer += i

		if "s" in timer.lower():
			unix_timestamp = int(time.time()) + int(value)
			return unix_timestamp
		if "m" in timer.lower():
			_value = int(value) * 60
			unix_timestamp = int(time.time()) + _value
			return unix_timestamp
		if "h" in timer.lower():
			_value = int(value) * 3600
			unix_timestamp = int(time.time()) + _value
			return unix_timestamp
		if "d" in timer.lower():
			_value = int(value) * 86400
			unix_timestamp = int(time.time()) + _value
			return unix_timestamp
		if "w" in timer.lower():
			_value = int(value) * 604800
			unix_timestamp = int(time.time()) + _value
			return unix_timestamp

	async def unix_to_datetime(self, timestamp: int):
		return datetime.datetime.utcfromtimestamp(timestamp)
	#endregion

	#region - GIVEAWAY TIMER
	async def giveaway_timer(self, timestamp: int, message_id: int):
		seconds_to_sleep = (timestamp - int(time.time()))
		await asyncio.sleep(seconds_to_sleep)
		pool = await Database.get_global_pool()
		if pool._closed:
			await Database.create_pool()
		giveaway_rows = await Database.get_all_giveaways()
		for row in giveaway_rows:
			if message_id == int(row["id"]):
				await self.end_giveaway(value = row["id"])
	#endregion

def setup(client):
	Giveaways(client)