from __future__ import annotations

import asyncio
import datetime
import io
from typing import TYPE_CHECKING, Any, NamedTuple, Dict, Optional, List, Union

from .asset import Asset, PartialAsset
from .embeds import Embed
from .file import File
from .mixins import Hashable
from ..utils import MISSING

if TYPE_CHECKING:
    from ..cache import CacheManager
    from ..types.file import File as FilePayload
    from ..types.message import Masquerade as MasqueradePayload
    from ..types.message import Message as MessagePayload
    from ..types.message import MessageReply as MessageReplyPayload
    
    from ..errors import HTTPException, InvalidArgument

__all__ = (
    "Message",
    "MessageReply",
    "Masquerade"
)


class Attachment(Asset):
    """Represents an attachment from Revolt.

    Attributes
    ------------
    id: :class:`int`
        The attachment ID.
    size: :class:`int`
        The attachment size in bytes.
    height: Optional[:class:`int`]
        The attachment's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The attachment's width, in pixels. Only applicable to images and videos.
    filename: :class:`str`
        The attachment's filename.
    url: :class:`str`
        The attachment URL. If the message this attachment was attached
        to is deleted, then this will 404.
    content_type: Optional[:class:`str`]
        The attachment's `media type <https://en.wikipedia.org/wiki/Media_type>`_
    """

    def __repr__(self) -> str:
        return f"<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>"

    def __str__(self) -> str:
        return self.url or ""

    def is_spoiler(self) -> bool:
        """:class:`bool`: Whether this attachment contains a spoiler."""
        return self.filename.startswith("SPOILER_")

    async def to_file(self, *, spoiler: bool = False) -> File:
        """|coro|

        Converts the attachment into a :class:`File` suitable for sending via
        :meth:`abc.Messageable.send`.

        Parameters
        -----------
        spoiler: :class:`bool`
            Whether the file is a spoiler.

        Raises
        ------
        HTTPException
            Downloading the attachment failed.
        Forbidden
            You do not have permissions to access this attachment
        NotFound
            The attachment was deleted.

        Returns
        -------
        :class:`File`
            The attachment as a file suitable for sending.
        """

        data = await self.read()
        return File(io.BytesIO(data), filename=self.filename, spoiler=spoiler)


class Message(Hashable):
    """Represents a message

    Attributes
    -----------
    id: :class:`str`
        The id of the message
    content: :class:`str`
        The content of the message, this will not include system message's content
    attachments: list[:class:`Asset`]
        The attachments of the message
    embeds: list[:class:`Embed`]
        The embeds of the message
    channel: :class:`Messageable`
        The channel the message was sent in
    server: :class:`Server`
        The server the message was sent in
    author: Union[:class:`Member`, :class:`User`]
        The author of the message, will be :class:`User` in DMs
    edited_at: Optional[:class:`datetime.datetime`]
        The time at which the message was edited, will be None if the message has not been edited
    mentions: list[Union[:class:`Member`, :class:`User`]]
        The users or members that where mentioned in the message
    replies: list[:class:`Message`]
        The message's this message has replied to, this may not contain all the messages if they are outside the cache
    reply_ids: list[:class:`str`]
        The message's ids this message has replies to
    """
    __slots__ = ("_cache", "id", "content", "attachments", "embeds", "channel", "server", "author", "edited_at", "mentions", "replies", "replies_ids")

    def __init__(self, data: MessagePayload, *, cache: CacheManager):
        self._cache = cache

        self.id = data["_id"]
        self.content = data["content"]
        self.attachments = [Attachment(cache, attachment) for attachment in data.get("attachments", [])]
        self.embeds = [Embed.from_dict(embed) for embed in data.get("embeds", [])]

        self.channel = cache.get_channel(data["channel"])
        self.server = self.channel and self.channel.server

        if self.server:
            author = cache.get_member(self.server.id, data["author"])
        else:
            author = cache.get_user(data["author"])

        self.author = author

        if masquerade := data.get("masquerade"):
            self.masquerade = Masquerade(**masquerade)

        if edited_at := data.get("edited"):
            self.edited_at: Optional[datetime.datetime] = datetime.datetime.strptime(edited_at["$date"], "%Y-%m-%dT%H:%M:%S.%f%z")

        if self.server:
            self.mentions = [self.server.get_member(member_id) for member_id in data.get("mentions", [])]
        else:
            self.mentions = [cache.get_user(member_id) for member_id in data.get("mentions", [])]

        self.replies = []
        self.replies_ids = []

        for reply in data.get("replies", []):
            try:
                message = cache.get_message(reply)
                self.replies.append(message)
            except KeyError:
                pass

            self.replies_ids.append(reply)

    def _update(self, *, content: Optional[str] = None, edited_at: Optional[str] = None) -> Message:
        if content:
            self.content = content

        if edited_at:
            self.edited_at = datetime.datetime.strptime(edited_at, "%Y-%m-%dT%H:%M:%S.%f%z")
            # strptime is used here instead of fromisoformat because of its inability to parse `Z` (Zulu or UTC time) in the RFCC 3339 format provided by API

        return self

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to this message."""
        base_url = self._state.api.info["app"]
        return base_url + f"/channels/{self.channel.id}/{self.id}"

    async def edit(
        self, 
        content: str, 
        *, 
        embed: Optional[Embed] = MISSING, 
        embeds: List[Embed] = MISSING, 
        delete_after: Optional[float] = None
    ) -> None:
        """Edits the message. The bot can only edit its own message
        Parameters
        -----------
        content: :class:`str`
            The new content of the message
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove the embed.
        embeds: List[:class:`Embed`]
            The new embeds to replace the original with. Must be a maximum of 10.
            To remove all embeds ``[]`` should be passed.
        """
        payload: Dict[str, Any] = {}
        
        if embed is not MISSING and embeds is not MISSING:
            raise InvalidArgument("cannot pass both embed and embeds parameter to edit()")

        if embed is not MISSING:
            if embed is None:
                payload["embeds"] = []
            else:
                payload["embeds"] = [embed.to_dict()]
        elif embeds is not MISSING:
            payload["embeds"] = [e.to_dict() for e in embeds]
        
        await self._cache.api.edit_message(self.channel.id, self.id, content, **payload)
        
        if delete_after is not None:
            await self.delete(delay=delete_after)

    async def reply(self, content: str = " ", mention: bool = True, **kwargs) -> Message:
        """|coro|

        A shortcut method to :meth:`.abc.Messageable.send` to reply to the
        :class:`.Message`.

        Raises
        --------
        HTTPException
            Sending the message failed.
        Forbidden
            You do not have the proper permissions to send the message.
        InvalidArgument
            The ``files`` list is not of the appropriate size or
            you specified both ``file`` and ``files``.

        Returns
        ---------
        :class:`.Message`
            The message that was sent.
        """

        reply = MessageReply(self, mention)
        return await self.channel.send(content, reply=reply, **kwargs)

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the message.

        Your own messages could be deleted without any proper permissions. However to
        delete other people's messages, you need the :attr:`~ChannelPermissions.manage_messages`
        permission.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message. If the deletion fails then it is silently ignored.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        NotFound
            The message was deleted already
        HTTPException
            Deleting the message failed.
        """
        if delay is not None:

            async def delete(delay: float):
                await asyncio.sleep(delay)
                try:
                    await self._cache.api.delete_message(self.channel.id, self.id)
                except HTTPException:
                    pass

            asyncio.create_task(delete(delay))
        else:
            await self._cache.api.delete_message(self.channel.id, self.id)


class MessageReply(NamedTuple):
    """A namedtuple which represents a reply to a message.

    Parameters
    -----------
    message: :class:`Message`
        The message being replied to.
    mention: :class:`bool`
        Whether the reply should mention the author of the message. Defaults to false.
    """
    message: Message
    mention: bool = True

    def to_dict(self) -> MessageReplyPayload:
        return { "id": self.message.id, "mention": self.mention }


class Masquerade:
    """A class which represents a message's masquerade.

    Parameters
    -----------
    name: Optional[:class:`str`]
        The name to display for the message
    avatar: Optional[:class:`str`]
        The avatar's url to display for the message
    """ 

    def __init__(self, name: Optional[str] = None, avatar: Optional[Union[str, Asset]] = None) -> None:
        self.name = name
        
        if isinstance(avatar, Asset):
            self.avatar = avatar.url
        else:
            self.avatar = avatar

    def to_dict(self) -> MasqueradePayload:
        output: MasqueradePayload = {}

        if name := self.name:
            output["name"] = name

        if avatar := self.avatar:
            output["avatar"] = avatar

        return output
