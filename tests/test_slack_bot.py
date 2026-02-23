from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.slack_bot import OpenClawSlack


@pytest.fixture
def hardware():
    hw = MagicMock()
    hw.open_claw.return_value = "Claw is now OPEN"
    hw.close_claw.return_value = "Claw is now CLOSED"
    return hw


@pytest.fixture
def ai_client():
    ai = MagicMock()
    ai.chat = AsyncMock(return_value="Here is my LLM response.")
    return ai


@pytest.fixture
def slack_bot(hardware, ai_client):
    with (
        patch("bot.slack_bot.WebClient"),
        patch("bot.slack_bot.SocketModeClient"),
    ):
        bot = OpenClawSlack(
            bot_token="xoxb-test",
            app_token="xapp-test",
            ai_client=ai_client,
            hardware=hardware,
        )
    return bot


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_initialization_stores_tokens_and_clients(hardware, ai_client):
    with (
        patch("bot.slack_bot.WebClient") as mock_web,
        patch("bot.slack_bot.SocketModeClient") as mock_socket,
    ):
        bot = OpenClawSlack(
            bot_token="xoxb-test",
            app_token="xapp-test",
            ai_client=ai_client,
            hardware=hardware,
        )

    assert bot.bot_token == "xoxb-test"
    assert bot.app_token == "xapp-test"
    assert bot.ai is ai_client
    assert bot.hardware is hardware
    assert bot._bot_user_id is None
    mock_web.assert_called_once_with(token="xoxb-test")
    mock_socket.assert_called_once()


# ---------------------------------------------------------------------------
# _get_bot_user_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_bot_user_id_fetches_once(slack_bot):
    slack_bot.web_client = MagicMock()
    slack_bot.web_client.auth_test = AsyncMock(return_value={"user_id": "U123"})
    slack_bot._bot_user_id = None

    uid = await slack_bot._get_bot_user_id()
    assert uid == "U123"
    slack_bot.web_client.auth_test.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_bot_user_id_cached(slack_bot):
    slack_bot._bot_user_id = "U999"
    slack_bot.web_client = MagicMock()
    slack_bot.web_client.auth_test = AsyncMock()

    uid = await slack_bot._get_bot_user_id()
    assert uid == "U999"
    slack_bot.web_client.auth_test.assert_not_awaited()


# ---------------------------------------------------------------------------
# handle_request — command parsing
# ---------------------------------------------------------------------------


def _make_request(
    text: str, channel: str = "C1", user: str = "U1", ts: str = "1234.5"
) -> MagicMock:
    req = MagicMock()
    req.type = "events_api"
    req.envelope_id = "env-001"
    req.payload = {
        "event": {
            "type": "app_mention",
            "text": text,
            "channel": channel,
            "user": user,
            "ts": ts,
        }
    }
    return req


@pytest.mark.asyncio
async def test_open_claw_command(slack_bot, hardware):
    slack_bot._bot_user_id = "UBOT"
    slack_bot.web_client = MagicMock()
    slack_bot.web_client.chat_postMessage = AsyncMock()

    client = MagicMock()
    client.send_socket_mode_response = AsyncMock()

    request = _make_request(text="open claw please")

    await slack_bot.handle_request(client, request)

    hardware.open_claw.assert_called_once()
    slack_bot.web_client.chat_postMessage.assert_awaited_once_with(
        channel="C1", text="Claw is now OPEN"
    )
    slack_bot.ai.chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_claw_command(slack_bot, hardware):
    slack_bot._bot_user_id = "UBOT"
    slack_bot.web_client = MagicMock()
    slack_bot.web_client.chat_postMessage = AsyncMock()

    client = MagicMock()
    client.send_socket_mode_response = AsyncMock()

    request = _make_request(text="close claw now")

    await slack_bot.handle_request(client, request)

    hardware.close_claw.assert_called_once()
    slack_bot.web_client.chat_postMessage.assert_awaited_once_with(
        channel="C1", text="Claw is now CLOSED"
    )
    slack_bot.ai.chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_llm_routing_for_non_command(slack_bot, ai_client):
    slack_bot._bot_user_id = "UBOT"
    slack_bot.web_client = MagicMock()
    slack_bot.web_client.chat_postMessage = AsyncMock()
    slack_bot.web_client.reactions_add = AsyncMock()
    slack_bot.web_client.reactions_remove = AsyncMock()

    client = MagicMock()
    client.send_socket_mode_response = AsyncMock()

    request = _make_request(text="What is the meaning of life?")

    await slack_bot.handle_request(client, request)

    ai_client.chat.assert_awaited_once_with("What is the meaning of life?")
    slack_bot.web_client.chat_postMessage.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_prompt_returns_early(slack_bot, ai_client):
    """An empty prompt after stripping the mention must not call ai.chat."""
    slack_bot._bot_user_id = "UBOT"
    slack_bot.web_client = MagicMock()

    client = MagicMock()
    client.send_socket_mode_response = AsyncMock()

    # Text is just the bot mention — stripped prompt will be empty
    request = _make_request(text="<@UBOT>")

    await slack_bot.handle_request(client, request)

    ai_client.chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_events_api_request_ignored(slack_bot, ai_client):
    """Requests that are not events_api type should be ignored."""
    slack_bot._bot_user_id = "UBOT"

    client = MagicMock()
    req = MagicMock()
    req.type = "slash_commands"

    await slack_bot.handle_request(client, req)

    ai_client.chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_im_message_event_type(slack_bot, ai_client):
    """Direct messages (im channel_type) should also trigger LLM routing."""
    slack_bot._bot_user_id = "UBOT"
    slack_bot.web_client = MagicMock()
    slack_bot.web_client.chat_postMessage = AsyncMock()
    slack_bot.web_client.reactions_add = AsyncMock()
    slack_bot.web_client.reactions_remove = AsyncMock()

    client = MagicMock()
    client.send_socket_mode_response = AsyncMock()

    req = MagicMock()
    req.type = "events_api"
    req.envelope_id = "env-002"
    req.payload = {
        "event": {
            "type": "message",
            "channel_type": "im",
            "text": "Hello there",
            "channel": "D1",
            "user": "U2",
            "ts": "5678.9",
        }
    }

    await slack_bot.handle_request(client, req)

    ai_client.chat.assert_awaited_once_with("Hello there")


@pytest.mark.asyncio
async def test_reactions_added_and_removed_around_llm_call(slack_bot, ai_client):
    """Thinking reaction should be added before and removed after LLM call."""
    slack_bot._bot_user_id = "UBOT"
    slack_bot.web_client = MagicMock()
    slack_bot.web_client.chat_postMessage = AsyncMock()
    slack_bot.web_client.reactions_add = AsyncMock()
    slack_bot.web_client.reactions_remove = AsyncMock()

    client = MagicMock()
    client.send_socket_mode_response = AsyncMock()

    request = _make_request(text="Tell me something", ts="1111.0")

    await slack_bot.handle_request(client, request)

    slack_bot.web_client.reactions_add.assert_awaited_once_with(
        channel="C1", timestamp="1111.0", name="thinking_face"
    )
    slack_bot.web_client.reactions_remove.assert_awaited_once_with(
        channel="C1", timestamp="1111.0", name="thinking_face"
    )
