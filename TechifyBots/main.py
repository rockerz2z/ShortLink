import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from TechifyBots.db import db
from TechifyBots.shortener import shorten_text, shorten_bulk, shorten_forwarded
from TechifyBots.notifications import start_scheduler

API_ID = 123456   # your Telegram API ID
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

app = Client("shortlink-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Withdraw History", callback_data="history")],
        [InlineKeyboardButton("👤 Profile Info", callback_data="profile")]
    ])

    await message.reply_text(
        "👋 Welcome to the Link Shortener Bot!\n\n"
        "Send me any link or post and I’ll shorten it.\n\n"
        "Use the menu below to manage your account 👇",
        reply_markup=keyboard
    )
    db.add_user(message.from_user.id, message.from_user.first_name)


# Handle Normal Links
@app.on_message(filters.text & filters.private & ~filters.forwarded)
async def shortener_handler(client, message: Message):
    url = message.text.strip()
    short = await shorten_text(url, message.from_user.id)
    await message.reply_text(f"🔗 Shortened Link:\n{short}")


# Handle Bulk Links
@app.on_message(filters.document & filters.private)
async def bulk_handler(client, message: Message):
    file = await message.download()
    with open(file, "r") as f:
        urls = f.read().splitlines()
    short_links = await shorten_bulk(urls, message.from_user.id)
    await message.reply_text("✅ Bulk Links Shortened:\n\n" + "\n".join(short_links))


# Handle Forwarded Posts
@app.on_message(filters.forwarded & filters.private)
async def forward_handler(client, message: Message):
    short_text = await shorten_forwarded(message, message.from_user.id)
    await message.reply_text(short_text)


# Start Background Notifications
@app.on_message(filters.command("run_scheduler") & filters.user([123456789]))
async def run_scheduler(client, message: Message):
    asyncio.create_task(start_scheduler(app))
    await message.reply_text("⏰ Notification scheduler started.")


# Import callback handlers
from TechifyBots import callback

print("✅ Bot started...")
app.run()
