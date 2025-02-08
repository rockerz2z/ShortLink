from configs import *
from aiohttp import web
from shortzy import Shortzy
import asyncio, logging, aiohttp
from plugins.database import db

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    """Root API Route"""
    return web.json_response("TechifyBots")

async def web_server():
    """Starts the web server"""
    web_app = web.Application(client_max_size=30_000_000)
    web_app.add_routes(routes)
    return web_app

async def ping_server():
    """Pings the server every 10 minutes to keep it alive"""
    while True:
        await asyncio.sleep(600)
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(BASE_URL) as resp:
                    logging.info(f"Pinged server with response: {resp.status}")
        except asyncio.TimeoutError:
            logging.warning("⚠️ Connection timed out while pinging the server!")
        except aiohttp.ClientError as e:
            logging.error(f"❌ Network error while pinging the server: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in ping_server: {e}")

async def short_link(link, uid):
    """Shortens a link using the user's stored shortener settings"""
    usite = await db.get_value("shortner", uid=uid)
    uapi = await db.get_value("api", uid=uid)

    if not usite or not uapi:
        raise ValueError("⚠️ Shortener URL or API key is missing!")

    shortzy = Shortzy(api_key=uapi, base_site=usite)
    return await shortzy.convert_from_text(link)

async def save_data(tst_url, tst_api, uid):
    """Saves user-provided shortener URL & API key if valid"""
    shortzy = Shortzy(api_key=tst_api, base_site=tst_url)
    test_link = "https://telegram.me/TechifyBots"

    try:
        short = await shortzy.convert(test_link)
        if short.startswith("http"):
            await db.set_shortner(uid, shortner=tst_url, api=tst_api)
            return True
    except Exception as e:
        logging.error(f"❌ Failed to validate shortener: {e}")

    return False
