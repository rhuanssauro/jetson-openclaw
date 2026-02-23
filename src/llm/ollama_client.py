# src/llm/ollama_client.py

import aiohttp
from loguru import logger


class OllamaClient:
    def __init__(self, host, model):
        self.host = host
        self.model = model
        self.session = None

    async def check_connection(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.host}/api/tags") as resp:
                    if resp.status == 200:
                        return True
        except Exception as e:
            logger.error(f"Could not connect to Ollama at {self.host}: {e}")
        return False

    async def chat(self, prompt, context=None):
        if not self.session:
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
