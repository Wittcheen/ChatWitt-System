# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions

from utils.yaml_file import server_id, id_map

ANNOUNCEMENT_MODAL = interactions.Modal(
    custom_id = "announcement_form",
    title = "Send a new announcement",
    *[interactions.InputText(
        custom_id = "title", required = True, min_length = 1, max_length = 100,
        style = interactions.TextStyles.SHORT, label = "Title:"
    ),interactions.InputText(
        custom_id = "message", required = True, min_length = 1, max_length = 3500,
        style = interactions.TextStyles.PARAGRAPH, label = "Message:"
    )]
)

class Announcement(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

        self._type = None

    #region - ANNOUNCE COMMAND
    @interactions.slash_command(name = "announce", description = "send a new announcement",
        default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [server_id])
    @interactions.slash_option(name = "type", description = "choose the format of the message", opt_type = interactions.OptionType.STRING, required = True,
        choices = [interactions.SlashCommandChoice(name = "embed", value = "embed"), interactions.SlashCommandChoice(name = "text", value = "text")])
    async def announce(self, ctx: interactions.SlashContext, type: str):
        if ctx.channel.id == id_map["announcement_channel"]:
            self._type = type
            await ctx.send_modal(modal = ANNOUNCEMENT_MODAL)
        else:
            announcement_channel = ctx.guild.get_channel(id_map["announcement_channel"])
            await ctx.send(content = f"The command can't be used in this channel! Use it here instead: {announcement_channel.mention}", ephemeral = True)
    #endregion

    #region - ANNOUNCEMENT MODAL CALLBACK
    @interactions.modal_callback("announcement_form")
    async def __announcement_modal_response(self, ctx: interactions.ModalContext, title: str, message: str):
        ping_role = ctx.guild.get_role(id_map["ping_role"])
        if self._type == "embed":
            embed = interactions.Embed(
                color = int("0x2f3136", 0),
                description = ("<:chatwitt:1048944473675137054>  | ChatWitt - Announcement |  <:chatwitt:1048944473675137054>\n"
                    f"## {title}\n{message}"
                )
            )
            embed.set_footer(text = "ChatWitt | Announcement", icon_url = ctx.guild.icon._url)
            await ctx.channel.send(content = f"||{ping_role.mention}||", embeds = embed)
        else:
            await ctx.channel.send(content = f"||{ping_role.mention}||\n## {title}\n{message}")

        msg = await ctx.send(content = "_The announcement has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

def setup(client):
    Announcement(client)