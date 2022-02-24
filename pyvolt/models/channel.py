from __future__ import annotations

import time
import asyncio
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)
import datetime

from . import abc
from .permissions import ChannelPermissions
from ..enums import ChannelType
from .mixins import Hashable
from .. import utils
from ..utils import MISSING
from .asset import Asset
from ..errors import ClientException, InvalidArgument

__all__ = ()

if TYPE_CHECKING:
    from .role import Role
    from .message import Message
    from ..cache import CacheManager
    from ..types.channel import (
        SavedMessages as SavedMessagesPayload,
        DMChannel as DMChannelPayload,
        GroupChannel as GroupChannelPayload,
        TextChannel as TextChannelPayload,
        VoiceChannel as VoiceChannelPayload,
        ChannelType as ChannelTypePayload
    )
    from ..types.snowflake import SnowflakeList


class SavedMessages(abc.BaseChannel, abc.Messageable, Hashable):
    """Represents the saved message channel"""
    
    def __init__(self, data: SavedMessagesPayload, *, cache: CacheManager) -> None:
        self._cache = cache
        
        self.id = data["_id"]
        self.type = ChannelType(data["channel_type"])
        assert self.type == ChannelType.saved_message
        
        self._data = data
        

class DMChannel(abc.BaseChannel, abc.Messageable, Hashable): 
    """Represents a direct message channel"""
    
    def __init__(self, data: DMChannelPayload, *, cache: CacheManager) -> None:
        self._cache = cache
        
        self.id = data["_id"]
        self.type = ChannelType(data["channel_type"])
        assert self.type == ChannelType.direct_message
        
        self._data = data
        
    @property
    def active(self) -> bool:
        return self._data["active"]
    
    @property
    def recipients(self) -> List:
        return [self._cache.get_user(user_id) for user_id in self._data["recipients"]]
    
    @property
    def last_message(self) -> Optional[Message]:
        return self._cache.get_message(self._data["last_message_id"])
    
    @property
    def last_message_id(self) -> Optional[str]:
        return self._data["last_message_id"]

    
class GroupChannel(abc.EditableChannel, abc.Messageable, Hashable): 
    """Represents a group channel"""
    
    def __init__(self, data: GroupChannelPayload, *, cache: CacheManager) -> None:
        self._cache = cache
        
        self.id = data["_id"]
        self.type = ChannelType(data["channel_type"])
        assert self.type == ChannelType.group
        
        self._data = data
    
    @property
    def owner(self) -> ...:
        return self._cache.get_user(self._data["owner"])
    
    @property
    def recipients(self) -> List:
        return [self._cache.get_user(user_id) for user_id in self._data["recipients"]]
    
    @property
    def last_message(self) -> Optional[Message]:
        return self._cache.get_message(self._data["last_message_id"])
    
    @property
    def last_message_id(self) -> Optional[str]:
        return self._data["last_message_id"]

    @property
    def permissions(self):
        return ChannelPermissions(self._data["permissions"])


class TextChannel(abc.ServerChannel, abc.Messageable, Hashable): 
    """Represents a server text channel"""
    
    def __init__(self, data: TextChannelPayload, *, cache: CacheManager) -> None:
        self._cache = cache
        
        self.id = data["_id"]
        self.type = ChannelType(data["channel_type"])
        assert self.type == ChannelType.text_channel
        
        self.server = cache.get_server(data["server"])
        self._data = data
    
    @property
    def last_message(self) -> Optional[Message]:
        return self._cache.get_message(self._data["last_message_id"])
    
    @property
    def last_message_id(self) -> Optional[str]:
        return self._data["last_message_id"]


class VoiceChannel(abc.ServerChannel, Hashable): 
    """Represents a server voice channel"""
    
    def __init__(self, data: VoiceChannelPayload, *, cache: CacheManager) -> None:
        self._cache = cache
        
        self.id = data["_id"]
        self.type = ChannelType(data["channel_type"])
        assert self.type == ChannelType.voice_channel
        
        self.server = cache.get_server(data["server"])
        self._data = data


def _channel_factory(
    data: ChannelTypePayload, cache: CacheManager
) -> Union[SavedMessages, DMChannel, GroupChannel,TextChannel, VoiceChannel]:
    channel_type = ChannelType(data["channel_type"])
    if channel_type == ChannelType.saved_message:
        return SavedMessages(data, cache=cache)
    elif channel_type == ChannelType.direct_message:
        return DMChannel(data, cache=cache)
    elif channel_type == ChannelType.group:
        return GroupChannel(data, cache=cache)
    elif channel_type == ChannelType.text_channel:
        return TextChannel(data, cache=cache)
    elif channel_type == ChannelType.voice_channel:
        return VoiceChannel(data, cache=cache)
    else:
        raise InvalidArgument
