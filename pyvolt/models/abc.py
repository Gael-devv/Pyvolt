from __future__ import annotations

import copy
import asyncio
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Protocol,
    Sequence,
    Generator,
    Tuple,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

from ..context_managers import Typing
from ..enums import ChannelType, RemoveFromChannel, SortType
from ..errors import InvalidArgument, ClientException
# from .server import Server
from .permissions import ChannelPermissions, ServerPermissions
from .role import Role
from .file import File
from .. import utils

__all__ = (
    "Snowflake",
    "BaseChannel",
    "EditableChannel",
    "ServerChannel"
)

MISSING = utils.MISSING

if TYPE_CHECKING:
    from datetime import datetime

    from ..client import Client
    from ..cache import CacheManager

    from .asset import Asset
    from .embeds import Embed
    from .message import MessageReply, Masquerade, Message

    MC = TypeVar("MC", "Messageable")


class _Undefined:
    def __repr__(self) -> str:
        return 'see-below'


_undefined: Any = _Undefined()


@runtime_checkable
class Snowflake(Protocol):
    """An ABC that details the common operations on a pyvolt model."""

    __slots__ = ()
    id: str
    

class BaseChannel(Snowflake):
    """An ABC that details the common operations on a Revolt channel."""
    
    __slots__ = ()    
    type: ChannelType
    _cache: CacheManager
    

class EditableChannel(BaseChannel):
    """An ABC that details the common operations on a model that can editable channel"""
    
    __slots__ = ()
    name: str
    description: Optional[str]
    icon: Optional[Asset]
    nsfw: bool

    @overload
    async def edit(
        self, 
        *, 
        name: Optional[str] = ...,
        description: Optional[str] = ...,
        icon: Optional[File] = ...,
        nsfw: Optional[bool] = ...
    ) -> None: ...

    async def edit(self, **kwargs) -> None:
        if kwargs.get("icon", MISSING) == None:
            kwargs["remove"] = RemoveFromChannel.icon
        elif kwargs.get("description", MISSING) == None:
            kwargs["remove"] = RemoveFromChannel.description

        await self._cache.api.edit_channel(self.id, **kwargs)
        
    async def set_default_permissions(self, permissions: ChannelPermissions) -> None:
        await self._cache.api.set_channel_default_permissions(self.id, permissions.value)


class ServerChannel(EditableChannel): 
    """An ABC that details the common operations on a Revolt server channel."""
    
    __slots__ = ()
    server: str
    default_permissions: Optional[ChannelPermissions]
    role_permissions: Optional[Dict[str, ChannelPermissions]]
    
    @property
    def mention(self) -> str:
        return f"<#{self.id}>"

    async def delete(self) -> None:
        await self._cache.api.close_channel(self.id)
    
    async def set_role_permissions(self, role: Role, permissions: ChannelPermissions) -> None:
        """Sets the permissions for a role in a channel."""
        await self._cache.api.set_channel_role_permissions(self.id, role.id, permissions.value)
    

class Messageable:
    """An ABC that details the common operations on a model that can send messages."""

    __slots__ = ()
    _cache: CacheManager

    async def _get_channel(self) -> MC:
        raise NotImplementedError

    async def send(
        self, 
        content: str = " ", 
        *, 
        embed: Optional[Embed] = None, 
        embeds: Optional[List[Embed]] = None, 
        file: Optional[File] = None, 
        files: Optional[List[File]] = None, 
        reply: Optional[MessageReply] = None, 
        replies: Optional[List[MessageReply]] = None, 
        masquerade: Optional[Masquerade] = None,
        delete_after: Optional[float] = None
    ) -> Message:
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~pyvolt.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~pyvolt.File` objects.
        **Specifying both parameters will lead to an exception**.

        To upload a single embed, the ``embed`` parameter should be used with a
        single :class:`~pyvolt.Embed` object. To upload multiple embeds, the ``embeds``
        parameter should be used with a :class:`list` of :class:`~pyvolt.Embed` objects.
        **Specifying both parameters will lead to an exception**.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content of the message to send.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        embeds: List[:class:`~discord.Embed`]
            A list of embeds to upload. Must be a maximum of 10.
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        replies: Optional[list[:class:`MessageReply`]]
            The list of messages to reply to.

        Raises
        --------
        HTTPException
            Sending the message failed.
        Forbidden
            You do not have the proper permissions to send the message.
        InvalidArgument
            The ``files`` list is not of the appropriate size,
            you specified both ``file`` and ``files``,
            or you specified both ``embed`` and ``embeds``,

        Returns
        ---------
        :class:`~discord.Message`
            The message that was sent.
        """

        channel = await self._get_channel()
        cache = self._cache
        content = str(content) 

        if embed is not None and embeds is not None:
            raise InvalidArgument("cannot pass both embed and embeds parameter to send()")

        if embed is not None:
            embed = embed.to_dict()

        elif embeds is not None:
            if len(embeds) > 10:
                raise InvalidArgument("embeds parameter must be a list of up to 10 elements")
            
            embeds = [embed.to_dict() for embed in embeds]

        if reply is not None and replies is not None:
            raise InvalidArgument("cannot pass both reply and replies parameter to send()")

        if reply is not None:
            try:
                reply = reply.to_dict()
            except AttributeError:
                raise InvalidArgument("reply parameter must be MessageReply") from None

        if replies is not None:
            if not all(isinstance(reply, MessageReply) for reply in replies):
                raise InvalidArgument("resplies parameter must be a list of MessageReply")
            
            replies = [reply.to_dict() for reply in replies]

        if file is not None and files is not None:
            raise InvalidArgument("cannot pass both file and files parameter to send()")

        if file is not None:
            if not isinstance(file, File):
                raise InvalidArgument("file parameter must be File")

            file = await cache.api.features.autumn.upload_file(file, "attachments")

        if files is not None:
            if len(files) > 10:
                raise InvalidArgument("files parameter must be a list of up to 10 elements")
            elif not all(isinstance(file, File) for file in files):
                raise InvalidArgument("files parameter must be a list of File")

            attachment_ids: List[str] = []

            for attachment in files:
                data = await cache.api.features.autumn.upload_file(attachment, "attachments")
                attachment_ids.append(data)

            files = attachment_ids
        
        if masquerade is not None:
            masquerade = masquerade.to_dict()
        
        data = await cache.api.send_message(
            channel.id,
            content=content,
            embed=embed,
            embeds=embeds,
            attachment=file,
            attachments=files,
            reply=reply,
            replies=replies,
            masquerade=masquerade
        )

        ret = cache.create_message(channel=channel, data=data)
        if delete_after is not None:
            await ret.delete(delay=delete_after)
        
        return ret
    
    def typing(self) -> Typing:
        """Returns a context manager that allows you to type for an indefinite period of time.

        This is useful for denoting long computations in your bot.

        .. note::

            This is both a regular context manager and an async context manager.
            This means that both ``with`` and ``async with`` work with this.

        Example Usage: ::

            async with channel.typing():
                # simulate something heavy
                await asyncio.sleep(10)

            await channel.send('done!')

        """
        return Typing(self)
    
    
    async def fetch_message(self, id: int, /) -> Message:
        """|coro|

        Retrieves a single :class:`~pyvolt.Message` from the destination.

        Parameters
        ------------
        id: :class:`int`
            The message ID to look for.

        Raises
        --------
        NotFound
            The specified message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.

        Returns
        --------
        :class:`~pyvolt.Message`
            The message asked for.
        """

        channel = await self._get_channel()
        data = await self._cache.api.fetch_message(channel.id, id)
        return self._cache.create_message(channel=channel, data=data)

    async def history(
        self, 
        *, 
        sort: SortType = SortType.latest, 
        limit: int = 100, 
        before: Optional[str] = None, 
        after: Optional[str] = None, 
        nearby: Optional[str] = None
    ) -> Generator[Message]:
        """Fetches multiple messages from the channel's history

        Parameters
        -----------
        sort: :class:`SortType`
            The order to sort the messages in
        limit: :class:`int`
            How many messages to fetch
        before: Optional[:class:`str`]
            The id of the message which should come *before* all the messages to be fetched
        after: Optional[:class:`str`]
            The id of the message which should come *after* all the messages to be fetched
        nearby: Optional[:class:`str`]
            The id of the message which should be nearby all the messages to be fetched

        Returns
        --------
        Generator[:class:`Message`]
            The messages found in order of the sort parameter
        """
        channel = await self._get_channel()
        payloads = await self._cache.api.fetch_messages(channel, sort=sort, limit=limit, before=before, after=after, nearby=nearby)
        
        for payload in payloads:
            yield Message(payload, cache=self._cache)

    async def search(
        self, 
        query: str, 
        *, 
        sort: SortType = SortType.latest, 
        limit: int = 100, 
        before: Optional[str] = None, 
        after: Optional[str] = None
    ) -> Generator[Message]:
        """Searches the channel for a query

        Parameters
        -----------
        query: :class:`str`
            The query to search for in the channel
        sort: :class:`SortType`
            The order to sort the messages in
        limit: :class:`int`
            How many messages to fetch
        before: Optional[:class:`str`]
            The id of the message which should come *before* all the messages to be fetched
        after: Optional[:class:`str`]
            The id of the message which should come *after* all the messages to be fetched

        Returns
        --------
        Generator[:class:`Message`]
            The messages found in order of the sort parameter
        """
        channel = await self._get_channel()
        payloads = await self._cache.api.search_messages(channel, query, sort=sort, limit=limit, before=before, after=after)
        
        for payload in payloads:
            yield Message(payload, cache=self._cache)
