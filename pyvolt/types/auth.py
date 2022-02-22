from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .snowflake import Snowflake
    
__all__ = ("Account",)
    

class Account(TypedDict):
    _id: Snowflake
    email: str


class SessionToken(TypedDict):
    _id: Snowflake
    user_id: Snowflake
    token: str
    name: str
    subscription: str
    
    
class AllSessions(TypedDict):
    _id: Snowflake
    name: str
