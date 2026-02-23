# src/bot/discord_bot.py
import discord
from discord.ext import commands
from loguru import logger


class OpenClawDiscord(commands.Bot):
    def __init__(self, token, ai_client, hardware):
        self.token = token
        self.ai = ai_client
        self.hardware = hardware

        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!claw ", intents=intents)

    async def on_ready(self):
        logger.info(f"Discord Bot connected as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("!claw"):
            await self.process_commands(message)
            return

        # Check if the message is a direct message or mentions the bot
        if isinstance(message.channel, discord.DMChannel) or self.user in message.mentions:
            query = message.content.replace(f"<@{self.user.id}>", "").strip()
            if not query:
                return

            await message.channel.send("Thinking...")

            # Simple RAG or direct LLM call
            response = await self.ai.chat(query)
            await message.channel.send(response)

    async def start(self):
        await super().start(self.token)

    # Commands
    @commands.command(name="status")
    async def claw_status(self, ctx):
        status = self.hardware.get_status()
        await ctx.send(f"Status: {status}")

    @commands.command(name="open")
    async def claw_open(self, ctx):
        result = self.hardware.open_claw()
        await ctx.send(result)

    @commands.command(name="close")
    async def claw_close(self, ctx):
        result = self.hardware.close_claw()
        await ctx.send(result)
