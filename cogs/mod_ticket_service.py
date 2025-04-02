# (c) 2025 Christoffer Wittchen
# Released under the MIT License.

import interactions

from utils.yaml_file import id_map, yaml_instance

TWITCH_MOD_MODAL = interactions.Modal(
    custom_id = "twitch_mod_form",
    title = "Modansøgning",
    *[interactions.InputText(
        custom_id = "name", required = True, min_length = 1, max_length = 100,
        style = interactions.TextStyles.SHORT, label = "Twitch og IRL navn:"
    ),interactions.InputText(
        custom_id = "age", required = True, min_length = 2, max_length = 2,
        style = interactions.TextStyles.SHORT, label = "Hvor gammel er du?"
    ),interactions.InputText(
        custom_id = "why_me", required = True, min_length = 100, max_length = 3000,
        style = interactions.TextStyles.PARAGRAPH, label = "Hvorfor skal DU være mod, og har du erfaring?"
    ),interactions.InputText(
        custom_id = "follow", required = True, min_length = 10, max_length = 100,
        style = interactions.TextStyles.PARAGRAPH, label = "Hvor længe har du fulgt Sjippi på Twitch?", placeholder = "Eventuelt tilføj et billede, som et link"
    )]
)

CLOSE_TICKET_BUTTON = interactions.Button(
    custom_id = "close_ticket_button", style = interactions.ButtonStyle.SECONDARY,
    emoji = interactions.PartialEmoji(name = "\U0001F512"), label = "Luk denne ticket"
)

class ModTicketService(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    #region - SEND TWITCH MOD TICKET MESSAGE
    async def mod_ticket(self, ctx: interactions.SlashContext):
        embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = ("<:chatwitt:1048944473675137054>  | ChatWitt - Twitch Mod Ansøgning |  <:chatwitt:1048944473675137054>\n\n"
            "**Vil du gerne være mod?**\n\n"
            "Gå ned og send en ansøgning, hvorfor du skal være mod.\n"
            "Udfyld skemaet, og husk at være tålmodig med dit svar.\n\n"
            "> _Kun send en ansøgning, hvis du reelt vil være mod!_"
        ))
        embed.set_footer(text = "ChatWitt | Twitch Mod Ansøgning", icon_url = ctx.guild.icon._url)
        open_ticket_button = interactions.Button(
            custom_id = "open_ticket_button", style = interactions.ButtonStyle.SECONDARY,
            emoji = interactions.PartialEmoji(name = "\U0001F4E9"), label = "Tryk her for at begynde"
        )
        await ctx.channel.send(embeds = embed, components = open_ticket_button)
        msg = await ctx.send(content = "_The mod ticket message has been sent._", ephemeral = True)
        await ctx.delete(msg.id)
    #endregion

    #region - OPEN TICKET BUTTON EVENT
    @interactions.component_callback("open_ticket_button")
    async def __open_ticket_button(self, ctx: interactions.ComponentContext):
        if await self.is_ticket_active(user_id = ctx.author_id):
            return await ctx.send("Du har allerede en aktiv mod ticket!", ephemeral = True)
        await ctx.send_modal(modal = TWITCH_MOD_MODAL)
    #endregion

    #region - TWITCH MOD MODAL CALLBACK
    @interactions.modal_callback("twitch_mod_form")
    async def __twitch_mod_modal_response(self, ctx: interactions.ModalContext, name: str, age: str, why_me: str, follow: str):
        embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = ("<:chatwitt:1048944473675137054>  | ChatWitt - Twitch Mod Ansøgning |  <:chatwitt:1048944473675137054>\n\n"
            f"**Ansøger:** {ctx.author.mention}\n\U00002800"
        ))
        for comp, value in zip(TWITCH_MOD_MODAL.components, [name, age, why_me, follow]):
            embed.add_field(name = f"*{comp.label}*", value = value, inline = False)
        embed.set_footer(text = "ChatWitt | Twitch Mod Ansøgning", icon_url = ctx.guild.icon._url)
        created_channel = await self.__create_mod_ticket_channel(ctx)
        message = await created_channel.send(embeds = embed)
        await message.reply(f"{ctx.author.mention}, husk at være tålmodig. Hvis du fortryder, kan du altid lukke din ticket.", components = CLOSE_TICKET_BUTTON)
        await self.add_active_ticket(user_id = ctx.author_id)
        await ctx.send(f"Du oprettede en mod ticket {created_channel.mention}.", ephemeral = True)
    #endregion

    #region - CREATE MOD TICKET CHANNEL
    async def __create_mod_ticket_channel(self, ctx: interactions.BaseContext) -> interactions.GuildChannel:
        created_channel = await ctx.guild.create_text_channel(
            category = id_map["mod_tickets_category"], name = f'ticket-{ctx.author.username}',
            permission_overwrites = [
                interactions.PermissionOverwrite(id = int(ctx.author_id), type = 1, allow = interactions.Permissions.VIEW_CHANNEL),
                interactions.PermissionOverwrite(id = id_map["everyone_role"], type = 0, deny = interactions.Permissions.VIEW_CHANNEL)
            ]
        )
        return created_channel
    #endregion

    #region - CLOSE TICKET BUTTONS EVENT
    @interactions.component_callback("close_ticket_button")
    async def __close_ticket_button(self, ctx: interactions.ComponentContext):
        user_id = ctx.message._mention_ids[1]
        confirm_button = interactions.Button(
            custom_id = "confirm_button", style = interactions.ButtonStyle.SUCCESS, label = "Confirm"
        )
        cancel_button = interactions.Button(
            custom_id = "cancel_button", style = interactions.ButtonStyle.DANGER, label = "Cancel"
        )
        button_row = interactions.ActionRow(*[confirm_button, cancel_button])
        await ctx.send(f"Er du sikker på, at du vil lukke <@{user_id}>'s ticket?", components = button_row)

    @interactions.component_callback("confirm_button")
    async def __confirm_button(self, ctx: interactions.ComponentContext):
        await ctx.send("Denne ticket lukkes!", ephemeral = True)
        user_id = ctx.message._mention_ids[0]
        await self.remove_active_ticket(user_id = user_id)
        await ctx.channel.delete()

    @interactions.component_callback("cancel_button")
    async def __cancel_button(self, ctx: interactions.ComponentContext):
        await ctx.message.delete()
    #endregion

    #region - MOD TICKET STORAGE
    async def load_active_tickets(self):
        tickets = await yaml_instance.get("mod_tickets")
        return tickets["user_ids"] if tickets else []

    async def add_active_ticket(self, user_id):
        users_list = await self.load_active_tickets()
        if int(user_id) not in users_list:
            users_list.append(int(user_id))
            await yaml_instance.dump("mod_tickets", {"user_ids": users_list})

    async def remove_active_ticket(self, user_id):
        users_list = await self.load_active_tickets()
        if int(user_id) in users_list:
            users_list.remove(int(user_id))
            await yaml_instance.dump("mod_tickets", {"user_ids": users_list})

    async def is_ticket_active(self, user_id) -> bool:
        return int(user_id) in await self.load_active_tickets()
    #endregion

def setup(client):
    ModTicketService(client)
