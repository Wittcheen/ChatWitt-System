# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions

import yaml
with open("./yaml/id_map.yaml") as config_file:
    id_map = yaml.safe_load(config_file)

SAY_MODAL = interactions.Modal(
    custom_id = "say_form",
    title = "Send a message as the bot",
    *[interactions.InputText(
        custom_id = "say_message", required = True, min_length = 1, max_length = 3500,
        style = interactions.TextStyles.PARAGRAPH, label = "Write the message the bot should send"
    )]
)

class Miscellaneous(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    #region - PURGE COMMAND
    @interactions.slash_command(name = "purge", description = "deletes the amount of messages",
        default_member_permissions = interactions.Permissions.MANAGE_MESSAGES, scopes = [id_map["server_id"]])
    @interactions.slash_option(name = "amount", description = "write the amount to delete", opt_type = interactions.OptionType.INTEGER)
    async def clear(self, ctx: interactions.SlashContext, amount: int = 1):
        await ctx.channel.purge(deletion_limit = amount)
        message = await ctx.send(content = f"Deleted {amount} message(s) from this channel!", ephemeral = True)
        await ctx.delete(message.id)
    #endregion

    #region - SAY COMMAND
    @interactions.slash_command(name = "say", description = "send a message as the bot",
        default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [id_map["server_id"]])
    async def say(self, ctx: interactions.SlashContext):
        await ctx.send_modal(modal = SAY_MODAL)
    @interactions.modal_callback("say_form")
    async def say_modal_response(self, ctx: interactions.ModalContext, say_message: str):
        await ctx.channel.send(content = say_message)
        message = await ctx.send(content = "Completed.", ephemeral = True)
        await ctx.delete(message.id)
    #endregion

def setup(client):
    Miscellaneous(client)