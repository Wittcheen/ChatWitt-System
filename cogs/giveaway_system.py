# (c) 2025 Christoffer Wittchen
# Released under the MIT License.

from dataclasses import dataclass
import interactions
from utils.giveaway import GiveawayManager
# from cogs.miscellaneous import log_message
import asyncio, time

from utils.yaml_file import server_id

@dataclass
class Giveaway:
    prize: str
    timestamp: int
    author: int
    channel_id: int
    entries: int
    total_winners: int
    user_entries: list[int]
    winners: list[int]

GIVEAWAYS: dict[int, Giveaway] = {}

GIVEAWAY_MODAL = interactions.Modal(
    custom_id = "giveaway_form",
    title = "Create a giveaway",
    *[interactions.InputText(
        custom_id = "prize", required = True, min_length = 1, max_length = 128,
        style = interactions.TextStyles.SHORT, label = "Prize:"
    ),interactions.InputText(
        custom_id = "total_winners", required = True, min_length = 1, max_length = 2,
        style = interactions.TextStyles.SHORT, label = "Total winners:",  value = "1"
    ),interactions.InputText(
        custom_id = "duration", required = True, min_length = 2, max_length = 100,
        style = interactions.TextStyles.SHORT, label = "Duration:", placeholder = "Ex: 1d"
    )]
)

GIVEAWAY_BUTTON = interactions.Button(
    custom_id = "join_giveaway_button", style = interactions.ButtonStyle.PRIMARY,
    emoji = interactions.PartialEmoji(name = "\U0001F389")
)

class GiveawaySystem(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.listen()
    async def on_startup(self):
        rows = await GiveawayManager.get_active_giveaways()
        for row in rows:
            users = await GiveawayManager.get_all_entries(id = row["id"])
            GIVEAWAYS[int(row["id"])] = Giveaway(
                prize = row["prize"], timestamp = row["timestamp"], author = row["author"], channel_id = row["channel_id"],
                entries = row["entries"], total_winners = row["winners"], user_entries = users,  winners = []
            )
            asyncio.create_task(self.giveaway_timer(timestamp = row["timestamp"], id = row["id"]))

    #region - GIVEAWAY PARENT COMMAND
    @interactions.slash_command(name = "giveaway", description = "start, end and delete giveaways",
        default_member_permissions = interactions.Permissions.ADMINISTRATOR, scopes = [server_id])
    @interactions.slash_option(name = "command", description = "choose a command", opt_type = interactions.OptionType.STRING, required = True,
        choices = [interactions.SlashCommandChoice(name = cmd, value = cmd) for cmd in ["create", "end", "reroll", "delete"]])
    async def giveaway(self, ctx: interactions.SlashContext, command: str):
        _actions = {
            "create": self.create,
            "end": self.end,
            "reroll": self.reroll,
            "delete": self.delete
        }
        if callable(_actions[command]):
            await _actions[command](ctx)
        else:
            await ctx.send(content = "Invalid command!", ephemeral = True)
    #endregion

    #region - COMMAND ACTIONS
    async def create(self, ctx: interactions.SlashContext):
        await ctx.send_modal(modal = GIVEAWAY_MODAL)

    async def end(self, ctx: interactions.SlashContext):
        dict_values = list(GIVEAWAYS.values())
        if len(dict_values) == 0:
            await ctx.send(content = "No ongoing giveaways.", ephemeral = True)
        else:
            await self.__show_giveaway_selection(ctx, "giveaway_end_select", "Select a giveaway to end")

    async def reroll(self, ctx: interactions.SlashContext):
        dict_values = list(GIVEAWAYS.values())
        if len(dict_values) == 0:
            await ctx.send(content = "No giveaway data.", ephemeral = True)
        else:
            await self.__show_giveaway_selection(ctx, "giveaway_reroll_select", "Select a giveaway to reroll")

    async def delete(self, ctx: interactions.SlashContext):
        dict_values = list(GIVEAWAYS.values())
        if len(dict_values) == 0:
            await ctx.send(content = "No giveaways to delete.", ephemeral = True)
        else:
            await self.__show_giveaway_selection(ctx, "giveaway_delete_select", "Select a giveaway to delete")
    #endregion

    #region - GIVEAWAY MODAL CALLBACK
    @interactions.modal_callback("giveaway_form")
    async def __giveaway_modal_response(self, ctx: interactions.ModalContext, prize: str, total_winners: str, duration: str):
        unix_timestamp = self.calculate_timestamp(duration)
        giveaway = Giveaway(
            prize = prize, timestamp = unix_timestamp, author = ctx.author.id, channel_id = ctx.channel.id,
            entries = 0, total_winners = int(total_winners), user_entries = [],  winners = []
        )
        embed = self.__create_embed(giveaway)
        embed.set_footer(text = "ChatWitt | Giveaway", icon_url = ctx.guild.icon._url)
        message = await ctx.channel.send(embeds = embed, components = GIVEAWAY_BUTTON)
        GIVEAWAYS[int(message.id)] = giveaway
        asyncio.create_task(self.giveaway_timer(timestamp = giveaway.timestamp, id = message.id))
        data = {
            "id": message.id, "active": 1, "prize": giveaway.prize, "timestamp": giveaway.timestamp, "author": giveaway.author,
            "channel_id": giveaway.channel_id, "entries": giveaway.entries, "winners": giveaway.total_winners
        }
        await GiveawayManager.create_giveaway(message_id = message.id, data = data)
        await ctx.send(content = "The giveaway has been created.", ephemeral = True)
    #endregion

    #region - CREATE EMBED GIVEAWAY MESSAGE
    def __create_embed(self, giveaway: Giveaway) -> interactions.Embed:
        description = (
            "<:chatwitt:1048944473675137054>  | ChatWitt - Giveaway |  <:chatwitt:1048944473675137054>\n\n"
            f"**{giveaway.prize}**\n\n"
            f"{'Ended' if len(giveaway.winners) > 0 else 'Ends'}: <t:{giveaway.timestamp}:R> <t:{giveaway.timestamp}>\n"
            f"Created by: <@{giveaway.author}>\n"
            f"Entries: **{giveaway.entries}**\n"
        )
        if len(giveaway.winners) == 0:
            description += f"Winners: **{giveaway.total_winners}**"
        elif giveaway.winners[0] == "None":
            description += f"Winners: Nobody."
        else:
            winners = " ".join(f"<@{winner}>" for winner in giveaway.winners)
            description += f"Winners: {winners}"
        return interactions.Embed(color = int("0x2f3136", 0), description = description)
    #endregion

    #region - JOIN BUTTON EVENT
    @interactions.component_callback("join_giveaway_button")
    async def __join_giveaway_button(self, ctx: interactions.ComponentContext):
        giveaway = GIVEAWAYS.get(ctx.message.id)
        if giveaway:
            if ctx.author.id in giveaway.user_entries:
                leave_button = interactions.Button(
                    custom_id = "leave_giveaway_button", style = interactions.ButtonStyle.DANGER, label = "Leave the giveaway"
                )
                await ctx.send(content = f"You have already joined this giveaway! {ctx.message.jump_url}", components = leave_button, ephemeral = True)
            else:
                giveaway.entries += 1
                giveaway.user_entries.append(ctx.author.id)
                data = {"id": ctx.author.id, "user_name": ctx.author.display_name}
                await GiveawayManager.add_entry(id = ctx.message.id, data = data)
                embed = self.__create_embed(giveaway)
                embed.set_footer(text = "ChatWitt | Giveaway", icon_url = ctx.guild.icon._url)
                await ctx.edit_origin(embeds = embed, components = GIVEAWAY_BUTTON)
        else:
            await ctx.send(content = "This is an old giveaway.", ephemeral = True)
    #endregion

    #region - LEAVE BUTTON EVENT
    @interactions.component_callback("leave_giveaway_button")
    async def __leave_giveaway_button(self, ctx: interactions.ComponentContext):
        id = ctx.message.content.split("/")[-1]
        giveaway = GIVEAWAYS.get(int(id))
        if giveaway:
            if ctx.author.id in giveaway.user_entries:
                giveaway.entries -= 1
                giveaway.user_entries.remove(ctx.author.id)
                await GiveawayManager.remove_entry(id = int(id), user_id = ctx.author.id)
                embed = self.__create_embed(giveaway)
                embed.set_footer(text = "ChatWitt | Giveaway", icon_url = ctx.guild.icon._url)
                message = await ctx.channel.fetch_message(message_id = int(id))
                await message.edit(embeds = embed, components = GIVEAWAY_BUTTON)
                await ctx.edit_origin(content = "You leaved this giveaway!", components = [])
            else:
                await ctx.send(content = "You aren't in this giveaway", ephemeral = True)
        else:
            await ctx.send(content = "This is an old giveaway.", ephemeral = True)
    #endregion

    #region - END SELECT CALLBACK
    @interactions.component_callback("giveaway_end_select")
    async def __giveaway_end_select_response(self, ctx: interactions.ComponentContext):
        giveaway = GIVEAWAYS.get(int(ctx.values[0]))
        if giveaway:
            giveaway.timestamp = int(time.time())
            giveaway.winners = await GiveawayManager.select_winners(id = int(ctx.values[0]), limit = giveaway.total_winners)
            await GiveawayManager.mark_as_completed(id = int(ctx.values[0]))
            await self.update_giveaway_message(giveaway = giveaway, id = int(ctx.values[0]), action = "end")
            await ctx.edit_origin(content = f"Ended the giveaway: {ctx.values[0]}", components = [])
            # await log_message(self, f"{ctx.author.mention} ended the giveaway: {ctx.values[0]}")
    #endregion

    #region - REROLL SELECT CALLBACK
    @interactions.component_callback("giveaway_reroll_select")
    async def __giveaway_reroll_select_response(self, ctx: interactions.ComponentContext):
        await ctx.send_modal(modal = interactions.Modal(
            custom_id = f"reroll_form_{int(ctx.values[0])}",
            title = f"Reroll the giveaway",
            *[interactions.InputText(
                custom_id = "count", required = True, min_length = 1, max_length = 2,
                style = interactions.TextStyles.SHORT, label = "Number of rerolls:"
            )]
        ))

    @interactions.modal_callback(r"reroll_form_*")
    async def __reroll_modal_response(self, ctx: interactions.ModalContext, count: str):
        id = ctx.custom_id[len("reroll_form_"):]
        giveaway = GIVEAWAYS.get(int(id))
        if giveaway:
            if int(count) > giveaway.total_winners:
                await ctx.send(content = f"Cannot reroll {count} winners; the giveaway only has {giveaway.total_winners} winners.", ephemeral = True)
                return
            giveaway.winners = await GiveawayManager.select_winners(id = int(id), limit = int(count))
            if giveaway.winners[0] == "None":
                await ctx.send(content = f"No more entries, so no one won reroll!", ephemeral = True)
            else:
                await self.update_giveaway_message(giveaway = giveaway, id = int(id), action = "reroll")
                await ctx.send(content = f"Rerolled {count} winners.", ephemeral = True)
    #endregion

    #region - DELETE SELECT CALLBACK
    @interactions.component_callback("giveaway_delete_select")
    async def __giveaway_delete_select_response(self, ctx: interactions.ComponentContext):
        if GIVEAWAYS.get(int(ctx.values[0])):
            del GIVEAWAYS[int(ctx.values[0])]
            await GiveawayManager.delete_giveaway(id = int(ctx.values[0]))
            await ctx.edit_origin(content = f"Deleted the giveaway: {ctx.values[0]}", components = [])
    #endregion

    #region - UPDATE GIVEAWAY MESSAGE
    async def update_giveaway_message(self, giveaway: Giveaway, id: int, action: str):
        channel = self.client.get_channel(channel_id = giveaway.channel_id)
        message = await channel.fetch_message(message_id = id)
        embed = self.__create_embed(giveaway)
        action_text = "Ended" if action == "end" else "Rerolled"
        embed.set_footer(text = f"ChatWitt | Giveaway {action_text}", icon_url = channel.guild.icon._url)
        await message.edit(embeds = embed, components = [])
        if action == "end" and giveaway.winners[0] == "None":
            await message.reply(content = f"No entries, so no one won this giveaway!")
            return
        winners = " ".join(f"<@{winner}>" for winner in giveaway.winners)
        if action == "end":
            await message.reply(content = f"Congratulations {winners}! You won **{giveaway.prize}**!")
        elif action == "reroll":
            await message.reply(content = f"Congratulations {winners}, you won the reroll of **{giveaway.prize}**!")
    #endregion

    async def __show_giveaway_selection(self, ctx: interactions.SlashContext, custom_id: str, placeholder: str):
        select_menu = interactions.StringSelectMenu(
            custom_id = custom_id,
            *[interactions.StringSelectOption(
                label = giveaway.prize, value = id
            ) for id, giveaway in GIVEAWAYS.items()],
            placeholder = placeholder
        )
        await ctx.send(components = select_menu, ephemeral = True)

    def calculate_timestamp(self, duration: str) -> int:
        value = int("".join([i for i in duration if i.isdigit()]))
        unit = "".join([i for i in duration if not i.isdigit()]).lower()
        time_units = {
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
            "w": 604800
        }
        if unit in time_units:
            return int(time.time()) + (value * time_units[unit])
        return int(time.time())  # Default case if no valid unit is found

    async def giveaway_timer(self, timestamp: int, id: int):
        now = int(time.time())
        seconds_to_sleep = max(timestamp - now, 0)
        await asyncio.sleep(seconds_to_sleep)
        giveaway = GIVEAWAYS.get(id)
        if giveaway:
            giveaway.timestamp = now
            giveaway.winners = await GiveawayManager.select_winners(id = id, limit = giveaway.total_winners)
            await GiveawayManager.mark_as_completed(id = id)
            await self.update_giveaway_message(giveaway = giveaway, id = id, action = "end")

def setup(client):
    GiveawaySystem(client)
