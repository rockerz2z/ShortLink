from pyrogram import Client, filters
from pyrogram.errors import *
from pyrogram.types import *
import httpx
import asyncio
from config import *
import random
from .db import tb
from shortzy import Shortzy
from .fsub import get_fsub
from Script import text
from .maintenance import get_maintenance
import re
from datetime import datetime, timedelta

# ------------------ SHORTNER HANDLERS ------------------

async def short_link(link, user_id):
    usite = await tb.get_value("shortner", user_id=user_id)
    uapi = await tb.get_value("api", user_id=user_id)

    if not usite or not uapi:
        return link  # fallback to original if not set

    shortzy = Shortzy(api_key=uapi, base_site=usite)

    # If input is a single link
    if link.startswith("http://") or link.startswith("https://"):
        return await shortzy.convert(link)
    else:
        # If input contains multiple links in text
        return await shortzy.convert_from_text(link)

async def save_data(tst_url, tst_api, user_id):
    shortzy = Shortzy(api_key=tst_api, base_site=tst_url)
    link = "https://telegram.me/R2k_bots"
    try:
        short = await shortzy.convert(link)
    except Exception:
        return False
    if short and short.startswith("http"):
        await tb.set_shortner(user_id=user_id, shortner=tst_url, api=tst_api)
        return True
    return False

# ------------------ COMMAND HANDLERS ------------------

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
                [InlineKeyboardButton("ℹ️ 𝖠𝖻𝗈𝗎𝗍", callback_data="about"),
                 InlineKeyboardButton("📚 𝖧𝖾𝗅𝗉", callback_data="help")],
                [InlineKeyboardButton("👨‍💻 𝖣𝖾𝗏𝖾𝗅𝗈𝗉𝖾𝗋 👨‍💻", user_id=int(ADMIN))]
            ])
        )
    except Exception as u:
        await m.reply(f"**❌ Error:** `{str(u)}`")

@Client.on_message(filters.command('shortlink') & filters.private)
async def save_shortlink(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))

    if IS_FSUB and not await get_fsub(c, m):
        return

    if len(m.command) < 3:
        return await m.reply_text(
            "**❌ Please provide both the Shortener URL and API key along with the command.**\n\n"
            "Example: `/shortlink example.com your_api_key`\n\n>❤️‍🔥 By: @R2k_bots",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )

    usr = m.from_user
    elg = await save_data(
        m.command[1].replace("/", "").replace("https:", "").replace("http:", ""),
        m.command[2],
        user_id=usr.id
    )

    if elg:
        await m.reply_text(
            f"**✅ Shortener has been set successfully!**\n\n"
            f"🌐 Shortener URL - `{await tb.get_value('shortner', user_id=usr.id)}`\n"
            f"🔑 Shortener API - `{await tb.get_value('api', user_id=usr.id)}`\n\n"
            f">❤️‍🔥 By: @R2k_bots",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )
    else:
        await m.reply_text(
            "**⚠️ Error: Invalid Shortlink API or URL, please check again!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )

@Client.on_message(filters.command('info') & filters.private)
async def showinfo(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))

    usr = m.from_user
    site = await tb.get_value('shortner', user_id=usr.id)
    api = await tb.get_value('api', user_id=usr.id)
    balance = await tb.get_user_balance(user_id=usr.id)

    await m.reply_text(
        f"**Your Information**\n\n👤 User: {usr.mention}\n🆔 User ID: `{usr.id}`\n\n"
        f"🌐 Connected Site: `{site}`\n🔗 Connected API: `{api}`\n\n"
        f"💰 **Current Balance:** `{balance}`\n\n"
        f">❤️‍🔥 By: @R2k_bots",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
    )

@Client.on_message(filters.command("tiny") & filters.private)
async def tiny_handler(client, message):
    if await get_maintenance() and message.from_user.id != ADMIN:
        return await message.reply_text("**🛠️ Bot is Under Maintenance**",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text("❗ Send a valid URL.\n\n◉ `/tiny https://youtube.com/`", quote=True)

    url = parts[1].strip()
    if not url.startswith(("http://", "https://")):
        return await message.reply_text("❗ URL must start with http:// or https://", quote=True)

    try:
        async with httpx.AsyncClient() as client_httpx:
            resp = await client_httpx.get(f"http://tinyurl.com/api-create.php?url={url}")
            short_url = resp.text.strip()

        if not short_url.startswith("http"):
            return await message.reply_text("❌ TinyURL could not shorten this link. Try a different URL.", quote=True)

        sent = await message.reply_text(
            f"🔗 **ShortLink:**\n\n`{short_url}`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )

        await asyncio.sleep(300)
        try:
            await sent.delete()
        except Exception:
            pass
    except Exception as e:
        await message.reply_text(f"❌ Failed to shorten using TinyURL: {e}", quote=True)

# New command handlers
@Client.on_message(filters.command('balance') & filters.private)
async def show_balance(c, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        return await m.reply_text("**🛠️ Bot is Under Maintenance**",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    
    balance = await tb.get_user_balance(m.from_user.id)
    await m.reply_text(f"💰 **Your Current Balance:** `{balance}`\n\n**Minimum Withdrawal Threshold:** `{WITHDRAW_THRESHOLD}`")

@Client.on_message(filters.command('withdraw') & filters.private)
async def withdraw_command(c, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        return await m.reply_text("**🛠️ Bot is Under Maintenance**",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))

    try:
        command_parts = m.text.split(maxsplit=2)
        if len(command_parts) < 3:
            return await m.reply_text("Usage: /withdraw [amount] [payment_method]")
        
        amount = float(command_parts[1])
        payment_method = command_parts[2]

        user_balance = await tb.get_user_balance(m.from_user.id)
        if amount > user_balance:
            return await m.reply_text("❌ You do not have enough balance to withdraw that amount.")
        if amount < WITHDRAW_THRESHOLD:
            return await m.reply_text(f"❌ Minimum withdrawal amount is {WITHDRAW_THRESHOLD}")
        
        # Record the withdrawal request
        await tb.record_withdrawal_request(m.from_user.id, amount, payment_method)
        await tb.update_user_balance(m.from_user.id, -amount)
        
        # Notify user and admin
        await m.reply_text("✅ Your withdrawal request has been submitted and is pending approval.")
        await c.send_message(WITHDRAWAL_NOTIFICATION_CHANNEL, f"New withdrawal request from user `{m.from_user.id}` for `{amount}` via `{payment_method}`.")

    except ValueError:
        await m.reply_text("❌ Please provide a valid amount.")
    except Exception as e:
        await m.reply_text(f"An error occurred: {str(e)}")

@Client.on_message(filters.command('withdrawhistory') & filters.private)
async def show_withdraw_history(c, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        return await m.reply_text("**🛠️ Bot is Under Maintenance**",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))

    history = await tb.get_withdrawal_history(m.from_user.id)
    if not history:
        return await m.reply_text("No withdrawal history found.")
    
    msg = "**Your Withdrawal History:**\n\n"
    for item in history:
        status = item.get("status")
        msg += f"**Amount:** `{item['amount']}`\n"
        msg += f"**Method:** `{item['method']}`\n"
        msg += f"**Status:** `{status}`\n"
        msg += f"**Date:** `{item['timestamp'].strftime('%Y-%m-%d %H:%M')}`\n\n"
    
    await m.reply_text(msg)

@Client.on_message(filters.forwarded & filters.private)
async def forwarded_link_handler(_, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        return await m.reply_text("**🛠️ Bot is Under Maintenance**",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))
    
    text = m.caption or m.text
    if not text:
        return await m.reply_text("No links or text found in the forwarded message.")

    urls = re.findall(r'https?://[^\s]+', text)
    if not urls:
        return await m.reply_text("No links found in the forwarded message.")

    shortened_urls = []
    for url in urls:
        short = await short_link(link=url, user_id=m.from_user.id)
        if short and short.startswith("http"):
            shortened_urls.append(f"• `{short}`")
        else:
            shortened_urls.append(f"• `{url}` (failed to shorten)")
            
    msg = "**✨ Your Short Link(s) are Ready!**\n\n" + "\n".join(shortened_urls)
    await m.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]]))
    await tb.record_analytics(m.from_user.id, "links_shortened", {"count": len(urls)})


# ------------------ AUTO SHORTEN TEXT HANDLER ------------------

@Client.on_message(filters.text & filters.private & ~filters.command(["tiny", "stats", "broadcast", "balance", "withdraw", "withdrawhistory"]))
async def shorten_link_handler(_, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        await m.delete()
        return await m.reply_text("**🛠️ Bot is Under Maintenance**",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))

    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**",
                             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", user_id=int(ADMIN))]]))

    if IS_FSUB and not await get_fsub(_, m):
        return

    txt = m.text
    if txt.startswith("/"):
        return
    
    urls = re.findall(r'https?://[^\s]+', txt)
    if not urls:
        return await m.reply_text("Please send a valid link to shorten.")
    
    usr = m.from_user
    try:
        shortened_urls = []
        for url in urls:
            short = await short_link(link=url, user_id=usr.id)
            if short and short.startswith("http"):
                shortened_urls.append(f"• `{short}`")
            else:
                shortened_urls.append(f"• `{url}` (failed to shorten)")

        msg = f"**✨ Your Short Link(s) are Ready!**\n\n" + "\n".join(shortened_urls)
        await m.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]]))
        await tb.record_analytics(m.from_user.id, "links_shortened", {"count": len(urls)})

    except Exception as e:
        await m.reply_text(f"Error shortening link: {e}")
