"""Telegram userbot version of the Stranger Things Farewell experience."""
from __future__ import annotations

import os
from typing import Iterable, List, Set

from telethon import TelegramClient, events

from stranger_things.dialogue import StrangerThingsFarewell


class StrangerThingsFarewellUserbot:
    """Wraps the shared dialogue logic for a plain Telethon userbot."""

    def __init__(self, client: TelegramClient) -> None:
        self._dialogue = StrangerThingsFarewell()
        self._skip_ids: Set[int] = set()

        client.add_event_handler(self._start_handler, events.NewMessage(pattern=r"^\.strange$", outgoing=True))
        client.add_event_handler(self._stop_handler, events.NewMessage(pattern=r"^\.stop$", outgoing=True))
        client.add_event_handler(self._dialogue_handler, events.NewMessage())

    async def _send_responses(self, event, responses: Iterable[str]) -> None:
        for text in responses:
            sent = await event.respond(text)
            if sent is not None:
                self._skip_ids.add(sent.id)

    async def _start_handler(self, event) -> None:
        responses = self._dialogue.start(event.chat_id)
        await self._send_responses(event, responses)

    async def _stop_handler(self, event) -> None:
        responses = self._dialogue.stop(event.chat_id)
        await self._send_responses(event, responses)

    async def _dialogue_handler(self, event) -> None:
        message = event.message
        text = message.raw_text or ""

        if message.id in self._skip_ids:
            self._skip_ids.discard(message.id)
            return

        if text.startswith('.'):
            return

        responses: List[str] = self._dialogue.handle_message(event.chat_id, text)
        if responses:
            await self._send_responses(event, responses)


def run_bot() -> None:
    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    session = os.environ.get("TG_SESSION", "stranger_things_farewell")

    if not api_id or not api_hash:
        raise RuntimeError("Set TG_API_ID and TG_API_HASH environment variables to run the userbot.")

    client = TelegramClient(session, int(api_id), api_hash)
    StrangerThingsFarewellUserbot(client)

    print("Stranger Things Farewell userbot запущен. Напиши .strange, чтобы начать воспоминания.")
    with client:
        client.loop.run_until_complete(client.send_message("me", "Stranger Things Farewell готов к работе."))
        client.loop.run_until_complete(client.send_message("me", "Используй команды .strange и .stop."))
        client.run_until_disconnected()


if __name__ == "__main__":
    run_bot()
