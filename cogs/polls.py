from dataclasses import dataclass, field
import interactions

import yaml
with open("./server_ids.yaml") as config_file:
    server_ids = yaml.safe_load(config_file)

@dataclass
class Poll:
    title: str
    options: list[str]
    votes: dict[int, int] = field(default_factory = dict)

POLLS: dict[int, Poll] = {}
NUMBERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
END_POLL_EMOJI = "🔴"

POLL_MODAL = interactions.Modal(
    custom_id = "modal_poll",
    title = "Create a poll",
    *[
        interactions.InputText(style = interactions.TextStyles.SHORT, label = "Title", custom_id = "poll_title", required = True),
        interactions.InputText(style = interactions.TextStyles.PARAGRAPH, label = "Poll options (min: 2, max: 10)", custom_id = "poll_options", placeholder = "One option per line.", required = True)
    ])

class Polls(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    #region - POLLS COMMAND
    @interactions.slash_command(name = "poll", description = "creates a new poll",
        default_member_permissions = interactions.Permissions.MANAGE_MESSAGES, scopes = [server_ids["server_id"]])
    async def poll(self, ctx: interactions.SlashContext):
        await ctx.send_modal(modal = POLL_MODAL)
    #endregion

    #region - POLL MODAL CALLBACKS
    @interactions.modal_callback("modal_poll")
    async def modal_poll(self, ctx: interactions.ModalContext, poll_title: str, poll_options: str):
        _options = [option.strip() for option in poll_options.split('\n') if option.strip()]
        num = len(_options)
        if num > len(NUMBERS):
            await ctx.send(content = f"This poll have to many options ({num}, max: {len(NUMBERS)}).", ephemeral = True)
        elif num < 2:
            await ctx.send(content = f"This poll doesn't have enough options ({num}, min: 2).", ephemeral = True)
        else:
            poll = Poll(title = poll_title, options = _options)
            message = await ctx.send(content = "_Loading.._")
            POLLS[int(message.id)] = poll
            select_menu = interactions.StringSelectMenu(
                custom_id = "select_poll",
                *[interactions.StringSelectOption(
                    label = choice, value = str(i),
                    emoji = interactions.PartialEmoji(name = NUMBERS[i])
                ) for i, choice in enumerate(poll.options)],
                placeholder = poll.title
            )
            poll_embed = self.create_poll_embed(poll)
            poll_embed.set_footer(text = "ChatWitt | Polls", icon_url = ctx.guild.icon._url)
            await message.edit(content = "", embeds = poll_embed, components = select_menu)
            await ctx.send(content = f"The poll has been made. React with {END_POLL_EMOJI} to end the poll!", ephemeral = True)
    #endregion

    #region - POLL SELECT CALLBACK
    @interactions.component_callback("select_poll")
    async def on_poll_select(self, ctx: interactions.ComponentContext):
        option = int(ctx.values[0])
        voter_id = int(ctx.author.id)
        poll = POLLS.get(int(ctx.message.id))
        if not poll:
            await self.close_poll(ctx.message)
        else:
            poll.votes[voter_id] = option
            poll_embed = self.create_poll_embed(poll)
            poll_embed.set_footer(text = "ChatWitt | Polls", icon_url = ctx.guild.icon._url)
            await ctx.message.edit(embeds = poll_embed, components = ctx.message.components)
            await ctx.send(content = f"You chose option {NUMBERS[option]} - `{poll.options[option]}`", ephemeral = True)
    #endregion

    #region - CREATE POLL EMBED MESSAGE
    def create_poll_embed(self, poll: Poll) -> interactions.Embed:
        votes = [0 for _ in range(len(poll.options))]
        for voter_id, option in poll.votes.items():
            votes[option] += 1
        num_votes = len(poll.votes)
        if num_votes == 0:
            percentages = [0 for _ in range(len(votes))]
        else:
            percentages = [vote / num_votes for vote in votes]
        bars = []
        for percentage in percentages:
            num: int = round(percentage * 20)
            bars.append("█" * num)
        fields = [(
            f"{NUMBERS[i]} - {choice}",
            f"{bars[i]} **{round(percentages[i] * 100)}%** ({votes[i]})",
            False
        ) for i, choice in enumerate(poll.options)]
        poll_embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = "<:ChatWitt:1048944473675137054>  | ChatWitt - Polls |  <:ChatWitt:1048944473675137054>\n\n" +
            f"**{poll.title}**\n\U00002800" 
        )
        for field in fields:
            poll_embed.add_field(name = field[0], value = field[1], inline = field[2])
        return poll_embed
    #endregion

    #region - CLOSE POLL FUNCTION
    async def close_poll(self, message: interactions.Message):
        embed = message.embeds[0]
        embed.add_field(name = "\U00002800", value = "This poll has ended", inline = False)
        await message.edit(embeds = embed, components = [])
    #endregion

    #region - EVENT LISTENER ON REACTIONS TO POLL
    @interactions.listen()
    async def on_message_reaction_add(self, message_reaction: interactions.events.MessageReactionAdd):
        poll_id = int(message_reaction.message.id)
        poll = POLLS.get(poll_id)
        if message_reaction.author.has_permission(interactions.Permissions.MANAGE_MESSAGES):
            if message_reaction.emoji.name != END_POLL_EMOJI:
                return
            if not poll:
                return
            await self.close_poll(message_reaction.message)
            await message_reaction.message.remove_reaction(message_reaction.emoji, message_reaction.author)
            del POLLS[poll_id]
        else:
            if not poll:
                return
            await message_reaction.message.remove_reaction(message_reaction.emoji, message_reaction.author)
    #endregion

def setup(client):
    Polls(client)