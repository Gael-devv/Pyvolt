from __future__ import annotations

from typing import TYPE_CHECKING, List, TypedDict
    
if TYPE_CHECKING:
    from .member import Member
    from .message import Message
    from .user import User
        
__all__ = (
    "VosoFeature",
    "ApiInfo",
    "Autumn",
)


class ApiFeature(TypedDict):
    enabled: bool
    url: str


class VosoFeature(ApiFeature):
    ws: str


class Features(TypedDict):
    email: bool
    invite_only: bool
    captcha: ApiFeature
    autumn: ApiFeature
    january: ApiFeature
    voso: VosoFeature


class ApiInfo(TypedDict):
    revolt: str
    features: Features
    ws: str
    app: str
    vapid: str


class Autumn(TypedDict):
    id: str


class GetServerMembers(TypedDict):
    members: List[Member]
    users: List[User]


class MessageWithUserData(TypedDict):
    messages: List[Message]
    members: List[Member]
    users: List[User]


class JoinCall(TypedDict):
    token: str
