from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm.ollama_client import OllamaClient


@pytest.fixture
def client():
    return OllamaClient(host="http://localhost:11434", model="llama3")


@pytest.mark.asyncio
async def test_check_connection_success(client):
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(return_value=mock_resp)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client.session = None
        result = await client.check_connection()

    assert result is True


@pytest.mark.asyncio
async def test_check_connection_failure_non_200(client):
    mock_resp = AsyncMock()
    mock_resp.status = 500
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(return_value=mock_resp)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client.session = None
        result = await client.check_connection()

    assert result is False


@pytest.mark.asyncio
async def test_check_connection_failure_exception(client):
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(side_effect=Exception("Connection refused"))

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client.session = None
        result = await client.check_connection()

    assert result is False


@pytest.mark.asyncio
async def test_chat_returns_llm_response(client):
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"response": "Hello from Ollama!"})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.post = MagicMock(return_value=mock_resp)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client.session = None
        result = await client.chat("Say hello")

    assert result == "Hello from Ollama!"


@pytest.mark.asyncio
async def test_chat_handles_ollama_error_status(client):
    mock_resp = AsyncMock()
    mock_resp.status = 503
    mock_resp.text = AsyncMock(return_value="Service unavailable")
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.post = MagicMock(return_value=mock_resp)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client.session = None
        result = await client.chat("Say hello")

    assert result == "Sorry, my brain is offline."


@pytest.mark.asyncio
async def test_chat_handles_exception(client):
    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.post = MagicMock(side_effect=Exception("Network error"))

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client.session = None
        result = await client.chat("Say hello")

    assert result == "I encountered a neural error."


@pytest.mark.asyncio
async def test_chat_missing_response_key(client):
    """When 'response' key is absent, default fallback text is returned."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={})
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.post = MagicMock(return_value=mock_resp)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        client.session = None
        result = await client.chat("test")

    assert result == "I have no words."


@pytest.mark.asyncio
async def test_session_created_lazily(client):
    """Session should be None until first network call."""
    assert client.session is None

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(return_value=mock_resp)

    with patch("aiohttp.ClientSession", return_value=mock_session) as mock_cls:
        await client.check_connection()
        mock_cls.assert_called_once()


@pytest.mark.asyncio
async def test_session_reused_on_second_call(client):
    """An open session must not be recreated on subsequent calls."""
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.closed = False
    mock_session.get = MagicMock(return_value=mock_resp)

    with patch("aiohttp.ClientSession", return_value=mock_session) as mock_cls:
        client.session = None
        await client.check_connection()
        await client.check_connection()
        # ClientSession constructor should only be called once
        assert mock_cls.call_count == 1


@pytest.mark.asyncio
async def test_close_closes_open_session(client):
    mock_session = AsyncMock()
    mock_session.closed = False
    client.session = mock_session

    await client.close()

    mock_session.close.assert_awaited_once()
    assert client.session is None


@pytest.mark.asyncio
async def test_close_noop_when_already_closed(client):
    mock_session = MagicMock()
    mock_session.closed = True
    client.session = mock_session

    await client.close()

    mock_session.close.assert_not_called()


@pytest.mark.asyncio
async def test_close_noop_when_no_session(client):
    client.session = None
    # Should not raise
    await client.close()


@pytest.mark.asyncio
async def test_async_context_manager():
    """__aenter__ returns the client; __aexit__ calls close()."""
    c = OllamaClient(host="http://localhost:11434", model="llama3")
    mock_session = AsyncMock()
    mock_session.closed = False
    c.session = mock_session

    async with c as entered:
        assert entered is c

    mock_session.close.assert_awaited_once()
