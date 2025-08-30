import re
import httpx
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.errors import *
from pyrogram.types import *
from config import *
from .db import tb
from .fsub import get_fsub
from Script import text
from .maintenance import get_maintenance

# Regex to detect URLs
URL_REGEX = r'(https?://[^\s]+)'

# --- Shortening Functions ---
async def shorten_url(original_url, api_key, base_site="shortzy.in"):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{base_site}/api",
                params={"api": api_key, "url": original_url},
                timeout=8
            )
            data = await resp.asejson()
            if data.get("status") == "success":
                return data.get("shortenedUrl")
            return original_url  # fallback if failed
    except Exception as e:
        print(f"[ERROR] Failed to shorten: {original_url} — {e}")
        return original_url

async def shorten_urls_in_text(text, api_key, base_site="shortzy.in"):
    urls = re.findall(URL_REGEX, text)
    if not urls:
        return text
    updated_text = text
    for url in urls:
        short_url = await shorten_url(url, api_key, base_site)
        updated_text = updated_text.replace(url, short_url)
    return updated_text

# --- DB Handling ---
async def short_link(link, user_id):
    usite = await tb.get_value("shortner", user_id=user_id) or "shortzy.in"
    uapi = await tb.get_value("api", user_id=user_id)
    if not uapi:
        return link  # API not set yet
    return await shorten_url(link, uapi, usite)

async def save_data(tst_url, tst_api, user_id):
    test_link = "https://telegram.me/TechifyBots"
    short = await shorten_url(test_link, tst_api, tst_url)
    if short.startswith("http"):
        await tb.set_shortner(user_id=user_id, shortner=tst_url, api=tst_api)
        return True
    return False

# --- Bot Handlers ---
@Client.on_message(filters.command('start') & filters.private)
async def start_handler(c, m):
    try:
        if await tb.is_user_banned(m.from_user.id):
            return await m.reply(
                "**🚫 You are banned from using this bot**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]])
            )
        if await tb.get_user(m.from_user.id) is None:
            await tb.add_user(m.from_user.id, m.from_user.first_name)

        bot = await c.get_me()
        await c.send_message(
            LOG_CHANNEL,
            text.LOG.format(
                m.from_user.id,
                getattr(m.from_user, "dc_id", "N/A"),
                m.from_user.first_name or "N/A",
                f"@{m.from_user.username}" if m.from_user.username else "N/A",
                bot.username
            )
        )
        if IS_FSUB and not await get_fsub(c, m):
            return

        await m.reply_photo(
            photo=random.choice(PICS),
            caption=text.START.format(m.from_user.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ℹ️ About", callback_data="about"),
                 InlineKeyboardButton("📚 Help", callback_data="help")],
                [InlineKeyboardButton("👨‍💻 Developer 👨‍💻", user_id=int(ADMIN))]
            ])
        )
    except Exception as u:
        await m.reply(f"**❌ Error:** `{str(u)}`")

@Client.on_message(filters.command('shortlink') & filters.private)
async def save_shortlink(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    if IS_FSUB and not await get_fsub(c, m): return
    if len(m.command) < 3:
        return await m.reply_text(
            "**❌ Please provide both the Shortener URL and API key.\n\nExample: `/shortlink shortzy.in your_api_key`**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]]))

    usr = m.from_user
    elg = await save_data(m.command[1], m.command[2], user_id=usr.id)
    if elg:
        return await m.reply_text(
            f"**✅ Shortener set successfully!\n\n🌐 URL - {await tb.get_value('shortner', user_id=usr.id)}\n🔑 API - {await tb.get_value('api', user_id=usr.id)}**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]]))
    else:
        return await m.reply_text("**⚠️ Error:\n\nInvalid Shortlink API or URL!**",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]]))

@Client.on_message(filters.command('info') & filters.private)
async def showinfo(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    usr = m.from_user
    site = await tb.get_value('shortner', user_id=usr.id)
    api = await tb.get_value('api', user_id=usr.id)
    await m.reply_text(
        f"**Your Information**\n\n👤 User: {usr.mention}\n🆔 ID: `{usr.id}`\n\n🌐 Site: `{site}`\n🔑 API: `{api}`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]]))

@Client.on_message(filters.command("tiny") & filters.private)
async def tiny_handler(client, message):
    if await get_maintenance() and message.from_user.id != ADMIN:
        return await message.reply_text("**🛠️ Bot is Under Maintenance**",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text("❗ Usage: `/tiny https://example.com/`", quote=True)

    url = parts[1].strip()
    if not url.startswith(("http://", "https://")):
        return await message.reply_text("❗ URL must start with http:// or https://", quote=True)

    try:
        async with httpx.AsyncClient() as client_httpx:
            resp = await client_httpx.get(f"http://tinyurl.com/api-create.php?url={url}")
            short_url = resp.text.strip()
        if not short_url.startswith("http"):
            return await message.reply_text("❌ TinyURL failed. Try another URL.", quote=True)

        sent = await message.reply_text(f"🔗 **ShortLink:**\n\n`{short_url}`",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]]))
        await asyncio.sleep(300)
        try: await sent.delete()
        except: pass
    except Exception as e:
        await message.reply_text(f"❌ Failed with TinyURL: {e}", quote=True)

@Client.on_message(filters.text & filters.private & ~filters.command(["tiny", "stats", "broadcast"]))
async def shorten_link_handler(_, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        return await m.reply_text("**🛠️ Bot is Under Maintenance**")

    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")

    if IS_FSUB and not await get_fsub(_, m): return

    txt = m.text
    if txt.startswith("/"):
        return

    usr = m.from_user
    api = await tb.get_value("api", user_id=usr.id)
    site = await tb.get_value("shortner", user_id=usr.id) or "shortzy.in"

    if not api:
        return await m.reply_text("⚠️ You haven’t set your shortener yet. Use:\n\n`/shortlink shortzy.in YOUR_API_KEY`")

    try:
        short_text = await shorten_urls_in_text(txt, api, site)
        await m.reply_text(
            f"✨ **Your Short Link(s) are Ready!**\n\n{short_text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )
    except Exception as e:
        await m.reply_text(f"Error shortening link: {e}")
