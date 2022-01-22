from dotenv import load_dotenv
from os import getenv

import pyvolt
import asyncio


async def main():
    http_client = pyvolt.http.HTTPClient(loop=asyncio.get_event_loop())
    
    token = pyvolt.Token(getenv("BOT_TOKEN"))
    print(await http_client.static_login(token))
    
    print(http_client.api_info)
    
    await http_client.close()


load_dotenv()
asyncio.run(main())