from __future__ import annotations

# src/main.py
import asyncio
import os
import signal

from dotenv import load_dotenv
from loguru import logger

from bot.discord_bot import OpenClawDiscord
from bot.slack_bot import OpenClawSlack
from hardware.claw_controller import ClawController
from llm.ollama_client import OllamaClient

load_dotenv()


async def shutdown(loop: asyncio.AbstractEventLoop, signal: signal.Signals | None = None) -> None:
    if signal:
        logger.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


async def main() -> None:
    logger.info("Initializing OpenClaw System...")

    # Hardware Init
    claw = ClawController()
    claw.init_gpio()

    # AI Init
    ai = OllamaClient(
        host=os.getenv("OLLAMA_HOST", "http://ollama:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M"),
    )

    # Check if AI is ready
    if await ai.check_connection():
        logger.info("Connected to local LLM (Ollama)")
    else:
        logger.warning("Could not connect to Ollama. AI features will be limited.")

    # Bots Init
    discord_token = os.getenv("DISCORD_TOKEN")
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_app_token = os.getenv("SLACK_APP_TOKEN")

    discord_bot: OpenClawDiscord | None = None
    slack_bot: OpenClawSlack | None = None

    tasks: list[asyncio.Task[None]] = []

    if discord_token:
        logger.info("Starting Discord Bot...")
        discord_bot = OpenClawDiscord(token=discord_token, ai_client=ai, hardware=claw)
        tasks.append(asyncio.create_task(discord_bot.start()))

    if slack_token and slack_app_token:
        logger.info("Starting Slack Bot (Socket Mode)...")
        slack_bot = OpenClawSlack(
            bot_token=slack_token, app_token=slack_app_token, ai_client=ai, hardware=claw
        )
        tasks.append(asyncio.create_task(slack_bot.start()))

    if not tasks:
        logger.error("No bot tokens provided! Please set DISCORD_TOKEN or SLACK_BOT_TOKEN in .env")
        return

    # Keep alive until signal
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Shutting down services...")
    finally:
        claw.cleanup()
        logger.info("OpenClaw stopped.")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s)))

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
