from __future__ import annotations

# src/bot/slack_bot.py
import asyncio

from loguru import logger
from slack_sdk import WebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from hardware.claw_controller import ClawController
from llm.ollama_client import OllamaClient


class OpenClawSlack:
    def __init__(
        self,
        bot_token: str,
        app_token: str,
        ai_client: OllamaClient,
        hardware: ClawController,
    ) -> None:
        self.bot_token = bot_token
        self.app_token = app_token
        self.ai = ai_client
        self.hardware = hardware

        self.web_client = WebClient(token=bot_token)
        self.socket_client = SocketModeClient(app_token=app_token, web_client=self.web_client)
        self._bot_user_id: str | None = None

    async def _get_bot_user_id(self) -> str:
        if self._bot_user_id is None:
            result = await self.web_client.auth_test()
            self._bot_user_id = result["user_id"]
        return self._bot_user_id

    async def start(self) -> None:
        logger.info("Connecting Slack Socket Mode...")
        # Cache bot_user_id before receiving messages
        await self._get_bot_user_id()
        self.socket_client.socket_mode_request_listeners.append(self.handle_request)
        await self.socket_client.connect()
        await asyncio.sleep(float("inf"))  # Keep running

    async def handle_request(self, client: SocketModeClient, request: SocketModeRequest) -> None:
        if request.type == "events_api":
            # Acknowledge receipt
            response = SocketModeResponse(envelope_id=request.envelope_id)
            await client.send_socket_mode_response(response)

            event = request.payload["event"]
            if event["type"] == "app_mention" or (
                event["type"] == "message" and event.get("channel_type") == "im"
            ):
                text = event.get("text", "")
                channel_id = event["channel"]
                user = event["user"]

                # Remove mention using cached bot_user_id
                bot_user_id = await self._get_bot_user_id()
                prompt = text.replace(f"<@{bot_user_id}>", "").strip()

                if not prompt:
                    return

                # Simple command parsing
                if "open claw" in prompt.lower():
                    msg = self.hardware.open_claw()
                    await self.web_client.chat_postMessage(channel=channel_id, text=msg)
                    return
                elif "close claw" in prompt.lower():
                    msg = self.hardware.close_claw()
                    await self.web_client.chat_postMessage(channel=channel_id, text=msg)
                    return

                # LLM Reply
                await self.web_client.reactions_add(
                    channel=channel_id, timestamp=event["ts"], name="thinking_face"
                )

                reply = await self.ai.chat(prompt)

                await self.web_client.chat_postMessage(
                    channel=channel_id, text=f"<@{user}> {reply}"
                )
                await self.web_client.reactions_remove(
                    channel=channel_id, timestamp=event["ts"], name="thinking_face"
                )
