import pyvolt
import asyncio


async def main():
    http_client = pyvolt.http.HTTPClient(loop=asyncio.get_event_loop())
    
    token = pyvolt.Token("AMcm_dFZNCE-roKk_N6rcPs-mbtGAhb-nLzC1m3kJVCqKcakSEFRC04TcvHN5qGE")
    print(await http_client.static_login(token))
    
    print(http_client.api_info)
    
    await http_client.close()


asyncio.run(main())