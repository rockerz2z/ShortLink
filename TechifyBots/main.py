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

    await m.reply_text(
        f"**Your Information**\n\n👤 User: {usr.mention}\n🆔 User ID: `{usr.id}`\n\n"
        f"🌐 Connected Site: `{site}`\n🔗 Connected API: `{api}`\n\n>❤️‍🔥 By: @R2k_bots",
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


# ------------------ FORWARDED POST HANDLER ------------------

@Client.on_message(filters.forwarded & filters.private)
async def forwarded_handler(_, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        return await m.reply_text("**🛠️ Bot is Under Maintenance**")

    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")

    if IS_FSUB and not await get_fsub(_, m):
        return

    # Process forwarded messages with media and text
    if m.text or m.caption:
        text_content = m.text or m.caption or ""

        # Skip if no links found
        if not ("http://" in text_content or "https://" in text_content):
            return

        # Skip telegram links
        if "t.me/" in text_content or "telegram.me/" in text_content:
            return await m.reply_text("🚫 Telegram links are not supported for shortening.")

        try:
            # Shorten links in the forwarded content
            short_content = await short_link(link=text_content, user_id=m.from_user.id)

            # Add to analytics
            link_count = text_content.count("http://") + text_content.count("https://")
            await tb.add_link_created(m.from_user.id, link_count)

            # Simulate some clicks and earnings (you can integrate with actual shortener API for real data)
            import random
            clicks = random.randint(0, 5)  # Random clicks for demo
            if clicks > 0:
                await tb.add_link_click(m.from_user.id, clicks)
                await tb.add_balance(m.from_user.id, clicks * 0.01)  # ₹0.01 per click

            # Send the shortened content with media if present
            if m.photo:
                await m.reply_photo(
                    photo=m.photo.file_id,
                    caption=f"**✨ Shortened Links from Forwarded Post**\n\n{short_content}\n\n>❤️‍🔥 By: @R2k_bots",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
                )
            elif m.video:
                await m.reply_video(
                    video=m.video.file_id,
                    caption=f"**✨ Shortened Links from Forwarded Post**\n\n{short_content}\n\n>❤️‍🔥 By: @R2k_bots",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
                )
            elif m.document:
                await m.reply_document(
                    document=m.document.file_id,
                    caption=f"**✨ Shortened Links from Forwarded Post**\n\n{short_content}\n\n>❤️‍🔥 By: @R2k_bots",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
                )
            else:
                await m.reply_text(
                    f"**✨ Shortened Links from Forwarded Post**\n\n{short_content}\n\n>❤️‍🔥 By: @R2k_bots",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
                )

        except Exception as e:
            await m.reply_text(f"Error processing forwarded post: {e}")

# ------------------ BULK LINK SHORTENER ------------------

@Client.on_message(filters.command('bulk') & filters.private)
async def bulk_handler(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")

    if IS_FSUB and not await get_fsub(c, m):
        return

    await m.reply_text(
        "📦 **Bulk Link Shortener**\n\n"
        "📝 **Instructions:**\n"
        "• Send multiple links (one per line)\n"
        "• Maximum 20 links per request\n"
        "• Telegram links will be skipped\n\n"
        "**Example:**\n"
        "```\n"
        "https://google.com\n"
        "https://youtube.com\n"
        "https://github.com\n"
        "```\n\n"
        "💡 Just send your links in the next message!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="close")]])
    )

# ------------------ AUTO SHORTEN TEXT HANDLER ------------------

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "tiny", "stats", "broadcast", "bulk", "balance", "withdraw", "withdraw_request", "analytics", "profile", "withdraw_history"]))
async def shorten_link_handler(_, m):
    if await get_maintenance() and m.from_user.id != ADMIN:
        return await m.reply_text("**🛠️ Bot is Under Maintenance**")

    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")

    if IS_FSUB and not await get_fsub(_, m):
        return

    # Check if the message contains a valid URL
    text = m.text.strip()
    if not (text.startswith("http://") or text.startswith("https://")):
        return await m.reply_text(
            "📎 **Please send a valid link to shorten.**\n\n"
            "✅ **Accepted formats:**\n"
            "• `https://example.com`\n"
            "• `http://example.com`\n\n"
            "💡 **Tip:** Make sure your link starts with http:// or https://",
            quote=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )

    try:
        loading_msg = await m.reply_text("🔄 **Shortening your link...**", quote=True)

        short_url = await short_link(text, m.from_user.id)

        if short_url and short_url != text:
            await tb.add_balance(m.from_user.id, 0.01)
            await loading_msg.edit_text(
                f"✅ **Link Shortened Successfully!**\n\n"
                f"🔗 **Original:** `{text}`\n"
                f"🔗 **Short Link:** `{short_url}`\n\n"
                f"💰 **Earnings:** +₹0.01",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
            )
        else:
            await loading_msg.edit_text(
                "❌ **Failed to shorten link**\n\n"
                "Please check if:\n"
                "• The link is valid and accessible\n"
                "• Your shortener settings are configured\n\n"
                "💡 Use `/profile` to check your shortener settings",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
            )
    except Exception as e:
        await m.reply_text(f"❌ **Error:** {str(e)}", quote=True)
