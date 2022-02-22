from __future__ import annotations

from typing import (TYPE_CHECKING, Optional)

import aiohttp

from ..errors import HTTPException, Forbidden, NotFound, RevoltServerError
from ..utils import json_or_text

if TYPE_CHECKING:
    from ..models.file import File

    from ..types import http
    from ..types.snowflake import Snowflake


class Autumn:
    """Represents revolt's pluggable file server
    `repo https://github.com/revoltchat/autumn`
    """
    
    def __init__(
        self,
        url: str,
        *,
        session: aiohttp.ClientSession,
        user_agent: str,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None
    ) -> None:
        self.url = url
        self.session = session
        self.user_agent = user_agent
        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[aiohttp.BasicAuth] = proxy_auth
        
    async def upload_file(self, file: File, tag: str) -> http.Autumn:
        url = f"{self.url}/{tag}"

        headers = {
            "User-Agent": self.user_agent
        }

        form = aiohttp.FormData()
        form.add_field("file", file.fp.read(), filename=file.filename)

        async with self.session.post(url, data=form, headers=headers, proxy=self.proxy, proxy_auth=self.proxy_auth) as resp:
            data: http.Autumn = await json_or_text(resp)
        
        if resp.status == 400:
            raise HTTPException(resp, data)
        elif 500 <= resp.status <= 600:
            raise RevoltServerError(resp, data)
        else:
            return data
    
    async def fetch_file(self, tag: str, id: Snowflake) -> bytes:
        url = f"{self.url}/{tag}/{id}"
        
        headers = {
            "User-Agent": self.user_agent
        }
        
        async with self.session.get(url, headers=headers, proxy=self.proxy, proxy_auth=self.proxy_auth) as resp:
            if resp.status == 200:
                return await resp.read()
            elif resp.status == 404:
                raise NotFound(resp, "file not found")
            elif resp.status == 403:
                raise Forbidden(resp, "cannot retrieve file")
            else:
                raise HTTPException(resp, "failed to get file")
    