from __future__ import annotations

import asyncio
from collections import deque, OrderedDict
import copy
import datetime
from typing import Dict, Optional, TYPE_CHECKING, Union, Callable, Any, List, TypeVar, Coroutine, Sequence, Tuple, Deque    
import inspect

from .models.message import Message

if TYPE_CHECKING:
    from .core import Delta, DeltaWebSocket
    from .client import Client


class CacheManager: 
    if TYPE_CHECKING:
        _get_websocket: Callable[..., DeltaWebSocket] 
        _get_client: Callable[..., Client]
        
    def __init__(
        self,
        *,
        api: Delta,
        loop: asyncio.AbstractEventLoop,
        **options: Any,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self.api: Delta = api
        self.max_messages: Optional[int] = options.get("max_messages", 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self._ready_task: Optional[asyncio.Task] = None
                
        self.clear()

    def clear(self) -> None: 
        self.user = None # ClientUser
        
        self._users: Dict = {} # str, User
        self._channels: Dict = {} # str, Channel
        self._servers: Dict = {} # str, Server

        if self.max_messages is not None:
            self._messages: Optional[Deque[Message]] = deque(maxlen=self.max_messages) 
        else:
            self._messages = None
