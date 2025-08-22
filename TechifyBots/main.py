from pyrogram import Client, filters
from pyrogram.errors import *
from pyrogram.types import *
import httpx
import asyncio
import random

from config import *
from .db import tb
from shortzy import Shortzy
from .fsub import get_fsub
from Script import text
from .maintenance import get_maintenance


# ---------- Shortener Functions ----------
async def short_link(link, user_id):
    usite = await tb.get_value("shortner", user_id=user_id)
    uapi = await tb.get_value("api", user_id=user_id) 
    shortzy = Shortzy(api_key=uapi, base_site=usite)
    return await shortzy.convert_from_text(link)

async def save_data(tst_url, tst_api, user_id):
    shortzy = Shortzy(api_key=tst_api, base_site=tst_url)
    link = "https://telegram.me/R2K_Bots"
    short = await shortzy.convert(link)        
    if short.startswith("http"):
        await tb.set_shortner(user_id=user_id, shortner=tst_url, api=tst_api)
        return True
    return False


# ---------- Start Handler ----------
@Client.on_message(filters.command('start') & filters.private)
async def start_handler(c, m):
    try:
        if await tb.is_user_banned(m.from_user.id):
            await m.reply(
                "**🚫 You are banned from using this bot**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Support", url="https://t.me/ProfessorR2K")]
                ])
            )
            return

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
                [
                    InlineKeyboardButton("ℹ️ 𝖠𝖻𝗈𝗎𝗍", callback_data="about"),
                    InlineKeyboardButton("📚 𝖧𝖾𝗅𝗉", callback_data="help")
                ],
                [
                    InlineKeyboardButton("👨‍💻 𝖣𝖾𝗏𝖾𝗅𝗈𝗉𝖾𝗋 👨‍💻", url="https://t.me/ProfessorR2K")
                ]
            ])
        )
    except Exception as u:
        await m.reply(f"**❌ Error:** `{str(u)}`")


# ---------- Save Shortlink ----------
@Client.on_message(filters.command('shortlink') & filters.private)
async def save_shortlink(c, m):
    if await tb.is_user_banned(m.from_user.id):
        await m.reply(
            "**🚫 You are banned from using this bot**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url="https://t.me/ProfessorR2K")]
            ])
        )
        return

    if IS_FSUB and not await get_fsub(c, m):
        return

    if len(m.command) < 3:
        await m.reply_text(
            "**❌ Please provide both the Shortener URL and API key along with the command.**\n\n"
            "Example:\n`/shortlink example.com your_api_key`\n\n>❤️‍🔥 By: @R2K_Bots",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
        return

    usr = m.from_user
    elg = await save_data(
        m.command[1].replace("/", "").replace("https:", "").replace("http:", ""),
        m.command[2],
        user_id=usr.id
    )

    if elg:
        await m.reply_text(
            f"**✅ Shortener has been set successfully!**\n\n"
            f"🌐 URL - `{await tb.get_value('shortner', user_id=usr.id)}`\n"
            f"🔑 API - `{await tb.get_value('api', user_id=usr.id)}`\n\n"
            ">❤️‍🔥 By: @R2K_Bots",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )
    else:       
        await m.reply_text(
            "**⚠️ Error: Your Shortlink API or URL is invalid, please check again!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )


# ---------- Info ----------
@Client.on_message(filters.command('info') & filters.private)
async def showinfo(c, m):
    if await tb.is_user_banned(m.from_user.id):
        await m.reply(
            "**🚫 You are banned from using this bot**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url="https://t.me/ProfessorR2K")]
            ])
        )
        return

    usr = m.from_user
    site = await tb.get_value('shortner', user_id=usr.id)
    api = await tb.get_value('api', user_id=usr.id)

    await m.reply_text(
        f"**Your Information**\n\n"
        f"👤 User: {usr.mention}\n"
        f"🆔 User ID: `{usr.id}`\n\n"
        f"🌐 Connected Site: `{site}`\n"
        f"🔗 Connected API: `{api}`\n\n"
        ">❤️‍🔥 By: @R2K_Bots",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )


# ---------- TinyURL ----------
@Client.on_message(filters.command("tiny") & filters.private)
async def tiny_handler(client, message):
    if await get_maintenance() and message.from_user.id != ADMIN:
        return await message.reply_text(
            "**🛠️ Bot is Under Maintenance**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url="https://t.me/ProfessorR2K")]
            ])
        )

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text(
            "❗ Send a valid URL.\n\nExample:\n`/tiny https://youtube.com/@R2K_Bots`"
        )

    url = parts[1].strip()
    if not url.startswith(("http://", "https://")):
        return await message.reply_text("❗ URL must start with http:// or https://")

    try:
        async with httpx.AsyncClient() as client_httpx:
            resp = await client_httpx.get(f"http://tinyurl.com/api-create.php?url={url}")
            short_url = resp.text.strip()

        if not short_url.startswith("http"):
            return await message.reply_text("❌ TinyURL could not shorten this link.")

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
        sent = await message.reply_text(f"🔗 **ShortLink:**\n\n`{short_url}`", reply_markup=reply_markup)

        await asyncio.sleep(300)
        try:
            await sent.delete()
        except:
            pass
    except Exception as e:
        await message.reply_text(f"❌ Failed to shorten using TinyURL: {e}")


# ---------- Auto Shorten ----------
@Client.on_message(filters.text & filters.private & ~filters.command(["tiny", "stats", "broadcast"]))
async def shorten_link(_, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        await m.delete()
        return await m.reply_text(
            "**🛠️ Bot is Under Maintenance**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url="https://t.me/ProfessorR2K")]
            ])
        )

    if await tb.is_user_banned(m.from_user.id):
        return await m.reply(
            "**🚫 You are banned from using this bot**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url="https://t.me/ProfessorR2K")]
            ])
        )

    if IS_FSUB and not await get_fsub(_, m):
        return

    usr = m.from_user
    txt = m.text.strip() if m.text else ""

    # Case 1: If it's a command (/short <link>)
    if m.text and m.text.startswith("/short"):
        if not m.command or len(m.command) < 2:
            return await m.reply_text(
                "⚠️ Please provide a valid link to shorten.\n\nUsage: `/short https://example.com`",
                parse_mode="MarkdownV2"
            )
        url = m.command[1]

    # Case 2: If user just sends a raw link
    elif "http://" in txt or "https://" in txt:
        url = txt

    else:
        return await m.reply_text("❌ Please send a valid link to shorten.")

    try:
        short = await short_link(link=url, user_id=usr.id)
        msg = (
            "✨ Your Short Link is Ready!\n\n"
            f"🔗 <b>Your Link:</b> <code>{short}</code>\n\n"
            "❤️‍🔥 By: @R2K_Bots"
        )
        await m.reply_text(
            msg,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    except Exception as e:
        await m.reply_text(f"⚠️ Error shortening link: `{e}`", parse_mode="Markdown")
