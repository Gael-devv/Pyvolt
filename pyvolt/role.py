from __future__ import annotations

from typing import TYPE_CHECKING, Optional, overload

from .utils import MISSING
from .permissions import ChannelPermissions, ServerPermissions

if TYPE_CHECKING:
    from .server import Server
    from .state import State
    from .types.role import Role as RolePayload

__all__ = ("Role",)


class Role:
    """Represents a role in a :class:`Server`"""
    __slots__ = (
        "server", 
        "id", 
        "name", 
        "server_permissions", 
        "channel_permissions",
        "colour", 
        "hoist", 
        "rank", 
        "_state", 
    )

    def __init__(self, *, server: Server, state: State, data: RolePayload, role_id: str):
        self.server = server
        self._state = state
        self.id = role_id
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Role id={self.id} name={self.name!r}>'

    @property
    def color(self):
        return self.colour

    async def set_permissions(self, *, server_permissions: Optional[ServerPermissions] = None, channel_permissions: Optional[ChannelPermissions] = None) -> None:
        """Sets the permissions for a role in a server."""

        if not server_permissions and not channel_permissions:
            return

        server_value = (server_permissions or self.server_permissions).value
        channel_value = (channel_permissions or self.channel_permissions).value

        await self._state.http.set_role_permissions(self.server.id, self.id, server_value, channel_value)

    def _update(self, data: RolePayload):
        self.name: str = data["name"]
        self.server_permissions = ServerPermissions._from_value(data["permissions"][0])
        self.channel_permissions = ChannelPermissions._from_value(data["permissions"][1])
        self.colour: int = data.get("colour", None)
        self.hoist: bool = data.get('hoist', False)
        self.rank = data["rank"]

    async def delete(self) -> None:
        """Deletes the role"""
        await self._state.http.delete_role(self.server.id, self.id)

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

        await self._state.http.edit_role(self.server.id, self.id, **kwargs)
