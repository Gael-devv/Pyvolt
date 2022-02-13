from __future__ import annotations

import asyncio
from collections import deque, OrderedDict
import copy
import datetime
from typing import Dict, Optional, TYPE_CHECKING, Union, Callable, Any, List, TypeVar, Coroutine, Sequence, Tuple, Deque    
import inspect

if TYPE_CHECKING:
    from .http import HTTPClient
    from .client import Client


class State: 
    if TYPE_CHECKING:
        _get_websocket: Callable[...] # Callable[..., RevoltWebSocketManager]
        _get_client: Callable[..., Client]
        _parsers: Dict[str, Callable[[Dict[str, Any]], None]]
        
    def __init__(
        self,
        *,
        http: HTTPClient,
        dispatch: Callable,
        loop: asyncio.AbstractEventLoop,
        handlers: Dict[str, Callable],
        **options: Any,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self.http: HTTPClient = http
        self.max_messages: Optional[int] = options.get("max_messages", 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.dispatch: Callable = dispatch
        self.handlers: Dict[str, Callable] = handlers
        self._ready_task: Optional[asyncio.Task] = None
        self.heartbeat_timeout: float = options.get("heartbeat_timeout", 60.0)

        self._status: Optional[str] = options.get("status", None)

        # are the functions that the websocket calls for the events
        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func
                
        self.clear()

    def clear(self) -> None: 
        self.user = None # ClientUser
        
        self._users: Dict = {} # str, User
        self._channels: Dict = {} # str, Channel
        self._servers: Dict = {} # str, Server

        if self.max_messages is not None:
            self._messages = deque(maxlen=self.max_messages) # Optional[Deque[Message]]
        else:
            self._messages = None
            
    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)