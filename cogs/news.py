# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions

import yaml
with open("./yaml/id_map.yaml") as config_file:
    id_map = yaml.safe_load(config_file)

NEWS_MODAL = interactions.Modal(
    custom_id = "news_form",
    title = "Send a news announcement",
    *[interactions.InputText(
        custom_id = "news_title", required = True, min_length = 1, max_length = 100,
        style = interactions.TextStyles.SHORT, label = "Title:"
    ),interactions.InputText(
        custom_id = "news_message", required = True, min_length = 1, max_length = 3500,
        style = interactions.TextStyles.PARAGRAPH, label = "Message:"
    )]
)

class News(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

        self.news_type = None

    #region - NEWS COMMAND
    @interactions.slash_command(name = "news", description = "send a news announcement",
        default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [id_map["server_id"]])
    @interactions.slash_option(name = "type", description = "choose the news format", opt_type = interactions.OptionType.STRING, required = True,
        choices = [interactions.SlashCommandChoice(name = "embed", value = "embed"), interactions.SlashCommandChoice(name = "text", value = "text")])
    async def ssm(self, ctx: interactions.SlashContext, type: str):
        if ctx.channel.id == id_map["news_channel_id"]:
            self.news_type = type
            await ctx.send_modal(modal = NEWS_MODAL)
        else:
            news_channel = ctx.guild.get_channel(id_map["news_channel_id"])
            await ctx.send(content = f"The command can't be used in this channel! Use it here instead: {news_channel.mention}", ephemeral = True)
    #endregion

    #region - NEWS MODAL CALLBACK
    @interactions.modal_callback("news_form")
    async def news_modal_response(self, ctx: interactions.ModalContext, news_title: str, news_message: str):
        news_ping = ctx.guild.get_role(id_map["news_ping_role_id"])
        if self.news_type == "embed":
            embed = interactions.Embed(
                color = int("0x2f3136", 0),
                description = (
                    "<:chatwitt:1048944473675137054>  | ChatWitt - Nyhed |  <:chatwitt:1048944473675137054>\n"
                    f"## {news_title}\n{news_message}"
                )
            )
            embed.set_footer(text = "ChatWitt | Nyhed", icon_url = ctx.guild.icon._url)
            await ctx.channel.send(content = f"||{news_ping.mention}||", embeds = embed)
        else:
            await ctx.channel.send(content = f"||{news_ping.mention}||\n## {news_title}\n{news_message}")

        msg = await ctx.send(content = "_The news announcement has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

def setup(client):
    News(client)