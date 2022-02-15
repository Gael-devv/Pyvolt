from __future__ import annotations

from typing import Any, Union


class _MissingSentinel:
    def __eq__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return '...'


MISSING: Any = _MissingSentinel()


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
