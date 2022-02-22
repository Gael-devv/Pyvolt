from __future__ import annotations

from typing import Any, Dict, Final, List, Literal, Mapping, Protocol, TYPE_CHECKING, Type, TypeVar, Union

from ..enums import EmbedType
from .. import utils

__all__ = (
    'Embed',
)


class _EmptyEmbed:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "Embed.Empty"

    def __len__(self) -> int:
        return 0


EmptyEmbed: Final = _EmptyEmbed()


class EmbedProxy:
    def __init__(self, layer: Dict[str, Any]):
        self.__dict__.update(layer)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __repr__(self) -> str:
        inner = ", ".join((f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")))
        return f"EmbedProxy({inner})"

    def __getattr__(self, attr: str) -> _EmptyEmbed:
        return EmptyEmbed


E = TypeVar("E", bound="Embed")

if TYPE_CHECKING:
    from ..types.embed import EmbedType

    T = TypeVar('T')
    MaybeEmpty = Union[T, _EmptyEmbed]

    class _EmbedImageProxy(Protocol):
        url: MaybeEmpty[str]
        height: MaybeEmpty[int]
        width: MaybeEmpty[int]
        size: MaybeEmpty[str]

    class _EmbedImageProxy(Protocol):
        url: MaybeEmpty[str]
        height: MaybeEmpty[int]
        width: MaybeEmpty[int]
        size: MaybeEmpty[str]

    class _EmbedVideoProxy(Protocol):
        url: MaybeEmpty[str]
        height: MaybeEmpty[int]
        width: MaybeEmpty[int]


class Embed:
    """Represents a Pyvolt embed.

    Certain properties return an ``EmbedProxy``, a type
    that acts similar to a regular :class:`dict` except using dotted access,
    e.g. ``embed.author.icon_url``. If the attribute
    is invalid or empty, then a special sentinel value is returned,
    :attr:`Embed.Empty`.

    For ease of use, all parameters that expect a :class:`str` are implicitly
    casted to :class:`str` for you.

    Attributes
    -----------
    title: :class:`str`
        The title of the embed.
        This can be set during initialisation.
    type: :class:`EmbedType`
        The type of embed. Usually is text.
        It is possible that this in a message is website.
    description: :class:`str`
        The description of the embed.
        This can be set during initialisation.
    url: :class:`str`
        The URL of the embed.
        This can be set during initialisation.
    colour: :class:`str`
        The colour of the embed. Aliased to ``color`` as well.
        This can be set during initialisation.
    Empty
        A special sentinel value used by ``EmbedProxy`` and this class
        to denote that the value or attribute is empty.
    """

    __slots__ = (
        "type",
        "title",
        "url",
        "_image",
        "_video",
        "_media",
        "description",
        "_colour"
    )

    Empty: Final = EmptyEmbed

    def __init__(
        self,
        *,
        colour: Union[str, tuple, _EmptyEmbed] = EmptyEmbed,
        color: Union[str, tuple, _EmptyEmbed] = EmptyEmbed,
        title: MaybeEmpty[Any] = EmptyEmbed,
        url: MaybeEmpty[Any] = EmptyEmbed,
        description: MaybeEmpty[Any] = EmptyEmbed,
    ):

        self.type = EmbedType.text
        self.title = title
        self.url = url
        self.description = description
        self._colour = utils.colour(colour) if colour is not EmptyEmbed else utils.colour(color)

        if self.title is not EmptyEmbed:
            self.title = str(self.title)

        if self.description is not EmptyEmbed:
            self.description = str(self.description)

        if self.url is not EmptyEmbed:
            self.url = str(self.url)

    @classmethod
    def from_dict(cls: Type[E], data: Mapping[str, Any]) -> E:
        """Converts a :class:`dict` to a :class:`Embed` provided it is in the
        format that Pyvolt expects it to be in.

        Parameters
        -----------
        data: :class:`dict`
            The dictionary to convert into an embed.
        """
        # we are bypassing __init__ here since it doesn't apply here
        self: E = cls.__new__(cls)

        # fill in the basic fields

        self.type = EmbedType(data["type"])
        self.title = data.get("title", EmptyEmbed)
        self.description = data.get("description", EmptyEmbed)
        self._colour = data.get("colour", EmptyEmbed)
        self.url = data.get("url", EmptyEmbed)

        if self.type is EmbedType.website:
            self._image = data.get("image", EmptyEmbed)
            self._video = data.get("video", EmptyEmbed)

            self.site_name = data.get("site_name", EmptyEmbed)
        else:
            self._media = data.get("media", EmptyEmbed)
    
        if self.title is not EmptyEmbed:
            self.title = str(self.title)

        if self.description is not EmptyEmbed:
            self.description = str(self.description)

        if self.url is not EmptyEmbed:
            self.url = str(self.url)


        return self

    def copy(self: E) -> E:
        """Returns a shallow copy of the embed."""
        return self.__class__.from_dict(self.to_dict())

    def __len__(self) -> int:
        total = len(self.title) + len(self.description)
        if self.title is EmbedType.website:
            total += len(self.image) + len(self.video)
        else:
            total += len(self.image)
        
        return total

    def __bool__(self) -> bool:
        return any(
            (
                self.url,
                self.title,
                self.description,
                self.colour,
            )
        )

    @property
    def colour(self) -> MaybeEmpty[str]:
        return getattr(self, "_colour", EmptyEmbed)

    @colour.setter
    def colour(self, value: Union[str, tuple, _EmptyEmbed]):  # type: ignore
        if isinstance(value, _EmptyEmbed):
            self._colour = value
        else:
            self._colour = utils.colour(value)

    color = colour

    @property
    def media(self): 
        """Returns an ``EmbedProxy`` denoting the image contents.

        Possible attributes you can access are:

        - ``url``
        - ``width``
        - ``height``

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_image', {}))  # type: ignore

    @property
    def image(self) -> _EmbedImageProxy:
        """Returns an ``EmbedProxy`` denoting the image contents if type is website.

        Possible attributes you can access are:

        - ``url``
        - ``width``
        - ``height``
        - ``size``

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_image', {}))  # type: ignore

    @property
    def video(self) -> _EmbedVideoProxy:
        """Returns an ``EmbedProxy`` denoting the video contents if type is website.

        Possible attributes include:

        - ``url`` for the video URL.
        - ``height`` for the video height.
        - ``width`` for the video width.

        If the attribute has no value then :attr:`Empty` is returned.
        """
        return EmbedProxy(getattr(self, '_video', {}))  # type: ignore

    def to_dict(self) -> EmbedType:
        """Converts this embed object into a dict."""

        # add in the raw data into the dict
        # fmt: off
        result = {
            key[1:]: getattr(self, key)
            for key in self.__slots__
            if key[0] == '_' and hasattr(self, key)
        }
        # fmt: on

        # add in the non raw attribute ones
        if self.type:
            result["type"] = self.type.value

        if self.description:
            result["description"] = self.description

        if self.url:
            result["url"] = self.url

        if self.title:
            result["title"] = self.title

        return result  # type: ignore
