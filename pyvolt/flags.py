from __future__ import annotations

from typing import Any, Callable, ClassVar, Dict, Iterator, Optional, Tuple, Type, TypeVar, overload

__all__ = ("flag_value", "Flags", "UserBadges")

FV = TypeVar('FV', bound='flag_value')
BF = TypeVar('BF', bound='BaseFlags')


class flag_value:
    __slots__ = ("flag", "__doc__")

    def __init__(self, func: Callable[[Any], int]):
        self.flag = func(None)
        self.__doc__ = func.__doc__

    @overload
    def __get__(self: FV, instance: None, owner: Type[BF]) -> FV:
        ...

    @overload
    def __get__(self, instance: BF, owner: Type[BF]) -> bool:
        ...

    def __get__(self, instance: Optional[BF], owner: Type[BF]) -> Any:
        if instance is None:
            return self

        return instance._has_flag(self.flag)

    def __set__(self, instance: BF, value: bool) -> None:
        instance._set_flag(self.flag, value)

    def __repr__(self):
        return f'<flag_value flag={self.flag!r}>'


class BaseFlags:
    VALID_FLAGS: ClassVar[Dict[str, int]]
    DEFAULT_VALUE: ClassVar[int]

    value: int

    __slots__ = ('value',)

    def __init__(self, **kwargs: bool):
        self.value = self.DEFAULT_VALUE
        
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
                
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} value={self.value}>'

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) == o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError(f'Value to set for {self.__class__.__name__} must be a bool.')


class UserBadges(BaseFlags):
    """Contains all user badges"""

    @flag_value
    def developer():
        """:class:`bool` The developer badge."""
        return 1 << 0

    @flag_value
    def translator():
        """:class:`bool` The translator badge."""
        return 1 << 1

    @flag_value
    def supporter():
        """:class:`bool` The supporter badge."""
        return 1 << 2

    @flag_value
    def responsible_disclosure():
        """:class:`bool` The responsible disclosure badge."""
        return 1 << 3

    @flag_value
    def founder():
        """:class:`bool` The founder badge."""
        return 1 << 4

    @flag_value
    def platform_moderation():
        """:class:`bool` The platform moderation badge."""
        return 1 << 5

    @flag_value
    def active_supporter():
        """:class:`bool` The active supporter badge."""
        return 1 << 6

    @flag_value
    def paw():
        """:class:`bool` The paw badge."""
        return 1 << 7

    @flag_value
    def early_adopter():
        """:class:`bool` The early adopter badge."""
        return 1 << 8

    @flag_value
    def reserved_relevant_joke_badge_1():
        """:class:`bool` The reserved relevant joke badge 1 badge."""
        return 1 << 9
