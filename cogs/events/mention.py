from utils import getConfig
import discord
from discord.ext import commands
from utils.Tools import get_ignore_data
import aiosqlite

class MentionDropdown(discord.ui.Select):
    def __init__(self, message: discord.Message, bot: commands.Bot, prefix: str):
        self.message = message
        self.bot = bot
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Home", description="Go to the main menu"),
            discord.SelectOption(label="Developer Info", description="See who owns this bot"),
            discord.SelectOption(label="Links", description="Useful bot links"),
        ]
        super().__init__(placeholder="Start With SALVATION", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.message.author.id:
            return await interaction.response.send_message("This menu is not for you!", ephemeral=True)

        embed = discord.Embed(color=0xFFFFFF)
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        if self.values[0] == "Home":
            embed.title = f"{self.message.guild.name}"
            embed.description = (
                f"**Hey {interaction.user.mention}**\n"
                f"**Prefix For This Server: `{self.prefix}`**\n\n"
                f"___Type `{self.prefix}help` for more information.___"
            )
        elif self.values[0] == "Developer Info":
            embed.title = "Developer"
            owner_ids = list(self.bot.owner_ids) if self.bot.owner_ids else ([self.bot.owner_id] if self.bot.owner_id else [])
            if owner_ids:
                owners = "\n".join(f"**[{i+1:02d}]. <@{oid}>**" for i, oid in enumerate(owner_ids))
                embed.description = f"This bot is privately owned and operated.\n\n**Owner{'s' if len(owner_ids) > 1 else ''}**\n{owners}"
            else:
                embed.description = "This bot is privately owned and operated."
        elif self.values[0] == "Links":
            embed.title = "Important Links"
            embed.description = (
                f"**[Invite SALVATION](https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands)**\n"
                "**Support Server:** *ask your server admin*"
            )

        embed.set_footer(text="Powered by SALVATION", icon_url=self.bot.user.avatar.url)
        await interaction.response.edit_message(embed=embed, view=self.view)

class MentionView(discord.ui.View):
    def __init__(self, message: discord.Message, bot: commands.Bot, prefix: str):
        super().__init__(timeout=None)
        self.add_item(MentionDropdown(message, bot, prefix))


class Mention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xFFFFFF
        self.bot_name = "SALVATION"

    async def is_blacklisted(self, message):
        async with aiosqlite.connect("db/block.db") as db:
            cursor = await db.execute("SELECT 1 FROM guild_blacklist WHERE guild_id = ?", (message.guild.id,))
            if await cursor.fetchone():
                return True
            cursor = await db.execute("SELECT 1 FROM user_blacklist WHERE user_id = ?", (message.author.id,))
            if await cursor.fetchone():
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if await self.is_blacklisted(message):
            return

        ignore_data = await get_ignore_data(message.guild.id)
        if str(message.author.id) in ignore_data["user"] or str(message.channel.id) in ignore_data["channel"]:
            return

        if self.bot.user in message.mentions and len(message.content.strip().split()) == 1:
            guild_id = message.guild.id
            data = await getConfig(guild_id)
            prefix = data["prefix"]

            embed = discord.Embed(
                title=f"{message.guild.name}",
                description=f"**Hey {message.author.mention}**\n"
                            f"**Prefix For This Server: `{prefix}`**\n\n"
                            f"___Type `{prefix}help` for more information.___",
                color=self.color
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(text="Powered by SALVATION", icon_url=self.bot.user.avatar.url)

            view = MentionView(message, self.bot, prefix)
            await message.channel.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Mention(bot))
