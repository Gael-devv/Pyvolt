from __future__ import annotations

from typing import TYPE_CHECKING, Optional, overload

from ..utils import MISSING
from .permissions import ChannelPermissions, ServerPermissions

if TYPE_CHECKING:
    from .server import Server
    from ..cache import CacheManager
    from ..types.role import Role as RolePayload

__all__ = ("Role",)


class Role:
    """Represents a role in a :class:`Server`"""
    __slots__ = (
        "_cache", 
        "server", 
        "id", 
        "_data"
    )

    def __init__(self, role_id: str, data: RolePayload, *, server: Server, cache: CacheManager):
        self._cache = cache
        self.server = server
        self.id = role_id
        self._data = data

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"

    @property
    def name(self):
        return self._data["name"]

    @property
    def server_permissions(self):
        return ServerPermissions(self._data["permissions"][0])

    @property
    def channel_permissions(self):
        return ChannelPermissions(self._data["permissions"][1])

    @property
    def colour(self):
        return self._data.get("colour", None)

    @property
    def color(self):
        return self.colour

    @property
    def hoist(self):
        return self._data.get("hoist", False)
    
    @property
    def rank(self):
        return self._data["rank"]

    async def set_permissions(self, *, server_permissions: Optional[ServerPermissions] = None, channel_permissions: Optional[ChannelPermissions] = None) -> None:
        """Sets the permissions for a role in a server."""

        if not server_permissions and not channel_permissions:
            return

        server_value = (server_permissions or self.server_permissions).value
        channel_value = (channel_permissions or self.channel_permissions).value

        await self._cache.api.set_role_permissions(self.server.id, self.id, server_value, channel_value)

    async def delete(self) -> None:
        """Deletes the role"""
        await self._cache.api.delete_role(self.server.id, self.id)

    @overload
    async def edit(
        self,
        *,
        name: Optional[str] = ...,
        colour: Optional[str] = ...,
        hoist: Optional[bool] = ...,
        rank: Optional[int] = ...,
    ) -> None: ...

    async def edit(self, **kwargs) -> None:
        """Edits the role"""
        if kwargs.get("colour", MISSING) == None:
            kwargs["remove_colour"] = True

        await self._cache.api.edit_role(self.server.id, self.id, **kwargs)
