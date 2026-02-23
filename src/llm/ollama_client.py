from __future__ import annotations

# src/llm/ollama_client.py
from urllib.parse import urlparse

import aiohttp
from loguru import logger

_ALLOWED_SCHEMES = {"http", "https"}


def _validate_ollama_host(host: str) -> str:
    """Reject dangerous OLLAMA_HOST values (SSRF guard).

    Only http/https schemes are permitted. Blocks file://, ftp://, etc.
    Internal/private addresses are fine — Ollama is always local.
    """
    parsed = urlparse(host)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"OLLAMA_HOST has disallowed scheme '{parsed.scheme}'. "
            "Only 'http' and 'https' are permitted."
        )
    return host


class OllamaClient:
    def __init__(self, host: str, model: str) -> None:
        self.host = _validate_ollama_host(host)
        self.model = model
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> OllamaClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def check_connection(self) -> bool:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        try:
            async with self.session.get(f"{self.host}/api/tags") as resp:
                if resp.status == 200:
                    return True
        except Exception as e:
            logger.error(f"Could not connect to Ollama at {self.host}: {e}")
        return False

    async def chat(self, prompt: str, context: object | None = None) -> str:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        # Simple completion endpoint, or chat depending on version
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        try:
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "I have no words.")
                else:
                    logger.error(f"Ollama error: {resp.status} - {await resp.text()}")
                    return "Sorry, my brain is offline."
        except Exception:
            logger.exception("LLM Request Failed")
            return "I encountered a neural error."
