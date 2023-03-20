import interactions
from interactions.ext.tasks import IntervalTrigger, create_task

import yaml
with open("./botconfig.yaml") as config_file:
    data = yaml.safe_load(config_file)

class Automations(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client
        self.update_member_channel.start(self)

    # MEMBER JOIN LISTENER
    @interactions.extension_listener()
    async def on_guild_member_add(self, member: interactions.GuildMember):
        with open("./botconfig.yaml") as config_file:
            data = yaml.safe_load(config_file)
        members = data["member_count"] + 1
        data["member_count"] = members
        with open("./botconfig.yaml", 'w') as config_file:
            yaml.dump(data, config_file)
        new_members_channel = await interactions.get(self.client, interactions.Channel, object_id = data["new_members_channel_id"])
        embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - Welcome |  <:chatwitt:1048944473675137054>\n\n" + 
            f"Welcome {member.mention} to the __ChatWitt__ Discord!\nWe hope you are staying on the server.\n"
        )
        if new_members_channel is not None:
            await new_members_channel.send(embeds = embed)
            await member.add_role(data["new_member_role_id"])

    # UPDATE MEMBER-COUNT CHANNEL
    @create_task(IntervalTrigger(900))
    async def update_member_channel(self):
        with open("./botconfig.yaml") as config_file:
            data = yaml.safe_load(config_file)
        member_count = data["member_count"]
        member_count_channel = await interactions.get(self.client, interactions.Channel, object_id = data["member_count_channel_id"])
        if member_count_channel is not None:
            await member_count_channel.modify(name = f"\U0001F30E・Members: {member_count}")

def setup(client):
    Automations(client)