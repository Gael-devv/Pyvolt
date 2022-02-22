from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, Optional, Union
import mimetypes

from ..enums import AssetType

if TYPE_CHECKING:
    from ..cache import CacheManager
    from ..types.file import File as FilePayload

__all__ = ("Asset",)


class AssetMixin:
    url: str
    _cache: CacheManager

    id: str
    tag: str
    size: int
    filename: str
    height: Optional[int]
    width: Optional[int]
    content_type: str
    type: AssetType

    async def read(self) -> bytes:
        """Reads the files content into bytes"""
        return await self._cache.api.features.autumn.fetch_file(self.tag, self.id)

    async def save(self, fp: Union[str, bytes, os.PathLike, io.BufferedIOBase]) -> int:
        """Saves this asset into a file-like object."""
        data = await self.read()
        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data)
            return written
        else:
            with open(fp, "wb") as f:
                return f.write(data)


class Asset(AssetMixin):
    """Represents a file on revolt"""
    __slots__ = (
        "_url"
        "_cache", 
        "id", 
        "tag", 
        "size", 
        "filename", 
        "width", 
        "height", 
        "content_type", 
        "type", 
    )
    
    def __init__(self, cache: CacheManager, data: FilePayload):
        self._cache = cache

        self.id = data["_id"]
        self.tag = data["tag"]
        self.size = data["size"]
        self.filename = data["filename"]
        
        metadata = data["metadata"]
        self.content_type = data["content_type"]
        self.type = AssetType(metadata["type"])
        
        if self.type == AssetType.image or self.type == AssetType.video:  # cant use `in` because type narrowing wont happen
            self.height = metadata["height"]
            self.width = metadata["width"]
        else:
            self.height = None
            self.width = None

        self._url = f"{self.tag}/{self.id}"

    def __str__(self) -> str:
        return self.url

    def __len__(self) -> int:
        return len(self._url)

    def __repr__(self):
        return f"<Asset url={self._url!r}>"

    def __eq__(self, other):
        return isinstance(other, Asset) and self._url == other._url

    def __hash__(self):
        return hash(self._url)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the underlying URL of the asset."""
        return self._cache.api.info["features"]["autumn"]["url"] + self._url


class PartialAsset(Asset):
    """Partial asset for when we get limited data about the asset"""

    def __init__(self, cache: CacheManager, url: str):
        self._cache = cache
        
        # something like this should appear: ['https:', '', 'autumn.revolt.chat', 'avatars', 'id']
        simple_data = url.split("/")
        self.id = simple_data[-1]
        self.tag = simple_data[-2]
        
        self.size = 0
        self.filename = ""
        self.height = None
        self.width = None
        self.content_type = mimetypes.guess_extension(url)
        self.type = AssetType.file
        self._url = f"{self.tag}/{self.id}"
