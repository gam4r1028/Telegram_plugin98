"""ExteraGram plugin for the Stranger Things Farewell experience."""
from __future__ import annotations

from typing import Iterable, List, Set

from .. import loader  # type: ignore

from stranger_things.dialogue import StrangerThingsFarewell


class StrangerThingsFarewellMod(loader.Module):
    """Ностальгический проводник по Stranger Things."""

    strings = {"name": "StrangerThingsFarewell"}

    def __init__(self) -> None:
        self._dialogue = StrangerThingsFarewell()
        self._skip_message_ids: Set[int] = set()

    async def _send_responses(self, message, responses: Iterable[str]) -> None:
        client = message.client
        for text in responses:
            sent = await client.send_message(message.chat_id, text)
            if sent is not None:
                self._skip_message_ids.add(sent.id)

    @loader.command()
    async def strange(self, message) -> None:
        """Запустить прогулку по воспоминаниям Stranger Things."""

        responses = self._dialogue.start(message.chat_id)
        await self._send_responses(message, responses)

    @loader.command()
    async def stop(self, message) -> None:
        """Остановить беседу и обнулить состояние."""

        responses = self._dialogue.stop(message.chat_id)
        await self._send_responses(message, responses)

    async def watcher(self, message) -> None:  # type: ignore
        text = getattr(message, "raw_text", None)
        if not text:
            return

        if message.id in self._skip_message_ids:
            self._skip_message_ids.discard(message.id)
            return

        if text.startswith("."):
            return

        responses: List[str] = self._dialogue.handle_message(message.chat_id, text)
        if responses:
            await self._send_responses(message, responses)
