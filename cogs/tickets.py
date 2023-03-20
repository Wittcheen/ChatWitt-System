import interactions

import yaml
with open("./botconfig.yaml") as config_file:
    data = yaml.safe_load(config_file)

TICKET_OPTIONS = ["Contact about programming", "Discuss about graphic and design", "Make a request for Twitch mod"]

PROGRAMMING_MODAL = interactions.Modal(
    custom_id = "programming_form",
    title = "Programming discussion",
    components = [
        interactions.TextInput(
            style = interactions.TextStyleType.PARAGRAPH, label = "Why do you wan't to create this ticket?", custom_id = "user_why", required = True, min_length = 50, max_length = 3500)
    ])
GRAPHICS_MODAL = interactions.Modal(
    custom_id = "graphics_form",
    title = "Graphic and design discussion",
    components = [
        interactions.TextInput(
            style = interactions.TextStyleType.PARAGRAPH, label = "Why do you wan't to create this ticket?", custom_id = "user_why", required = True, min_length = 50, max_length = 3500)
    ])
TWITCH_MODAL = interactions.Modal(
    custom_id = "twitch_mod_form",
    title = "Modansøgning",
    components = [
        interactions.TextInput(
            style = interactions.TextStyleType.SHORT, label = "Twitch og IRL navn:", custom_id = "user_name", required = True, min_length = 1, max_length = 100),
        interactions.TextInput(
            style = interactions.TextStyleType.SHORT, label = "Hvor gammel er du?", custom_id = "user_age", required = True, min_length = 2, max_length = 2), 
        interactions.TextInput(
            style = interactions.TextStyleType.PARAGRAPH, label = "Hvorfor skal DU være mod, og har du erfaring?", custom_id = "user_whyme", required = True, min_length = 100, max_length = 3000), 
        interactions.TextInput(
            style = interactions.TextStyleType.PARAGRAPH, label = "Hvor længe har du fulgt Sjippi på Twitch?", placeholder = "Eventuelt tilføj et billede, som et link", custom_id = "user_follow", required = True, min_length = 10, max_length = 100)
    ])

CLOSE_TICKET_BUTTON = interactions.Button(
    style = interactions.ButtonStyle.SECONDARY, emoji = interactions.Emoji(name = "\U0001F512"), label = "Close this ticket", custom_id = "close_ticket"
)

class Tickets(interactions.Extension):
    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command(default_member_permissions = interactions.Permissions.ADMINISTRATOR, scope = data["server_id"])
    async def opentickets(self, ctx: interactions.CommandContext):
        """Send the ticket message into this channel"""
        await ctx.get_channel()
        server_rules = await interactions.get(self.client, interactions.Channel, object_id = data["rules_channel_id"])
        tickets_embed = interactions.Embed(
            color = int("0x2f3136", 0),
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - Tickets |  <:chatwitt:1048944473675137054>\n\n" + 
            "**Wan't to contact the owner?**\n\n" +
            "Go down and select why you wan't to contact the owner.\n" +
            f"There is {len(TICKET_OPTIONS)} different options to choose from. Fill out the form,\nand remember to be patient for your answer.\n\n" +
            f"> _As mentioned in rule §3.4 ({server_rules.mention}), don't create a ticket for fun, take it serious!_"
        )
        tickets_embed.set_footer(text = "ChatWitt | Tickets", icon_url = ctx.guild.icon_url)
        tickets_embed.set_thumbnail(url = ctx.guild.icon_url)
        select_ticket = interactions.SelectMenu(
            custom_id = "select_ticket",
            options = [interactions.SelectOption(
                label = choice, value = str(i)
            ) for i, choice in enumerate(TICKET_OPTIONS)],
            placeholder = "Choose why you wan't to contant the owner"
        )
        await ctx.channel.send(embeds = tickets_embed, components = select_ticket)
        await ctx.send("You started the ticket system!", ephemeral = True)

    @interactions.extension_component("select_ticket")
    async def on_ticket_select(self, ctx: interactions.ComponentContext, options: list):
        option = int(options[0])
        for i, choice in enumerate(TICKET_OPTIONS):
            if i == option:
                if "programming" in choice:
                    await ctx.popup(PROGRAMMING_MODAL)
                if "graphic" in choice:
                    await ctx.popup(GRAPHICS_MODAL)
                if "Twitch" in choice:
                    await ctx.popup(TWITCH_MODAL)

    @interactions.extension_modal("programming_form")
    async def programming_modal_response(self, ctx: interactions.CommandContext, user_why: str):
        with open("./botconfig.yaml") as config_file:
            data = yaml.safe_load(config_file)
        embed = interactions.Embed(
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - Tickets |  <:chatwitt:1048944473675137054>\n\n" +
            f"**{PROGRAMMING_MODAL.title}** - {ctx.author.mention}\n\U00002800" 
        )
        value_list = [user_why]
        for i, comp in enumerate(PROGRAMMING_MODAL.components):
            embed.add_field(name = f"*{comp.label}*", value = value_list[i], inline = False)
        embed.set_footer(text = "ChatWitt | Tickets", icon_url = ctx.guild.icon_url)
        if await self.check_ticket_exists(ctx):
                await ctx.send("You already have an active ticket!", ephemeral = True)
        else:
            createdChannel = await ctx.guild.create_channel(parent_id = data["tickets_category_id"],
            name = f'ticket-{data["ticket_number"]}', type = interactions.ChannelType.GUILD_TEXT,
            permission_overwrites = [interactions.Overwrite(id = int(ctx.author.id), type = 1, allow = interactions.Permissions.VIEW_CHANNEL),
            interactions.Overwrite(id = data["everyone_role_id"], type = 0, deny = interactions.Permissions.VIEW_CHANNEL)]
            )
            await ctx.send(f"You created a ticket {createdChannel.mention}. An answer will return as fast as possible!", ephemeral = True)
            message = await createdChannel.send(embeds = embed)
            await self.autoreply(message)
            new_number = data["ticket_number"] + 1
            data["ticket_number"] = new_number
            with open("./botconfig.yaml", 'w') as config_file:
                yaml.dump(data, config_file)

    @interactions.extension_modal("graphics_form")
    async def graphics_modal_response(self, ctx: interactions.CommandContext, user_why: str):
        with open("./botconfig.yaml") as config_file:
            data = yaml.safe_load(config_file)
        embed = interactions.Embed(
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - Tickets |  <:chatwitt:1048944473675137054>\n\n" +
            f"**{GRAPHICS_MODAL.title}** - {ctx.author.mention}\n\U00002800" 
        )
        value_list = [user_why]
        for i, comp in enumerate(GRAPHICS_MODAL.components):
            embed.add_field(name = f"*{comp.label}*", value = value_list[i], inline = False)
        embed.set_footer(text = "ChatWitt | Tickets", icon_url = ctx.guild.icon_url)
        if await self.check_ticket_exists(ctx):
                await ctx.send("You already have an active ticket!", ephemeral = True)
        else:
            createdChannel = await ctx.guild.create_channel(parent_id = data["tickets_category_id"],
            name = f'ticket-{data["ticket_number"]}', type = interactions.ChannelType.GUILD_TEXT,
            permission_overwrites = [interactions.Overwrite(id = int(ctx.author.id), type = 1, allow = interactions.Permissions.VIEW_CHANNEL),
            interactions.Overwrite(id = data["everyone_role_id"], type = 0, deny = interactions.Permissions.VIEW_CHANNEL)]
            )
            await ctx.send(f"You created a ticket {createdChannel.mention}. An answer will return as fast as possible!", ephemeral = True)
            message = await createdChannel.send(embeds = embed)
            await self.autoreply(message)
            new_number = data["ticket_number"] + 1
            data["ticket_number"] = new_number
            with open("./botconfig.yaml", 'w') as config_file:
                yaml.dump(data, config_file)

    @interactions.extension_modal("twitch_mod_form")
    async def twitch_mod_modal_response(self, ctx: interactions.CommandContext, user_name: str, user_age: str, user_whyme: str, user_follow: str):
        with open("./botconfig.yaml") as config_file:
            data = yaml.safe_load(config_file)
        embed = interactions.Embed(
            description = "<:chatwitt:1048944473675137054>  | ChatWitt - Tickets |  <:chatwitt:1048944473675137054>\n\n" +
            f"**{TWITCH_MODAL.title}** - {ctx.author.mention}\n\U00002800" 
        )
        value_list = [user_name, user_age, user_whyme, user_follow]
        for i, comp in enumerate(TWITCH_MODAL.components):
            embed.add_field(name = f"*{comp.label}*", value = value_list[i], inline = False)
        embed.set_footer(text = "ChatWitt | Tickets", icon_url = ctx.guild.icon_url)
        if await self.check_ticket_exists(ctx):
                await ctx.send("You already have an active ticket!", ephemeral = True)
        else:
            createdChannel = await ctx.guild.create_channel(parent_id = data["tickets_category_id"],
            name = f'ticket-{data["ticket_number"]}', type = interactions.ChannelType.GUILD_TEXT,
            permission_overwrites = [interactions.Overwrite(id = int(ctx.author.id), type = 1, allow = interactions.Permissions.VIEW_CHANNEL),
            interactions.Overwrite(id = data["everyone_role_id"], type = 0, deny = interactions.Permissions.VIEW_CHANNEL)]
            )
            await ctx.send(f"You created a ticket {createdChannel.mention}. An answer will return as fast as possible!", ephemeral = True)
            message = await createdChannel.send(embeds = embed)
            await self.autoreply(message)
            new_number = data["ticket_number"] + 1
            data["ticket_number"] = new_number
            with open("./botconfig.yaml", 'w') as config_file:
                yaml.dump(data, config_file)

    async def check_ticket_exists(self, ctx: interactions.CommandContext) -> bool:
        await ctx.get_guild()
        for channel in await ctx.guild.get_all_channels():
            for overwrite in channel.permission_overwrites:
                if int(overwrite.id) == int(ctx.author.id) and int(overwrite.type) == 1 and int(overwrite.allow) & interactions.Permissions.VIEW_CHANNEL == interactions.Permissions.VIEW_CHANNEL:
                    return True
                if int(overwrite.id) == int(ctx.author.id) and int(overwrite.type) == 1 and int(overwrite.deny) & interactions.Permissions.VIEW_CHANNEL == interactions.Permissions.VIEW_CHANNEL:
                    return True
        return False

    async def autoreply(self, message: interactions.Message):
        await message.reply("Remember to be patient for your answer, and if you regret your ticket, you can always close it.", components = CLOSE_TICKET_BUTTON)

    @interactions.extension_component("close_ticket")
    async def close_ticket(self, ctx: interactions.CommandContext):
        confirm_button = interactions.Button(
            style = interactions.ButtonStyle.SUCCESS, label = "Confirm", custom_id = "confirm_button"
        )
        cancel_button = interactions.Button(
            style = interactions.ButtonStyle.DANGER, label = "Cancel", custom_id = "cancel_button"
        )
        button_row = interactions.ActionRow(
            components = [confirm_button, cancel_button]
        )
        await ctx.send(f"Are you sure you wan't to close this ticket?", components = button_row)

    @interactions.extension_component("cancel_button")
    async def cancel_button(self, ctx: interactions.CommandContext):
        await ctx.message.delete()

    @interactions.extension_component("confirm_button")
    async def confirm_button(self, ctx: interactions.CommandContext):
        channel = await ctx.get_channel()
        await ctx.send("This ticket is closing!", ephemeral = True)
        await channel.delete()

def setup(client):
    Tickets(client)