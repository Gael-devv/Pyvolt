from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, List

if TYPE_CHECKING:
    from .file import File
    from .category import Category
    from .role import Permissions, Role
    from .snowflake import Snowflake, SnowflakeList

__all__ = (
    "Server",
    "BannedUser",
    "Ban",
    "ServerBans",
    "SystemMessagesConfig"
)


class SystemMessagesConfig(TypedDict, total=False):
    user_joined: str
    user_left: str
    user_kicked: str
    user_banned: str


class _ServerOptional(TypedDict, total=False):
    nonce: str
    description: str
    categories: List[Category]
    system_messages: SystemMessagesConfig
    roles: List[Role]
    icon: File
    banner: File
    nsfw: bool


class Server(_ServerOptional):
    _id: Snowflake
    owner: Snowflake
    name: str
    channels: SnowflakeList
    default_permissions: Permissions


class _OptionalBannedUser(TypedDict, total=False):
    avatar: File


class BannedUser(_OptionalBannedUser):
    _id: Snowflake
    username: str


class _OptionalBan(TypedDict, total=False):
    reason: str


class Ban(_OptionalBan):
    _id: Snowflake


class ServerBans(TypedDict):
    users: List[BannedUser]
    bans: List[Ban]
