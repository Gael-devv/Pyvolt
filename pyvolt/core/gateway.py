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
import asyncio
from typing import TYPE_CHECKING, Any, Callable
from collections import namedtuple, deque
import concurrent.futures
import sys
import time
import threading
import traceback

import aiohttp

try:
    import ujson as _json
except ImportError:
    import _json

try:
    import msgpack
    use_msgpack = True
except ImportError:
    use_msgpack = False

from .. import utils
from ..errors import ConnectionClosed, InvalidArgument
from ..types.snowflake import Snowflake
from ..types.raw_models import (
    Base as BasePayload,
    ReadyEvent as ReadyEventPayload,
)

__all__ = (
    "DeltaWebSocket",
    "KeepAliveHandler",
    "ReconnectWebSocket",
)


class ReconnectWebSocket(Exception):
    """Signals to safely reconnect the websocket."""
    pass


class WebSocketClosure(Exception):
    """An exception to make up for the fact that aiohttp doesn't signal closure."""
    pass


EventListener = namedtuple("EventListener", "predicate event result future")


class GatewayRatelimiter:
    def __init__(self, count=110, per=60.0):
        # The default is 110 to give room for at least 10 heartbeats per minute
        self.max = count
        self.remaining = count
        self.window = 0.0
        self.per = per
        self.lock = asyncio.Lock()

    def is_ratelimited(self):
        current = time.time()
        if current > self.window + self.per:
            return False
        
        return self.remaining == 0

    def get_delay(self):
        current = time.time()

        if current > self.window + self.per:
            self.remaining = self.max

        if self.remaining == self.max:
            self.window = current

        if self.remaining == 0:
            return self.per - (current - self.window)

        self.remaining -= 1
        if self.remaining == 0:
            self.window = current

        return 0.0

    async def block(self):
        async with self.lock:
            delta = self.get_delay()
            if delta:
                await asyncio.sleep(delta)


class KeepAliveHandler(threading.Thread):
    def __init__(self, *args, **kwargs):
        ws = kwargs.pop("ws", None)
        super().__init__(*args, **kwargs)
        self.ws = ws
        self._main_thread_id = ws.thread_id
        self.interval = 15
        self.daemon = True
        
        self._stop_ev = threading.Event()
        self._last_send = time.perf_counter()
        self._last_recv = time.perf_counter()
        self.heartbeat_timeout = ws._max_heartbeat_timeout

    def run(self):
        while not self._stop_ev.wait(self.interval):
            if self._last_recv + self.heartbeat_timeout < time.perf_counter():
                coro = self.ws.close()
                f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)

                try:
                    f.result()
                except Exception:
                    pass
                finally:
                    self.stop()
                    return

            coro = self.ws.send_heartbeat()
            f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)
            try:
                # block until sending is complete
                while True:
                    try:
                        f.result(10)
                        break
                    except concurrent.futures.TimeoutError:
                        pass
            except Exception:
                self.stop()
            else:
                self._last_send = time.perf_counter()
                
    def stop(self):
        self._stop_ev.set()

    def tick(self):
        self._last_recv = time.perf_counter()


class Handlers: 
    """Set of functions that the websocket calls for events"""
    
    def __init__(self, dispatch: Callable) -> None:
        self.dispatch = dispatch
    
    def ready(self, data: ReadyEventPayload):
        self.dispatch("ready")
    
    def call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        func = getattr(self, name)
        func(*args, **kwargs)


class DeltaWebSocket:
    """Implements a WebSocket for Delta's gateway."""

    def __init__(self, socket, *, loop):
        self.socket: aiohttp.ClientWebSocketResponse = socket
        self.loop = loop

        # an empty dispatcher to prevent crashes
        self._dispatch = lambda *args: None
        # generic event listeners
        self._dispatch_listeners = []
        # handlers
        self._handlers: Handlers = None
        # the keep alive
        self._keep_alive = None
        self.thread_id = threading.get_ident()

        # ws related stuff
        self._close_code = None
        self._rate_limiter = GatewayRatelimiter()

    @property
    def open(self):
        return not self.socket.closed

    def is_ratelimited(self):
        return self._rate_limiter.is_ratelimited()

    @classmethod
    async def from_client(cls, client):
        """Creates a main websocket for Revolt from a :class:`Client`.

        This is for internal use only.
        """
        url = client.api.info["ws"] + "?format=" + "msgpack" if use_msgpack else "json"
        
        socket = await client.api.ws_connect(url)
        ws = cls(socket, loop=client.loop)

        # dynamically add attributes needed
        ws.url = url
        ws.token = client.api.token
        ws.cache = client.cache
        ws._handlers = Handlers(client.dispatch)
        ws._dispatch = client.dispatch
        ws._max_heartbeat_timeout = client.heartbeat_timeout

        await ws.authenticate()

        # poll event for Authenticated
        await ws.poll_event()
        
        return ws

    def wait_for(self, event, predicate, result=None):
        """Waits for a DISPATCH'd event that meets the predicate.

        Parameters
        -----------
        event: :class:`str`
            The event name in all upper case to wait for.
        predicate
            A function that takes a data parameter to check for event
            properties. The data parameter is the 'data' key in the JSON message.
        result
            A function that takes the same data parameter and executes to send
            the result to the future. If ``None``, returns the data.

        Returns
        --------
        asyncio.Future
            A future to wait for.
        """

        future = self.loop.create_future()
        entry = EventListener(event=event, predicate=predicate, result=result, future=future)
        self._dispatch_listeners.append(entry)
        return future

    async def authenticate(self):
        """Sends the Authenticate msg."""
        payload = {
            "type": "Authenticate",
            **self.token.payload
        }

        await self.send_payload(payload)

    async def received_payload(self, data: BasePayload, /):
        event_type = data["type"].lower()
        if event_type:
            self._dispatch("socket_event_type", event_type)

        if self._keep_alive:
            self._keep_alive.tick()

        if event_type == "error":
            raise data["error"]

        if event_type == "authenticated":
            self._keep_alive = KeepAliveHandler(ws=self)
            # send a heartbeat immediately
            await self.send_heartbeat()
            self._keep_alive.start()
            return

        try:
            self._handlers.call(event_type, data)
        except AttributeError:
            pass

        # remove the dispatched listeners
        removed = []
        for index, entry in enumerate(self._dispatch_listeners):
            if entry.event != event_type:
                continue

            future = entry.future
            if future.cancelled():
                removed.append(index)
                continue

            try:
                valid = entry.predicate(data)
            except Exception as exc:
                future.set_exception(exc)
                removed.append(index)
            else:
                if valid:
                    ret = data if entry.result is None else entry.result(data)
                    future.set_result(ret)
                    removed.append(index)

        for index in reversed(removed):
            del self._dispatch_listeners[index]

    def _can_handle_close(self):
        code = self._close_code or self.socket.close_code
        return code not in (1000, 4004, 4010, 4011, 4012, 4013, 4014)

    async def poll_event(self):
        """Polls for a DISPATCH event and handles the general gateway loop.

        Raises
        ------
        ConnectionClosed
            The websocket connection was terminated for unhandled reasons.
        """
        try:
            msg = await self.socket.receive(timeout=self._max_heartbeat_timeout)
            if msg.type is aiohttp.WSMsgType.TEXT:
                await self.received_payload(_json.loads(msg.data))
            elif msg.type is aiohttp.WSMsgType.BINARY:
                await self.received_payload(msgpack.unpackb(msg.data))
            elif msg.type is aiohttp.WSMsgType.ERROR:
                raise msg.data
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSE):
                raise WebSocketClosure
        except (asyncio.TimeoutError, WebSocketClosure) as e:
            # Ensure the keep alive handler is closed
            if self._keep_alive:
                self._keep_alive.stop()
                self._keep_alive = None

            if isinstance(e, asyncio.TimeoutError):
                return

            code = self._close_code or self.socket.close_code
            if self._can_handle_close():
                raise ReconnectWebSocket() from None
            else:
                raise ConnectionClosed(self.socket, code=code) from None

    if use_msgpack:
        async def send_payload(self, payload):
            try:
                await self._rate_limiter.block()
                await self.socket.send_bytes(msgpack.packb(payload)) # type: ignore
            except RuntimeError as exc:
                if not self._can_handle_close():
                    raise ConnectionClosed(self.socket) from exc
    else:
        async def send_payload(self, payload):
            try:
                await self._rate_limiter.block()
                await self.socket.send_str(_json.dumps(payload))
            except RuntimeError as exc:
                if not self._can_handle_close():
                    raise ConnectionClosed(self.socket) from exc

    async def send_heartbeat(self):
        # This bypasses the rate limit handling code since it has a higher priority
        try:
            await self.send_payload({"type": "Ping", "data": 0})
        except RuntimeError as exc:
            if not self._can_handle_close():
                raise ConnectionClosed(self.socket) from exc

    async def begin_typing(self, channel_id: Snowflake):
        payload = {
            "type": "BeginTyping",
            "channel": f"{channel_id}"
        }
        
        await self.send_payload(payload)

    async def end_typing(self, channel_id: Snowflake):
        payload = {
            "type": "EndTyping",
            "channel": f"{channel_id}"
        }
        
        await self.send_payload(payload)

    async def close(self, code=4000):
        if self._keep_alive:
            self._keep_alive.stop()
            self._keep_alive = None

        self._close_code = code
        await self.socket.close(code=code)
