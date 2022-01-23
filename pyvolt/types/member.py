from __future__ import annotations

from typing import TYPE_CHECKING, List, TypedDict

if TYPE_CHECKING:
    from .file import File
    from .snowflake import Snowflake

__all__ = ("Member",)


class _MemberOptional(TypedDict, total=False):
    nickname: str
    avatar: File
    roles: List[str]


class MemberID(TypedDict):
    server: Snowflake
    user: Snowflake


class Member(_MemberOptional):
    _id: MemberID
