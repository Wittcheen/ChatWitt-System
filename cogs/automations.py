import interactions
from interactions.models.internal.tasks import IntervalTrigger

import yaml
with open("./server_ids.yaml") as config_file:
	server_ids = yaml.safe_load(config_file)

class Automations(interactions.Extension):
	def __init__(self, client):
		self.client: interactions.Client = client

	@interactions.listen()
	async def on_startup(self):
		self.update_member_channel.start()

	#region - MEMBER JOIN LISTENER
	@interactions.listen()
	async def on_member_add(self, member_add: interactions.events.MemberAdd):
		with open("./server_ids.yaml") as config_file:
			server_ids = yaml.safe_load(config_file)
		members = server_ids["member_count"] + 1
		server_ids["member_count"] = members
		with open("./server_ids.yaml", 'w') as config_file:
			yaml.dump(server_ids, config_file)
		new_members_channel = member_add.guild.get_channel(server_ids["new_members_channel_id"])
		embed = interactions.Embed(
			color = int("0x2f3136", 0),
			description = "<:chatwitt:1048944473675137054>  | ChatWitt - Welcome |  <:chatwitt:1048944473675137054>\n\n" + 
			f"Welcome {member_add.member.mention} to __ChatWitt__ Discord!\nWe hope you are staying on the server.\n"
		)
		if new_members_channel is not None:
			await new_members_channel.send(embeds = embed)
			await member_add.member.add_role(server_ids["new_member_role_id"])
	#endregion

	#region - MEMBER LEAVE LISTENER
	@interactions.listen()
	async def on_member_remove(self, member_remove: interactions.events.MemberRemove):
		with open("./server_ids.yaml") as config_file:
			server_ids = yaml.safe_load(config_file)
		members = server_ids["member_count"] - 1
		server_ids["member_count"] = members
		with open("./server_ids.yaml", 'w') as config_file:
			yaml.dump(server_ids, config_file)
	#endregion

	#region - UPDATE MEMBER-COUNT CHANNEL
	@interactions.Task.create(IntervalTrigger(minutes = 15))
	async def update_member_channel(self):
		with open("./server_ids.yaml") as config_file:
			server_ids = yaml.safe_load(config_file)
		member_count = server_ids["member_count"]
		member_count_channel = self.client.get_guild(server_ids["server_id"]).get_channel(server_ids["member_count_channel_id"])
		if member_count_channel is not None:
			await member_count_channel.edit(name = f"\U0001F30E・Members: {member_count}")
	#endregion

def setup(client):
	Automations(client)