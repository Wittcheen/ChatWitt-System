# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions

import yaml
with open("./yaml/server_ids.yaml") as config_file:
    server_ids = yaml.safe_load(config_file)

class Miscellaneous(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    #region - PURGE COMMAND
    @interactions.slash_command(name = "purge", description = "deletes the amount of messages",
        default_member_permissions = interactions.Permissions.MANAGE_MESSAGES, scopes = [server_ids["server_id"]])
    @interactions.slash_option(name = "amount", description = "write the amount to delete", opt_type = interactions.OptionType.INTEGER)
    async def clear(self, ctx: interactions.SlashContext, amount: int = 1):
        await ctx.channel.purge(deletion_limit = amount)
        message = await ctx.send(content = f"Deleted {amount} message(s) from this channel!", ephemeral = True)
        await ctx.delete(message.id)
    #endregion

def setup(client):
    Miscellaneous(client)