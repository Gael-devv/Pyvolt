from __future__ import annotations

from typing import (TYPE_CHECKING, Any, Coroutine, Dict, List, Iterable, Literal, Optional, 
                    TypeVar, ClassVar, Type, Union, overload)

import asyncio
import sys

from urllib.parse import quote as _uriquote
import weakref

import aiohttp

try:
    import ujson as _json
except ImportError:
    import json as _json

from .autumn import Autumn
from ..errors import HTTPException, Forbidden, NotFound, RevoltServerError, LoginFailure
from .. import __version__
from ..utils import _MissingSentinel, MISSING, json_or_text

if TYPE_CHECKING:
    from ..models.token import AuthToken
    from ..models.file import File
    from ..enums import ServerChannelType, SortType, RemoveFromProfileUser, RemoveFromChannel, RemoveFromServer, RemoveFromProfileMember
    
    from ..types import (
        http,
        auth,
        file,
        embed,
        server,
        message,
        channel,
        invites,
        member,
        role,
        user
    )
    from ..types.http import ApiInfo
    from ..types.snowflake import Snowflake, SnowflakeList
    
    from types import TracebackType
    
    T = TypeVar('T')
    BE = TypeVar('BE', bound=BaseException)
    MU = TypeVar('MU', bound='MaybeUnlock')
    Response = Coroutine[Any, Any, T]


class Route:
    base: ClassVar[str] = "https://api.revolt.chat"

    def __init__(self, method: str, path: str, **parameters: Any) -> None:
        self.path: str = path
        self.method: str = method
        
        url = self.base + self.path
        if parameters:
            url = url.format_map({k: _uriquote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        self.url: str = url

        # major parameters:
        self.channel_id: Optional[Snowflake] = parameters.get("channel_id")
        self.server_id: Optional[Snowflake] = parameters.get("server_id")

    @property
    def bucket(self) -> str:
        # the bucket is just method + path w/ major parameters
        return f"{self.channel_id}:{self.server_id}:{self.path}"
    

class MaybeUnlock:
    def __init__(self, lock: asyncio.Lock) -> None:
        self.lock: asyncio.Lock = lock
        self._unlock: bool = True

    def __enter__(self: MU) -> MU:
        return self

    def defer(self) -> None:
        self._unlock = False

    def __exit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        if self._unlock:
            self.lock.release()


class Features: 
    def __init__(
        self, 
        api_info: ApiInfo,
        **kwargs
    ) -> None:
        for k, v in api_info["features"].items():
            if k == "autumn" and v.get("enabled"):
                if url := v.get("url"):
                    self.autumn = Autumn(url, **kwargs)
            
            elif k == "voso":
                pass


class Delta: 
    """Represents the delta API which is the main Revolt API
    `repo https://github.com/revoltchat/delta`
    """
    
    def __init__(
        self, 
        connector: Optional[aiohttp.BaseConnector] = None, 
        *, 
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        url: Optional[str] = None
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop() if loop is None else loop
        self.connector = connector
        self.__session: aiohttp.ClientSession = MISSING
        self._locks: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self._global_over: asyncio.Event = asyncio.Event()
        self._global_over.set()
        
        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[aiohttp.BasicAuth] = proxy_auth
        
        if url:
            Route.base = url

        # values set in init management
        self.token: Optional[AuthToken] = None 
        self.info: Optional[http.ApiInfo] = None 
        self.features: Features = MISSING
        
        user_agent = "Pyvolt (https://github.com/Gael-devv/Pyvolt {0}) Python/{1[0]}.{1[1]} aiohttp/{2}"
        self.user_agent: str = user_agent.format(__version__, sys.version_info, aiohttp.__version__)
        
    def recreate(self) -> None:
        if self.__session.closed:
            self.__session = aiohttp.ClientSession(
                connector=self.connector,
            )
        
    async def ws_connect(self, url: str) -> Any:
        kwargs = {
            "proxy": self.proxy,
            "proxy_auth": self.proxy_auth,
            "max_msg_size": 0,
            "timeout": 30.0,
            "autoclose": False,
            "headers": {
                "User-Agent": self.user_agent,
            }
        }

        return await self.__session.ws_connect(url, **kwargs)
        
    async def request(
        self,
        route: Route,
        *,
        form: Optional[Iterable[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Any:
        bucket = route.bucket
        method = route.method
        url = route.url

        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock()
            if bucket is not None:
                self._locks[bucket] = lock
        
        # header creation
        headers: Dict[str, str] = {
            "User-Agent": self.user_agent,
        }

        # authorization in delta API
        if self.token is not None:
            headers.update(self.token.headers)
        
        # some checking if it's a JSON request
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"
            kwargs["data"] = _json.dumps(kwargs.pop("json"))

        kwargs["headers"] = headers
        
        # Proxy support
        if self.proxy is not None:
            kwargs["proxy"] = self.proxy
        if self.proxy_auth is not None:
            kwargs["proxy_auth"] = self.proxy_auth
        
        if not self._global_over.is_set():
            # wait until the global lock is complete
            await self._global_over.wait()
        
        response: Optional[aiohttp.ClientResponse] = None
        data: Optional[Union[Dict[str, Any], str]] = None
        await lock.acquire()
        with MaybeUnlock(lock) as maybe_lock:
            for tries in range(5):
                if form:
                    form_data = aiohttp.FormData()
                    for params in form:
                        form_data.add_field(**params)
                    kwargs["data"] = form_data

                try:
                    async with self.__session.request(method, url, **kwargs) as response:
                        # even errors have text involved in them so this is safe to call
                        data = await json_or_text(response)

                        # the request was successful so just return the text/json
                        if 300 > response.status >= 200:
                            return data

                        # we are being rate limited
                        if response.status == 429:
                            if not response.headers.get("Via") or isinstance(data, str):
                                # Banned by Cloudflare more than likely.
                                raise HTTPException(response, data)

                            # sleep a bit
                            retry_after: float = data["retry_after"]

                            # check if it's a global rate limit
                            is_global = data.get("global", False)
                            if is_global:
                                self._global_over.clear()

                            await asyncio.sleep(retry_after)

                            # release the global lock now that the
                            # global rate limit has passed
                            if is_global:
                                self._global_over.set()

                            continue

                        # we've received a 500, 502, or 504, unconditional retry
                        if response.status in {500, 502, 504}:
                            await asyncio.sleep(1 + tries * 2)
                            continue

                        # the usual error cases
                        if response.status == 403:
                            raise Forbidden(response, data)
                        elif response.status == 404:
                            raise NotFound(response, data)
                        elif response.status >= 500:
                            raise RevoltServerError(response, data)
                        else:
                            raise HTTPException(response, data)

                # This is handling exceptions from the request
                except OSError as e:
                    # Connection reset by peer
                    if tries < 4 and e.errno in (54, 10054):
                        await asyncio.sleep(1 + tries * 2)
                        continue
                    raise

            if response is not None:
                # We've run out of retries, raise.
                if response.status >= 500:
                    raise RevoltServerError(response, data)

                raise HTTPException(response, data)

            raise RuntimeError("Unreachable code in HTTP handling")
    
    # state management
    
    async def close(self) -> None:
        if self.__session:
            await self.__session.close()
    
    # init management
    
    async def static_login(self, token: AuthToken) -> user.User:
        # Necessary to get aiohttp to stop complaining about session creation
        self.__session = aiohttp.ClientSession(connector=self.connector)
        self.info = await self.get_api_info()
        
        # Features creation
        kwargs = {"session": self.__session, "user_agent": self.user_agent, "proxy": self.proxy, "proxy_auth": self.proxy_auth}
        self.features = Features(self.info, **kwargs)
        
        # Set token
        old_token = self.token
        self.token = token

        try: 
            data = await self.request(Route("GET", "/users/@me"))
        except HTTPException as exc:
            self.token = old_token
            if exc.status == 401:
                raise LoginFailure("Improper token has been passed.") from exc
            raise

        return data
    
    # API core management
    
    def get_api_info(self) -> Response[http.ApiInfo]:
        return self.request(Route("GET", "/"))
    
    # Account management
    
    def fetch_account(self) -> Response[auth.Account]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("GET", "/auth/account"))
    
    def create_account(self, email: str, password: str, *, captcha: str, invite_code: str = None) -> Response[None]:
        """AUTHORIZATIONS: None"""
        r = Route("POST", "/auth/create")
        payload = {
            "email": email,
            "password": password,
            "captcha": captcha,
            "invite": invite_code
        }
        
        return self.request(r, json=payload)
        
    def resend_verification(self, email: str, *, captcha: str) -> Response[None]: 
        """AUTHORIZATIONS: None"""
        r = Route("POST", "/auth/account/reverify")
        payload = {"email": email, "captcha": captcha}
        
        return self.request(r, json=payload)
        
    def verify_email(self, verify_code: str) -> Response[None]:
        """AUTHORIZATIONS: None"""
        return self.request(Route("POST", "/auth/account/verify/{code}", code=verify_code))
        
    def send_password_reset(self, email: str, *, captcha: str) -> Response[None]:
        """AUTHORIZATIONS: None"""
        r = Route("POST", "/auth/account/reset_password")
        payload = {"email": email, "captcha": captcha}
        
        return self.request(r, json=payload)
        
    def password_reset(self, new_password: str, password_reset_token: str) -> Response[None]:
        """AUTHORIZATIONS: None"""
        r = Route("PATCH", "/auth/account/reset_password")
        payload = {"password": new_password, "token": password_reset_token}
        
        return self.request(r, json=payload)
        
    def change_password(self, new_password: str, current_password: str) -> Response[None]:
        """AUTHORIZATIONS: Session Token"""
        r = Route("PATCH", "/auth/account/change/password")
        payload = {"password": new_password, "current_password": current_password}
        
        return self.request(r, json=payload)
        
    def change_email(self, new_email: str, password: str) -> Response[None]:
        """AUTHORIZATIONS: Session Token"""
        r = Route("PATCH", "/auth/account/change/email")
        payload = {"email": new_email, "current_password": password}
        
        return self.request(r, json=payload)
        
    # Session management

    def create_session(
        self, 
        email: str, 
        password: str, 
        *, 
        challenge: str, 
        captcha: str, 
        friendly_name: str = None
    ) -> Response[auth.SessionToken]: 
        """AUTHORIZATIONS: None"""
        r = Route("POST", "/auth/session/login")
        payload = {
            "email": email,
            "password": password,
            "challenge": challenge,
            "captcha": captcha
        }
        
        if friendly_name:
            payload["friendly_name"] = self.user_agent
            
        return self.request(r, json=payload)
        
    def close_current_session(self) -> Response[None]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("POST", "/auth/session/logout"))
        
    def edit_session(self, session: str, friendly_name: str) -> Response[None]:
        """AUTHORIZATIONS: Session Token"""
        r = Route("PATCH", "/auth/session/{session}", session=session)
        payload = {"friendly_name": friendly_name}
        
        return self.request(r, json=payload)
        
    def delete_session(self, session: str) -> Response[None]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("DELETE", "/auth/session/{session}", session=session))
    
    def fetch_all_sessions(self) -> List[Response[auth.AllSessions]]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("GET", "/auth/session/all"))
        
    def delete_all_sessions(self, revoke_self: bool = False) -> Response[None]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("DELETE", "/auth/session/all"), json={"revoke_self": revoke_self})
    
    # User management
    
    async def edit_user(
        self, 
        *, 
        status: Optional[user.Status] = None,
        profile: Optional[user.UserProfile] = None,
        avatar: Optional[File] = None,
        remove: Optional[RemoveFromProfileUser] = None
    ) -> None:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PATCH", "/users/@me")
        payload: Dict[str, Any] = {}
        
        if status: 
            payload["status"] = status
        
        if profile:
            payload["profile"] = profile
        
        if avatar:
            data = await self.upload_file(avatar, "avatars")
            payload["avatar"] = data["id"]
        
        if remove:
            payload["remove"] = remove.value
        
        return await self.request(r, json=payload)
    
    def change_username(self, new_username: str, password: str) -> Response[None]: 
        """AUTHORIZATIONS: Session Token"""
        r = Route("PATCH", "/users/@me/username")
        payload: Dict[str, Any] = {"username": new_username, "password": password}
        
        return self.request(r, json=payload)
    
    def fetch_user(self, user_id: Snowflake) -> Response[user.User]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/users/{user_id}", user_id=user_id))
    
    def fetch_profile(self, user_id: Snowflake) -> Response[user.UserProfile]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/users/{user_id}/profile", user_id=user_id))

    def fetch_mutual_friends_and_servers(self, user_id: Snowflake) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/users/{user_id}/mutual", user_id=user_id))
    
    # Relationships management
    
    def fetch_relationships(self) -> Response[List[user.UserRelation]]: 
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("GET", "/users/relationships"))
    
    def fetch_relationship(self, user_id: Snowflake) -> Response[user.UserRelation]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("GET", "/users/{user_id}/relationship", user_id=user_id))
    
    def send_or_accept_friend_request(self, username: str) -> Response[user.RelationStatus]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("PUT", "/users/{username}/friend", username=username))
    
    def deny_friend_request_or_remove_friend(self, username: str) -> Response[user.RelationStatus]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("DELETE", "/users/{username}/friend", username=username))
        
    def block_user(self, user_id: Snowflake) -> Response[user.RelationStatus]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("PUT", "/users/{user_id}/block", user_id=user_id))
        
    def unblock_user(self, user_id: Snowflake) -> Response[user.RelationStatus]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("DELETE", "/users/{user_id}/block", user_id=user_id))
    
    # Message management
    
    def send_message(
        self, 
        channel_id: Snowflake, 
        *,
        content: Optional[str], 
        embed: Optional[embed.TextEmbed] = None,
        embeds: Optional[List[embed.TextEmbed]] = None,
        attachment: Optional[http.Autumn] = None,
        attachments: Optional[List[http.Autumn]] = None, 
        reply: Optional[message.MessageReply] = None, 
        replies: Optional[List[message.MessageReply]] = None, 
        masquerade: Optional[message.Masquerade] = None
    ) -> Response[message.Message]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("POST", "/channels/{channel_id}/messages", channel_id=channel_id)
        payload: Dict[str, Any] = {}

        if content:
            payload["content"] = content

        if embed:
            payload["embeds"] = [embed]

        if embeds:
            payload["embeds"] = embeds

        if attachment:
            payload["attachments"] = [attachment["id"]]

        if attachments:
            attachment_ids: List[str] = []

            for data in attachments:
                attachment_ids.append(data["id"])

            payload["attachments"] = attachment_ids

        if reply:
            payload["replies"] = [reply]

        if replies:
            payload["replies"] = replies

        if masquerade:
            payload["masquerade"] = masquerade

        return self.request(r, json=payload)

    def edit_message(
        self, 
        channel_id: Snowflake, 
        message_id: Snowflake, 
        content: Optional[str],
        *,
        embed: Optional[embed.TextEmbed] = None,
        embeds: Optional[List[embed.TextEmbed]] = None,
    ) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PATCH", "/channels/{channel_id}/messages/{message_id}", channel_id=channel_id, message_id=message_id)
        payload: Dict[str, Any] = {}

        if content:
            payload["content"] = content

        if embed:
            payload["embeds"] = [embed]

        if embeds:
            payload["embeds"] = embeds
        
        return self.request(r, json=payload)
    
    def delete_message(self, channel_id: Snowflake, message_id: Snowflake) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("DELETE", "/channels/{channel_id}/messages/{message_id}", channel_id=channel_id, message_id=message_id)
        return self.request(r)
    
    def fetch_message(self, channel_id: str, message_id: str) -> Response[message.Message]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("GET", "/channels/{channel_id}/messages/{message_id}", channel_id=channel_id, message_id=message_id)
        return self.request(r)
    
    def fetch_messages(
        self, 
        channel_id: Snowflake, 
        sort: SortType,
        *, 
        limit: Optional[int] = None, 
        before: Optional[str] = None, 
        after: Optional[str] = None, 
        nearby: Optional[str] = None, 
        include_users: bool = False
    ) -> Response[Union[List[message.Message], http.MessageWithUserData]]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("GET", "/channels/{channel_id}/messages", channel_id=channel_id)
        payload: Dict[str, Any] = {"sort": sort.value, "include_users": str(include_users)}

        if limit:
            payload["limit"] = limit

        if before:
            payload["before"] = before

        if after:
            payload["after"] = after

        if nearby:
            payload["nearby"] = nearby

        return self.request(r, json=payload)
    
    def search_messages(
        self, 
        channel_id: Snowflake, 
        query: str,
        *, 
        limit: Optional[int] = None, 
        before: Optional[str] = None, 
        after: Optional[str] = None,
        sort: Optional[SortType] = None,
        include_users: bool = False
    ) -> Response[Union[List[message.Message], http.MessageWithUserData]]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("POST", "/channels/{channel_id}/search", channel_id=channel_id)
        payload: Dict[str, Any] = {"query": query, "include_users": include_users}

        if limit:
            payload["limit"] = limit

        if before:
            payload["before"] = before

        if after:
            payload["after"] = after

        if sort:
            payload["sort"] = sort.value

        return self.request(r, json=payload)
    
    def poll_message_changes(self, channel_id: Snowflake, message_ids: SnowflakeList) -> Response[message.ChangedMessages]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("POST", "/channels/{channel_id}/messages/stale", channel_id=channel_id)  
        return self.request(r, json={"ids": message_ids})
    
    def ack_message(self, channel_id: Snowflake, message_id: Snowflake) -> Response[None]: 
        """AUTHORIZATIONS: Session Token"""
        r = Route("PUT", "/channels/{channel_id}/ack/{message_id}", channel_id=channel_id, message_id=message_id)
        return self.request(r)
    
    # DM management
    
    def fetch_dm_channels(self) -> Response[List[channel.ChannelType]]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/users/dms"))
        
    def open_dm(self, user_id: Snowflake) -> Response[channel.DMChannel]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/users/{user_id}/dm", user_id=user_id))
    
    # Channel management 
        
    async def edit_channel(
        self, 
        channel_id: Snowflake, 
        *, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[File] = None,
        nsfw: Optional[bool] = None,
        remove: Optional[RemoveFromChannel] = None
    ) -> None:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PATCH", "/channels/{channel_id}", channel_id=channel_id)
        payload: Dict[str, Any] = {}
        
        if name:
            payload["name"] = name
        
        if description:
            payload["description"] = description
        
        if icon:
            data = await self.upload_file(icon, "icons")
            payload["icon"] = data["id"]
        
        if nsfw is not None:
            payload["nsfw"] = nsfw
        
        if remove:
            payload["remove"] = remove.value
        
        return await self.request(r, json=payload)
    
    def fetch_channel(self, channel_id: Snowflake) -> Response[channel.ChannelType]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/channels/{channel_id}", channel_id=channel_id))
    
    def close_channel(self, channel_id: Snowflake) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("DELETE", "/channels/{channel_id}", channel_id=channel_id))
    
    def create_invite(self, channel_id: Snowflake) -> Response[invites.InviteCreated]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("POST", "/channels/{channel_id}/invites", channel_id=channel_id))
    
    def set_channel_role_permissions(self, channel_id: Snowflake, role_id: Snowflake, channel_permissions: int) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PUT", "/channels/{channel_id}/permissions/{role_id}", channel_id=channel_id, role_id=role_id)
        payload = {"permissions": channel_permissions}
        
        return self.request(r, json=payload)

    def set_channel_default_permissions(self, channel_id: Snowflake, channel_permissions: int) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PUT", "/channels/{channel_id}/permissions/default", channel_id=channel_id)
        payload = {"permissions": channel_permissions}
        
        return self.request(r, json=payload)  
        
    # Group management
    
    def create_group(
        self, 
        name: str, 
        *, 
        description: Optional[str] = None, 
        users: Optional[SnowflakeList] = None,
        nsfw: Optional[bool] = None
    ) -> Response[channel.Group]: 
        """AUTHORIZATIONS: Session Token"""
        r = Route("POST", "/channels/create")
        payload: Dict[str, Any] = {"name": name, "nsfw": nsfw}
        
        if description: 
            payload["description"] = description
            
        if users:
            payload["users"] = users
            
        if nsfw is not None:
            payload["nsfw"] = nsfw
        
        return self.request(r, json=payload)
        
    def fetch_group_members(self, channel_id: Snowflake) -> List[user.User]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/channels/{channel_id}/members", channel_id=channel_id))
    
    # Voice management 
    
    def join_call(self, channel_id: Snowflake) -> Response[http.JoinCall]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("POST", "/channels/{channel_id}/join_call", channel_id=channel_id))
        
    # Server management
    
    def fetch_server(self, server_id: Snowflake) -> Response[server.Server]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/servers/{server_id}", server_id=server_id))
        
    async def edit_server(
        self,
        server_id: Snowflake,
        *,
        icon: Optional[File] = None,
        banner: Optional[File] = None,
        remove: Optional[RemoveFromServer] = None,
        **options: Any
    ) -> None:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PATCH", "/servers/{server_id}", server_id=server_id)
        payload: Dict[str, Any] = {}
        
        if icon: 
            data = await self.upload_file(icon, "icons")
            payload["icon"] = data["id"]
        
        if banner: 
            data = await self.upload_file(banner, "banners")
            payload["banner"] = data["id"]
        
        if remove:
            payload["remove"] = remove.value
        
        valid_keys = (
            "name", 
            "description",
            "categories",
            "system_messages",
            "nsfw"
        )
        payload.update({k: v for k, v in options.items() if k in valid_keys and v is not None})
        
        return await self.request(r, json=payload)
        
    def create_server(self, name: str, *, description: Optional[str] = None, nsfw: Optional[bool] = None) -> Response[server.Server]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("POST", "/servers/create")
        payload = {"name": name}
        
        if description:
            payload["description"] = description
            
        if nsfw is not None:
            payload["nsfw"] = nsfw
            
        return self.request(r, json=payload)
    
    def delete_leave_server(self, server_id: Snowflake) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("DELETE", "/servers/{server_id}", server_id=server_id))
        
    def create_server_channel(
        self, 
        server_id: Snowflake, 
        channel_type: ServerChannelType, 
        *, 
        name: str, 
        description: Optional[str] = None, 
        nsfw: Optional[bool] = None
    ) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("POST", "/servers/{server_id}/channels", server_id=server_id)
        payload = {
            "type": channel_type.value,
            "name": name
        }
        
        if description: 
            payload["description"] = description
            
        if nsfw is not None:
            payload["nsfw"] = nsfw
            
        return self.request(r, json=payload)
        
    def fetch_server_invites(self, server_id: Snowflake) -> Response[List[invites.PartialInvite]]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/servers/{server_id}/invites", server_id=server_id))
        
    def mark_server_as_read(self, server_id: Snowflake) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("PUT", "/servers/{server_id}/ack", server_id=server_id))
    
    # Member management
    
    def fetch_member(self, server_id: Snowflake, member_id: Snowflake) -> Response[member.Member]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("GET", "/servers/{server_id}/members/{member_id}", server_id=server_id, member_id=member_id)
        return self.request(r)
        
    async def edit_member(
        self, 
        server_id: Snowflake, 
        member_id: Snowflake,
        *,
        nickname: Optional[str] = None,
        avatar: Optional[File] = None,
        roles: Optional[SnowflakeList] = None,
        remove: Optional[RemoveFromProfileMember] = None
    ) -> None:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PATCH", "/servers/{server_id}/members/{member_id}", server_id=server_id, member_id=member_id)
        payload: Dict[str, Any] = {}
        
        if nickname:
            payload["nickname"] = nickname
            
        if avatar:
            data = await self.upload_file(avatar, "avatars")
            payload["avatar"] = data["id"]
        
        if roles:
            payload["roles"] = roles
        
        if remove:
            payload["remove"] = remove.value
            
        return self.request(r, json=payload)
        
    def kick_member(self, server_id: Snowflake, member_id: Snowflake) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("DELETE", "/servers/{server_id}/members/{member_id}", server_id=server_id, member_id=member_id)
        return self.request(r)
        
    def fetch_members(self, server_id: Snowflake) -> Response[http.GetServerMembers]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/servers/{server_id}/members", server_id=server_id))
        
    def fetch_bans(self, server_id: Snowflake) -> Response[server.ServerBans]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/servers/{server_id}/bans", server_id=server_id))
        
    def ban_member(self, server_id: Snowflake, member_id: Snowflake, reason: Optional[str] = None) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PUT", "/servers/{server_id}/bans/{member_id}", server_id=server_id, member_id=member_id)
        payload = {"reason": reason} if reason else None
        
        return self.request(r, json=payload)
        
    def unban_member(self, server_id: Snowflake, member_id: Snowflake) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("DELETE", "/servers/{server_id}/bans/{member_id}", server_id=server_id, member_id=member_id)
        return self.request(r)
    
    # Role management
    
    def create_role(self, server_id: Snowflake, name: str) -> Response[role.Role]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("POST", "/servers/{server_id}/roles", server_id=server_id)        
        return self.request(r, json={"name": name})
    
    def edit_role(
        self, 
        server_id: Snowflake, 
        role_id: Snowflake, 
        *, 
        name: Optional[str] = None,
        colour: Optional[str] = None, # the values can be like this #674EA7 or rgb (103,78,167), and I suppose that with rgba() it also works
        hoist: Optional[bool] = None,
        rank: Optional[int] = None,
        remove_colour: Optional[bool] = None
    ) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PATCH", "/servers/{server_id}/roles/{role_id}", server_id=server_id, role_id=role_id)
        payload: Dict[str, Any] = {}
        
        if name:
            payload["name"] = name
            
        if colour:
            payload["colour"] = colour
            
        if hoist is not None:
            payload["hoist"] = hoist
            
        if rank:
            payload["rank"] = rank
            
        if remove_colour:
            payload["remove"] = "Colour"

        return self.request(r, json=payload)

    def delete_role(self, server_id: Snowflake, role_id: Snowflake) -> Response[None]: 
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("DELETE", "/servers/{server_id}/roles/{role_id}", server_id=server_id, role_id=role_id))
    
    def set_role_permissions(self, server_id: Snowflake, role_id: Snowflake, server_permissions: int, channel_permissions: int) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PUT", "/servers/{server_id}/permissions/{role_id}", server_id=server_id, role_id=role_id)
        payload = {
            "permissions": {
                "server": server_permissions,
                "channel": channel_permissions
            }
        }

        return self.request(r, json=payload)
    
    def set_default_permissions(self, server_id: Snowflake, server_permissions: int, channel_permissions: int) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        r = Route("PUT", "/servers/{server_id}/permissions/default", server_id=server_id)
        payload = {
            "permissions": {
                "server": server_permissions,
                "channel": channel_permissions
            }
        }

        return self.request(r, json=payload)
    
    # Invite management
    
    def fetch_invite(self, code: str) -> Response[invites.Invite]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("GET", "/invites/{invite_code}", invite_code=code))
        
    def join_invite(self, code: str) -> Response[invites.JoinInvite]:
        """AUTHORIZATIONS: Session Token"""
        return self.request(Route("POST", "/invites/{invite_code}", invite_code=code))
        
    def delete_invite(self, code: str) -> Response[None]:
        """AUTHORIZATIONS: Session Token or Bot Token"""
        return self.request(Route("DELETE", "/invites/{invite_code}", invite_code=code))
    