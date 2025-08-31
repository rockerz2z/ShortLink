import os
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram import Client
from aiohttp import web
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN, LOG_CHANNEL, WITHDRAW_THRESHOLD, ANALYTICS_CHANNEL
import asyncio
from TechifyBots.db import tb

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route(request):
    return web.Response(text="<h3 align='center'><b>I am Alive</b></h3>", content_type='text/html')

async def web_server():
    app = web.Application(client_max_size=30_000_000)
    app.add_routes(routes)
    return app

async def send_withdrawal_reminders(bot):
    print("Checking for withdrawal reminders...")
    users = await tb.get_all_users()
    for user in users:
        balance = user.get("balance", 0.0)
        if balance >= WITHDRAW_THRESHOLD:
            try:
                await bot.send_message(user["user_id"], f"💰 Your balance is currently `{balance}` which is above the withdrawal threshold of `{WITHDRAW_THRESHOLD}`. Use `/withdraw` to submit a request.")
            except Exception as e:
                print(f"Failed to send reminder to user {user['user_id']}: {e}")

async def collect_analytics(bot):
    print("Collecting analytics...")
    now = datetime.now(timezone("Asia/Kolkata"))
    daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    weekly_start = daily_start - timedelta(days=7)
    monthly_start = daily_start - timedelta(days=30)
    
    daily_stats = await tb.get_analytics_data(daily_start, now)
    weekly_stats = await tb.get_analytics_data(weekly_start, now)
    monthly_stats = await tb.get_analytics_data(monthly_start, now)
    
    msg = (
        f"📊 **Bot Analytics Report**\n\n"
        f"**Daily Stats:**\n"
        f"  Links Shortened: `{daily_stats.get('links_shortened', 0)}`\n"
        f"  Withdrawals: `{daily_stats.get('withdrawal_request', 0)}`\n\n"
        f"**Weekly Stats:**\n"
        f"  Links Shortened: `{weekly_stats.get('links_shortened', 0)}`\n"
        f"  Withdrawals: `{weekly_stats.get('withdrawal_request', 0)}`\n\n"
        f"**Monthly Stats:**\n"
        f"  Links Shortened: `{monthly_stats.get('links_shortened', 0)}`\n"
        f"  Withdrawals: `{monthly_stats.get('withdrawal_request', 0)}`\n"
    )
    
    try:
        await bot.send_message(ANALYTICS_CHANNEL, msg)
    except Exception as e:
        print(f"Error sending analytics to channel: {e}")

class Bot(Client):
    def __init__(self):
        super().__init__(
            "techifybots",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechifyBots"),
            workers=200,
            sleep_threshold=15
        )

    async def start(self):
        app_runner = web.AppRunner(await web_server())
        await app_runner.setup()
        try:
            site = web.TCPSite(app_runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
            await site.start()
            print("Web server started.")
        except Exception as e:
            print(f"Web server error: {e}")

        await super().start()
        me = await self.get_me()
        print(f"Bot Started as {me.first_name}")
        
        if isinstance(ADMIN, int):
            try:
                await self.send_message(ADMIN, f"**{me.first_name} is started...**")
            except Exception as e:
                print(f"Error sending message to admin: {e}")
                
        if LOG_CHANNEL:
            try:
                now = datetime.now(timezone("Asia/Kolkata"))
                msg = (
                    f"**{me.mention} is restarted!**\n\n"
                    f"📅 Date : `{now.strftime('%d %B, %Y')}`\n"
                    f"⏰ Time : `{now.strftime('%I:%M:%S %p')}`\n"
                    f"🌐 Timezone : `Asia/Kolkata`"
                )
                await self.send_message(LOG_CHANNEL, msg)
            except Exception as e:
                print(f"Error sending to LOG_CHANNEL: {e}")
        
        self.loop.create_task(self.scheduler())

    async def scheduler(self):
        while True:
            await send_withdrawal_reminders(self)
            await collect_analytics(self)
            await asyncio.sleep(86400) # Sleep for 24 hours

    async def stop(self, *args):
        await super().stop()
        print(f"{me.first_name} Bot stopped.")

Bot().run()
