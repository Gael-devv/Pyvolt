from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, TypeVar, Optional, Type

if TYPE_CHECKING:
    from .models.abc import Messageable

    from types import TracebackType

    TypingT = TypeVar("TypingT", bound="Typing")

__all__ = (
    "Typing",
)


def _typing_done_callback(fut: asyncio.Future) -> None:
    # just retrieve any exception and call it a day
    try:
        fut.exception()
    except (asyncio.CancelledError, Exception):
        pass


class Typing:
    def __init__(self, messageable: Messageable) -> None:
        self.loop: asyncio.AbstractEventLoop = messageable._cache.loop
        self.messageable: Messageable = messageable

    async def do_typing(self) -> None:
        try:
            channel = self._channel
        except AttributeError:
            channel = await self.messageable._get_channel()

        ws = channel._cache._get_websocket()
        while True:
            await ws.begin_typing(channel.id)
            await asyncio.sleep(5)

    async def end_typing(self) -> None:
        try:
            channel = self._channel
        except AttributeError:
            channel = await self.messageable._get_channel()
        
        ws = channel._cache._get_websocket()
        await ws.end_typing(channel.id)

    def __enter__(self: TypingT) -> TypingT:
        self.task: asyncio.Future = self.loop.create_task(self.do_typing())
        # self.task.add_done_callback(_typing_done_callback)
        return self

    def __exit__(self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.task.cancel()
        self.loop.create_task(self.end_typing())

    async def __aenter__(self: TypingT) -> TypingT:
        self._channel = await self.messageable._get_channel()
        return self.__enter__()

    async def __aexit__(self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.end_typing()
        print("xd?")
