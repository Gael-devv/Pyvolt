from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .snowflake import Snowflake, SnowflakeList

__all__ = ("Category",)


class Category(TypedDict):
    id: Snowflake
    title: str
    channels: SnowflakeList
