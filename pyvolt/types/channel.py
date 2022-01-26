from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Dict, TypedDict, Union

if TYPE_CHECKING:
    from .file import File
    from .snowflake import Snowflake, SnowflakeList

__all__ = (
    "SavedMessages",
    "DMChannel",
    "Group",
    "TextChannel",
    "VoiceChannel",
    "ChannelType",
)


class _NonceChannel(TypedDict, total=False):
    nonce: str


class _BaseChannel(_NonceChannel):
    _id: Snowflake


class SavedMessages(_BaseChannel):
    channel_type: Literal["SavedMessage"]
    user: str


class DMChannel(_BaseChannel):
    channel_type: Literal["DirectMessage"]
    active: bool
    recipients: SnowflakeList
    last_message_id: Snowflake


class _GroupOptional(TypedDict):
    icon: File
    description: str
    permissions: int
    last_message_id: Snowflake
    nsfw: bool


class Group(_BaseChannel, _GroupOptional):
    channel_type: Literal["Group"]
    recipients: SnowflakeList
    name: str
    owner: str


class _TextChannelOptional(TypedDict, total=False):
    icon: File
    description: str
    default_permissions: int
    role_permissions: Dict[str, int]
    nsfw: bool
    last_message_id: Snowflake


class TextChannel(_BaseChannel, _TextChannelOptional):
    channel_type: Literal["TextChannel"]
    server: str
    name: str


class _VoiceChannelOptional(TypedDict, total=False):
    icon: File
    description: str
    default_permissions: int
    role_permissions: Dict[str, int]
    nsfw: bool


class VoiceChannel(_BaseChannel, _VoiceChannelOptional):
    channel_type: Literal["VoiceChannel"]
    server: str
    name: str


ServerChannel = Union[TextChannel, VoiceChannel]
ChannelType = Union[ServerChannel, SavedMessages, DMChannel, Group]
