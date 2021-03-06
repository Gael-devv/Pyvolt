"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz
Copyright (c) 2022 Gael

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
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
        self.task.add_done_callback(_typing_done_callback)
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
