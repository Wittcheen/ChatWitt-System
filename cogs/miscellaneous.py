# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions

from utils.yaml_file import server_id

SAY_MODAL = interactions.Modal(
    custom_id = "say_form",
    title = "Send a message as the bot",
    *[interactions.InputText(
        custom_id = "message", required = True, min_length = 1, max_length = 3500,
        style = interactions.TextStyles.PARAGRAPH, label = "Message:"
    )]
)

class Miscellaneous(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    #region - PURGE COMMAND
    @interactions.slash_command(name = "purge", description = "deletes the amount of messages",
        default_member_permissions = interactions.Permissions.MANAGE_MESSAGES, scopes = [server_id])
    @interactions.slash_option(name = "amount", description = "specify the amount to delete", opt_type = interactions.OptionType.INTEGER)
    async def purge(self, ctx: interactions.SlashContext, amount: int = 1):
        await ctx.channel.purge(deletion_limit = amount)
        msg = await ctx.send(content = f"Deleted {amount} message(s) from this channel!", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

    #region - SAY COMMAND
    @interactions.slash_command(name = "say", description = "send a message as the bot",
        default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [server_id])
    async def say(self, ctx: interactions.SlashContext):
        await ctx.send_modal(modal = SAY_MODAL)
    @interactions.modal_callback("say_form")
    async def __say_modal_response(self, ctx: interactions.ModalContext, message: str):
        await ctx.channel.send(content = message)
        msg = await ctx.send(content = "_The message has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

def setup(client):
    Miscellaneous(client)