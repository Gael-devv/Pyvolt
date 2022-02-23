from __future__ import annotations

from typing import TypeVar, Any, Union, Dict, Callable, Optional, Iterable

from aiohttp import ClientResponse

try:
    import ujson as _json
except ImportError:
    import _json

T = TypeVar("T")


class _MissingSentinel:
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return "..."


MISSING: Any = _MissingSentinel()


async def json_or_text(response: ClientResponse) -> Union[Dict[str, Any], str]:
    text = await response.text(encoding="utf-8")
    try:
        if response.headers["content-type"] == "application/json":
            return _json.loads(text)
    except KeyError:
        # Thanks Cloudflare
        pass

    return text


def colour(value: Union[str, tuple]) -> str:
    """
    to convert the string or tuple into valid html colors. 
    Usage::
    
        colour((187, 64, 255))
        
        colour((187, 64, 255, 1))
        
        colour("BB40FF")
    """
    if isinstance(value, tuple):
        if len(value) == 4:
            return "rgba" + str(value)
        else:
            return "rgb" + str(value)
    elif isinstance(value, str):
        if value.startswith("#"):
            return value
        else:
            return "#" + value


def find(predicate: Callable[[T], Any], seq: Iterable[T]) -> Optional[T]:
    """A helper to return the first element found in the sequence
    that meets the predicate. For example: ::

        member = pyvolt.utils.find(lambda m: m.name == 'Mighty', channel.server.members)

    would find the first :class:`~pyvolt.Member` whose name is 'Mighty' and return it.
    If an entry is not found, then ``None`` is returned.

    This is different from :func:`py:filter` due to the fact it stops the moment it finds
    a valid entry.

    Parameters
    -----------
    predicate
        A function that returns a boolean-like result.
    seq: :class:`collections.abc.Iterable`
        The iterable to search through.
    """

    for element in seq:
        if predicate(element):
            return element
    
    return None