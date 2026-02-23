from __future__ import annotations

# src/bot/discord_bot.py
import discord
from discord.ext import commands
from loguru import logger

from hardware.claw_controller import ClawController
from llm.ollama_client import OllamaClient


class ClawCommands(commands.Cog):
    def __init__(self, hardware: ClawController, ai_client: OllamaClient) -> None:
        self.hardware = hardware
        self.ai = ai_client

    @commands.command(name="status")
    async def claw_status(self, ctx: commands.Context) -> None:
        status = self.hardware.get_status()
        await ctx.send(f"Status: {status}")

    @commands.command(name="open")
    async def claw_open(self, ctx: commands.Context) -> None:
        result = self.hardware.open_claw()
        await ctx.send(result)

    @commands.command(name="close")
    async def claw_close(self, ctx: commands.Context) -> None:
        result = self.hardware.close_claw()
        await ctx.send(result)


class OpenClawDiscord(commands.Bot):
    def __init__(self, token: str, ai_client: OllamaClient, hardware: ClawController) -> None:
        self.token = token
        self.ai = ai_client
        self.hardware = hardware

        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!claw ", intents=intents)

    async def setup_hook(self) -> None:
        await self.add_cog(ClawCommands(hardware=self.hardware, ai_client=self.ai))

    async def on_ready(self) -> None:
        logger.info(f"Discord Bot connected as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return

        # Check if the message is a direct message or mentions the bot
        if isinstance(message.channel, discord.DMChannel) or self.user in message.mentions:
            query = message.content.replace(f"<@{self.user.id}>", "").strip()
            if not query:
                await super().on_message(message)
                return

            await message.channel.send("Thinking...")

            # Simple RAG or direct LLM call
            response = await self.ai.chat(query)
            await message.channel.send(response)
            return

        await super().on_message(message)

    async def start(self) -> None:
        await super().start(self.token)
