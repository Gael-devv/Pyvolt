import pyvolt
import asyncio


async def main():
    http_client = pyvolt.http.HTTPClient(loop=asyncio.get_event_loop())
    
    token = pyvolt.Token("AMcm_dFZNCE-roKk_N6rcPs-mbtGAhb-nLzC1m3kJVCqKcakSEFRC04TcvHN5qGE")
    await http_client.static_login(token)
    
    # upload file
    file = pyvolt.File("C:\\Users\\gaelp\\Downloads\\R.jpg")
    data = await http_client.upload_file(file, "attachments")
    print(data)

    await http_client.close()


asyncio.run(main())