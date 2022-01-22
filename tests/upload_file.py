from dotenv import load_dotenv
from os import getenv

import pyvolt
import asyncio


async def main():
    http_client = pyvolt.http.HTTPClient(loop=asyncio.get_event_loop())
    
    token = pyvolt.Token(getenv("BOT_TOKEN"))
    await http_client.static_login(token)
    
    # upload file
    file = pyvolt.File("C:\\Users\\gaelp\\Downloads\\R.jpg")
    data = await http_client.upload_file(file, "attachments")
    print(data)

    await http_client.close()


load_dotenv()
asyncio.run(main())