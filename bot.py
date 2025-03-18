import os
import asyncio
import logging
from configs import *
from aiohttp import web
from pyrogram import Client
from utilities import web_server, ping_server

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShortnerBot(Client):
    def __init__(self):
        super().__init__(
            "shortner_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=100
        )

    async def start(self):
        # Properly initialize the web server
        app = await web_server()
        runner = web.AppRunner(app)
        await runner.setup()

        ba = "0.0.0.0"
        port = int(os.getenv("PORT", 8080))
        site = web.TCPSite(runner, ba, port)
        await site.start()

        await super().start()
        logger.info("Bot started successfully")

        # Start ping server in the background
        asyncio.create_task(ping_server())

    async def stop(self, *args):
        await super().stop()
        logger.info("Bot stopped")

if __name__ == '__main__':
    ShortnerBot().run()