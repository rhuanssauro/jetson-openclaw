from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot.discord_bot import ClawCommands, OpenClawDiscord


@pytest.fixture
def hardware():
    hw = MagicMock()
    hw.get_status.return_value = "OPEN"
    hw.open_claw.return_value = "Claw is now OPEN"
    hw.close_claw.return_value = "Claw is now CLOSED"
    return hw


@pytest.fixture
def ai_client():
    ai = MagicMock()
    ai.chat = AsyncMock(return_value="I am alive.")
    return ai


@pytest.fixture
def cog(hardware, ai_client):
    return ClawCommands(hardware=hardware, ai_client=ai_client)


def _make_ctx(send_mock: AsyncMock | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.send = send_mock or AsyncMock()
    return ctx


def _make_bot(hardware: object, ai_client: object) -> OpenClawDiscord:
    """Create an OpenClawDiscord instance without starting Discord internals."""
    with patch("discord.ext.commands.Bot.__init__", return_value=None):
        bot = OpenClawDiscord.__new__(OpenClawDiscord)
        bot.token = "tok"
        bot.ai = ai_client
        bot.hardware = hardware
        # Inject _user via the internal attribute discord.py reads through the property
        bot._connection = MagicMock()
        bot._connection.user = MagicMock(spec=discord.ClientUser)
        bot._connection.user.id = 99
    return bot


# ---------------------------------------------------------------------------
# ClawCommands cog tests
# ---------------------------------------------------------------------------


def test_cog_stores_hardware_and_ai(hardware, ai_client):
    cog = ClawCommands(hardware=hardware, ai_client=ai_client)
    assert cog.hardware is hardware
    assert cog.ai is ai_client


@pytest.mark.asyncio
async def test_claw_status_sends_hardware_status(cog, hardware):
    ctx = _make_ctx()
    # Invoke the underlying callback directly to bypass Command descriptor
    await cog.claw_status.callback(cog, ctx)
    hardware.get_status.assert_called_once()
    ctx.send.assert_awaited_once_with("Status: OPEN")


@pytest.mark.asyncio
async def test_claw_open_triggers_hardware_open(cog, hardware):
    ctx = _make_ctx()
    await cog.claw_open.callback(cog, ctx)
    hardware.open_claw.assert_called_once()
    ctx.send.assert_awaited_once_with("Claw is now OPEN")


@pytest.mark.asyncio
async def test_claw_close_triggers_hardware_close(cog, hardware):
    ctx = _make_ctx()
    await cog.claw_close.callback(cog, ctx)
    hardware.close_claw.assert_called_once()
    ctx.send.assert_awaited_once_with("Claw is now CLOSED")


# ---------------------------------------------------------------------------
# OpenClawDiscord bot tests
# ---------------------------------------------------------------------------


def test_bot_stores_token_ai_and_hardware(hardware, ai_client):
    bot = _make_bot(hardware, ai_client)
    assert bot.token == "tok"
    assert bot.ai is ai_client
    assert bot.hardware is hardware


@pytest.mark.asyncio
async def test_on_message_ignores_own_messages(hardware, ai_client):
    """Bot must not respond to its own messages."""
    bot = _make_bot(hardware, ai_client)
    bot_user = bot._connection.user

    message = MagicMock(spec=discord.Message)
    message.author = bot_user  # Same as bot user

    await bot.on_message(message)

    ai_client.chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_message_dm_calls_ai_and_replies(hardware, ai_client):
    """DM messages should trigger an LLM call and send the response."""
    bot = _make_bot(hardware, ai_client)

    channel = MagicMock(spec=discord.DMChannel)
    channel.send = AsyncMock()

    message = MagicMock(spec=discord.Message)
    message.author = MagicMock()  # Different from bot
    message.channel = channel
    message.content = "Hello bot"
    message.mentions = []

    await bot.on_message(message)

    ai_client.chat.assert_awaited_once_with("Hello bot")
    channel.send.assert_any_await("I am alive.")


@pytest.mark.asyncio
async def test_on_message_mention_calls_ai(hardware, ai_client):
    """Messages that mention the bot should trigger an LLM call."""
    bot = _make_bot(hardware, ai_client)
    bot_user = bot._connection.user

    channel = MagicMock()
    channel.send = AsyncMock()

    message = MagicMock(spec=discord.Message)
    message.author = MagicMock()
    message.channel = channel
    message.content = "<@99> what is up?"
    message.mentions = [bot_user]

    await bot.on_message(message)

    ai_client.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_message_empty_mention_falls_through(hardware, ai_client):
    """An empty mention (just @bot with no text) should not call ai.chat."""
    bot = _make_bot(hardware, ai_client)
    bot_user = bot._connection.user

    channel = MagicMock()

    message = MagicMock(spec=discord.Message)
    message.author = MagicMock()
    message.channel = channel
    message.content = "<@99>"
    message.mentions = [bot_user]

    with patch.object(discord.ext.commands.Bot, "on_message", new=AsyncMock()):
        await bot.on_message(message)

    ai_client.chat.assert_not_awaited()
