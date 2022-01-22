from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, TypedDict

if TYPE_CHECKING:
    from .file import File

__all__ = (
    "UserRelation",
    "Relation",
    "UserBot",
    "Status",
    "User",
    "UserProfile",
)


Relation = Literal["Blocked", "BlockedOther", "Friend", "Incoming", "None", "Outgoing", "User"]


class UserBot(TypedDict):
    owner: str


class Status(TypedDict, total=False):
    text: str
    presence: Literal["Busy", "Idle", "Invisible", "Online"]


class UserRelation(TypedDict):
    status: Relation
    _id: str


class _OptionalUser(TypedDict, total=False):
    avatar: File
    relations: List[UserRelation]
    badges: int
    status: Status
    relationship: Relation
    online: bool
    flags: int
    bot: UserBot


class User(_OptionalUser):
    _id: str
    username: str


class UserProfile(TypedDict, total=False):
    content: str
    background: File
