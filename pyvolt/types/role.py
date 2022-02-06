from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Tuple

if TYPE_CHECKING:
    from .snowflake import Snowflake

__all__ = (
    "Permissions",
    "Role",
)


Permissions = Tuple[int, int]


class _RoleOptional(TypedDict, total=False):
    id: Snowflake
    colour: str
    hoist: bool
    rank: int


class Role(_RoleOptional):
    name: str
    permissions: Permissions
