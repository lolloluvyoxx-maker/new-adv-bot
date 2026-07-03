import discord
import functools
import re
from utils.Tools import *


def _prettify_cog_name(name: str) -> str:
    """Turn a Cog class name like 'AutoRole' or 'StaffDMCog' into a readable
    category label like 'Auto Role' / 'Staff DM', without relying on any
    per-cog convention the cog itself has to implement."""
    if name.lower().endswith("cog"):
        name = name[:-3]
    name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', name)
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)
    name = name.strip()
    if not name:
        return "General"
    if name == name.lower():
        name = name.capitalize()
    return name


class Dropdown(discord.ui.Select):

    def __init__(self, ctx, options, placeholder="Choose a Category for Help", row=None):
        super().__init__(placeholder=placeholder,
                         min_values=1,
                         max_values=1,
                         options=options,
                         row=row)
        self.invoker = ctx.author

    async def callback(self, interaction: discord.Interaction):
        if self.invoker == interaction.user:
            index = self.view.find_index_from_select(self.values[0])
            if not index:
                index = 0
            await self.view.set_page(index, interaction)
        else:
            await interaction.response.send_message(
                "You must run this command to interact with it.", ephemeral=True)


class View(discord.ui.View):

    def __init__(self, mapping: dict, ctx: discord.ext.commands.context.Context, homeembed: discord.embeds.Embed, ui: int):
        super().__init__(timeout=None)
        self.mapping, self.ctx, self.home = mapping, ctx, homeembed
        self.index, self.buttons = 0, None
        self.current_page = 0

        self.options, self.embeds, self.total_pages = self.gen_embeds()

        if ui == 0:
            self.add_item(Dropdown(ctx=self.ctx, options=self.options))
        elif ui == 1:
            self.buttons = self.add_buttons()
        elif ui == 2:
            self.buttons = self.add_buttons()
            mid_point = len(self.options) // 2
            options_1 = self.options[:mid_point]
            options_2 = self.options[mid_point:]

            if options_1:
                self.add_item(Dropdown(ctx=self.ctx, options=options_1, placeholder="Main Commands", row=1))
            if options_2:
                self.add_item(Dropdown(ctx=self.ctx, options=options_2, placeholder="Extra Commands", row=2))
        else:
            self.buttons = self.add_buttons()
            self.add_item(Dropdown(ctx=self.ctx, options=self.options))

    def add_buttons(self):
        self.homeB = discord.ui.Button(label="Home", style=discord.ButtonStyle.secondary)
        self.homeB.callback = self.home_callback

        self.backB = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary)
        self.backB.callback = self.back_callback

        self.quitB = discord.ui.Button(label="Close", style=discord.ButtonStyle.danger)
        self.quitB.callback = self.quit_callback

        self.nextB = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary)
        self.nextB.callback = self.next_callback

        self.lastB = discord.ui.Button(label="Last", style=discord.ButtonStyle.secondary)
        self.lastB.callback = self.last_callback

        buttons = [self.homeB, self.backB, self.quitB, self.nextB, self.lastB]
        for button in buttons:
            self.add_item(button)
        return buttons

    async def home_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You must run this command to interact with it.", ephemeral=True)
            return
        await self.set_page(0, interaction)

    async def back_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You must run this command to interact with it.", ephemeral=True)
            return
        current_page = self.index - 1 if self.index > 0 else len(self.embeds) - 1
        await self.set_page(current_page, interaction)

    async def quit_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You must run this command to interact with it.", ephemeral=True)
            return
        await self.quit(interaction)

    async def next_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You must run this command to interact with it.", ephemeral=True)
            return
        current_page = self.index + 1 if self.index < len(self.embeds) - 1 else 0
        await self.set_page(current_page, interaction)

    async def last_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You must run this command to interact with it.", ephemeral=True)
            return
        await self.set_page(len(self.embeds) - 1, interaction)

    def find_index_from_select(self, value):
        i = 0
        used_labels = set()
        for cog in self.get_cogs():
            if cog is None or cog.__class__.__name__ == "Roleplay" or self._is_shadow_cog(cog):
                continue
            if not list(cog.get_commands()):
                continue
            if "help_custom" in dir(cog):
                _, label, _ = cog.help_custom()
            else:
                label = _prettify_cog_name(cog.qualified_name)
            original_label = label
            counter = 1
            while label in used_labels:
                label = f"{original_label} {counter}"
                counter += 1
            used_labels.add(label)
            if label == value or value.startswith(original_label + " "):
                return i + 1
            i += 1
        return 0

    def get_cogs(self):
        return list(self.mapping.keys())

    def _is_shadow_cog(self, cog) -> bool:
        """The cogs.zyrox package holds lightweight metadata-only cogs (one dummy
        command each, used only to supply an emoji/label/description for the old
        help system). They shouldn't show up as their own category now that labels
        are derived automatically - real commands live in the matching real cog."""
        module = type(cog).__module__ or ""
        return module.startswith("cogs.zyrox") or module.startswith(".zyrox")

    def gen_embeds(self):
        options, embeds = [], []
        total_pages = 0
        used_labels = set()

        options.append(discord.SelectOption(label="Home", description=""))
        embeds.append(self.home)
        total_pages += 1
        used_labels.add("Home")

        for cog in self.get_cogs():
            if cog is None or cog.__class__.__name__ == "Roleplay" or self._is_shadow_cog(cog):
                continue
            commands_list = list(cog.get_commands())
            if not commands_list:
                continue

            if "help_custom" in dir(cog):
                _, label, description = cog.help_custom()
            else:
                label = _prettify_cog_name(cog.qualified_name)
                description = (cog.description or "").strip() or f"{label} commands"

            original_label = label
            counter = 1
            while label in used_labels:
                label = f"{original_label} {counter}"
                counter += 1
            used_labels.add(label)

            options.append(discord.SelectOption(label=label, description=description))
            embed = discord.Embed(title=f"{original_label}", color=0xFFFFFF)

            for command in commands_list:
                params = ""
                for param in command.clean_params:
                    if param not in ["self", "ctx"]:
                        params += f" <{param}>"
                help_text = command.help or "No description available"
                if len(help_text) > 1020:
                    help_text = help_text[:1017] + "..."
                embed.add_field(name=f"{command.name}{params}",
                                value=f"{help_text}\n•",
                                inline=False)
            embeds.append(embed)
            total_pages += 1

        self.home.set_footer(text=f"• Help page 1/{total_pages} | Requested by: {self.ctx.author.display_name}",
                             icon_url=f"{self.ctx.bot.user.avatar.url}")
        return options, embeds, total_pages

    async def quit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.delete_original_response()

    async def to_page(self, page: int, interaction: discord.Interaction):
        if not self.index + page < 0 or not self.index + page > len(self.options):
            await self.set_index(page)
            embed = self.embeds[self.index]
            embed.set_footer(text=f"• Help page {self.index + 1}/{self.total_pages} | Requested by: {self.ctx.author.display_name}",
                             icon_url=f"{self.ctx.bot.user.avatar.url}")
            await interaction.response.edit_message(embed=embed, view=self)

    async def set_page(self, page: int, interaction: discord.Interaction):
        self.index = page
        self.current_page = page
        await self.to_page(0, interaction)

    async def set_index(self, page):
        self.index += page
        if self.buttons:
            self.homeB.disabled = (self.index == 0)
            self.backB.disabled = (self.index == 0)
            self.nextB.disabled = (self.index == len(self.options) - 1)
            self.lastB.disabled = (self.index == len(self.options) - 1)

    async def set_last_page(self, interaction: discord.Interaction):
        await self.set_page(len(self.options) - 1, interaction)