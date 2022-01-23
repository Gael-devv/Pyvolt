from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict, Union

if TYPE_CHECKING:
    from .snowflake import Snowflake

__all__ = ("File",)


class SizedMetadata(TypedDict):
    type: Literal["Image", "Video"]
    height: int
    width: int


class SimpleMetadata(TypedDict):
    type: Literal["File", "Text", "Audio"]


FileMetadata = Union[SizedMetadata, SimpleMetadata]


class File(TypedDict):
    _id: Snowflake
    tag: str
    size: int
    filename: str
    metadata: FileMetadata
    content_type: str
