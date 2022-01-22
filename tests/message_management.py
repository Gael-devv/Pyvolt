from dotenv import load_dotenv
from os import getenv

import pyvolt
import asyncio


async def main():
    http_client = pyvolt.http.HTTPClient(loop=asyncio.get_event_loop())
    
    token = pyvolt.Token(getenv("BOT_TOKEN"))
    await http_client.static_login(token)
    
    file = pyvolt.File("C:\\Users\\gaelp\\Downloads\\R.jpg", spoiler=True)
    message = await http_client.send_message("01FSMFSXJBYAAYSVCW9JGXXCJ0", "testing 123", attachment=file)
    await http_client.edit_message(message["channel"], message["_id"], "testing 456")
    
    await http_client.close()


load_dotenv()
asyncio.run(main())