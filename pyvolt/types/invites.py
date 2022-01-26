from typing import TYPE_CHECKING, Literal, TypedDict, Union

if TYPE_CHECKING:
    from .snowflake import Snowflake
    
__all__ = (
    "InviteCreated",
    "GroupInvite",
    "ServerInvite",
    "Invite",
)

class InviteCreated(TypedDict):
    code: str


class BaseInvite(TypedDict):
    _id: Snowflake
    creator: Snowflake
    channel: Snowflake


class GroupInvite(BaseInvite):
    type: Literal["Group"]


class ServerInvite(TypedDict):
    type: Literal["Server"]
    server: str


Invite = Union[ServerInvite, GroupInvite]
