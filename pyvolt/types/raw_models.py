from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

from .channel import (ChannelType, DMChannel, Group, SavedMessages,
                      TextChannel, VoiceChannel)
from .message import Message

if TYPE_CHECKING:
    from .member import Member, MemberID
    from .server import Server
    from .user import Status, User
    
    from .snowflake import Snowflake

__all__ = (
    "Base",
    "Authenticate",
    "ReadyEvent",
    "MessageEvent",
    "MessageUpdateEditedData",
    "MessageUpdateData",
    "MessageUpdateEvent",
    "MessageDeleteEvent",
    "ChannelCreateEvent",
    "ChannelUpdateEvent",
    "ChannelDeleteEvent",
    "ChannelStartTypingEvent",
    "ChannelDeleteTypingEvent",
    "ServerUpdateEvent",
    "ServerDeleteEvent",
    "ServerMemberUpdateEvent",
    "ServerMemberJoinEvent",
    "ServerMemberLeaveEvent",
    "ServerRoleUpdateEvent",
    "ServerRoleDeleteEvent",
    "UserUpdateEvent",
    "UserRelationshipEvent"
)


class Base(TypedDict):
    type: str


class Authenticate(Base):
    token: str


class ReadyEvent(Base):
    users: list[User]
    servers: list[Server]
    channels: list[ChannelType]
    members: list[Member]


class MessageEvent(Base, Message):
    pass


MessageUpdateEditedData = TypedDict("MessageUpdateEditedData", {"$date": str})


class MessageUpdateData(TypedDict):
    content: str
    edited: MessageUpdateEditedData


class MessageUpdateEvent(Base):
    channel: Snowflake
    data: MessageUpdateData
    id: Snowflake


class MessageDeleteEvent(Base):
    channel: Snowflake
    id: Snowflake


class ChannelCreateEvent_SavedMessages(Base, SavedMessages):
    pass


class ChannelCreateEvent_Group(Base, Group):
    pass


class ChannelCreateEvent_TextChannel(Base, TextChannel):
    pass


class ChannelCreateEvent_VoiceChannel(Base, VoiceChannel):
    pass


class ChannelCreateEvent_DMChannel(Base, DMChannel):
    pass


ChannelCreateEvent = Union[ChannelCreateEvent_Group, ChannelCreateEvent_Group, ChannelCreateEvent_TextChannel, 
                           ChannelCreateEvent_VoiceChannel, ChannelCreateEvent_DMChannel]


class ChannelUpdateEvent(Base):
    id: Snowflake
    data: ...
    clear: Literal["Icon", "Description"]


class ChannelDeleteEvent(Base):
    id: Snowflake


class ChannelStartTypingEvent(Base):
    id: Snowflake
    user: Snowflake


ChannelDeleteTypingEvent = ChannelStartTypingEvent


class ServerUpdateEvent(Base):
    id: Snowflake
    data: dict
    clear: Literal["Icon", "Banner", "Description"]


class ServerDeleteEvent(Base):
    id: Snowflake


class ServerMemberUpdateEvent(Base):
    id: MemberID
    data: dict
    clear: Literal["Nickname", "Avatar"]


class ServerMemberJoinEvent(Base):
    id: Snowflake
    user: Snowflake


ServerMemberLeaveEvent = ServerMemberJoinEvent


class ServerRoleUpdateEvent(Base):
    id: Snowflake
    role_id: Snowflake
    data: dict
    clear: Literal["Color"]


class ServerRoleDeleteEvent(Base):
    id: Snowflake
    role_id: Snowflake


class UserUpdateEvent(Base):
    id: str
    data: dict
    clear: Literal["ProfileContent", "ProfileBackground", "StatusText", "Avatar"]


class UserRelationshipEvent(Base):
    id: str
    user: str
    status: Status
