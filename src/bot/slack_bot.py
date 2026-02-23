# src/bot/slack_bot.py
import asyncio

from loguru import logger
from slack_sdk import WebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse


class OpenClawSlack:
    def __init__(self, bot_token, app_token, ai_client, hardware):
        self.bot_token = bot_token
        self.app_token = app_token
        self.ai = ai_client
        self.hardware = hardware

        self.web_client = WebClient(token=bot_token)
        self.socket_client = SocketModeClient(app_token=app_token, web_client=self.web_client)

    async def start(self):
        logger.info("Connecting Slack Socket Mode...")
        self.socket_client.socket_mode_request_listeners.append(self.handle_request)
        await self.socket_client.connect()
        await asyncio.sleep(float("inf"))  # Keep running

    async def handle_request(self, client: SocketModeClient, request: SocketModeRequest):
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

                # Remove mention
                bot_user_id = (await self.web_client.auth_test())["user_id"]
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
