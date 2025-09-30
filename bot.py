import os
import time
import requests
from threading import Thread
from flask import Flask
from datetime import datetime
from pytz import timezone
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN, LOG_CHANNEL

# --- ADDED: Flask app setup and keep-alive functions ---
app = Flask('')

@app.route('/')
def root_route():
    # This endpoint now provides the health check response
    return "<h3 align='center'><b>I am Alive</b></h3>"

def run_flask():
    """Runs the Flask web server."""
    # Use the PORT from environment variables, default to 8080
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Pings the web server to keep the service alive."""
    # !!! IMPORTANT: Replace this with your own app's public URL !!!
    url = 'https://your-app-name.onrender.com' 
    while True:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                print(f"Keep-alive ping successful.")
            else:
                print(f"Keep-alive ping failed with status code: {res.status_code}")
        except Exception as e:
            print(f"An error occurred during keep-alive ping: {e}")
        # Wait for 5 minutes (300 seconds) before the next ping
        time.sleep(300) 
# --- END of ADDED section ---


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
        # --- MODIFIED: Replaced aiohttp server with Flask threads ---
        print("Starting Flask web server and keep-alive thread...")
        # Start the keep_alive function in a separate thread
        Thread(target=keep_alive, daemon=True).start()
        # Start the Flask web server in a separate thread
        Thread(target=run_flask, daemon=True).start()
        print("Web server and keep-alive thread initiated.")
        # --- END of MODIFICATION ---

        await super().start()
        me = await self.get_me()
        self.me = me # Store me object for use in stop method
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

    async def stop(self, *args):
        await super().stop()
        print(f"{self.me.first_name} Bot stopped.")

Bot().run()
