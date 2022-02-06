from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from .snowflake import Snowflake
    from .file import File
    
__all__ = (
    "InviteCreated",
    "Invite",
    "PartialInvite"
)


class InviteCreated(TypedDict):
    code: str


class _InviteOptional(TypedDict, total=False):
    server_icon: File
    server_banner: File
    channel_description: str
    user_avatar: File


class Invite(_InviteOptional):
    type: Literal["Server"]
    server_id: Snowflake
    server_name: str
    channel_id: Snowflake
    channel_name: str
    user_name: str
    member_count: int


class PartialInvite(TypedDict):
    type: Literal["Server"]
    _id: Snowflake
    server: Snowflake
    channel: Snowflake
    creator: Snowflake
