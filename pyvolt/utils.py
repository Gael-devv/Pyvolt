from __future__ import annotations

from typing import Any, Union, Dict

from aiohttp import ClientResponse

try:
    import ujson as _json
except ImportError:
    import _json


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
