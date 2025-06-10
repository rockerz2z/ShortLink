from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from Script import text
from config import *

@Client.on_callback_query()
async def callback_query_handler(client, query: CallbackQuery):
    if query.data == "close":
        await query.message.delete()

    elif query.data == "help":
        await query.message.edit_text(
            text.HELP.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴜᴩᴅᴀᴛᴇꜱ", url="https://telegram.me/Techifybots"),
                 InlineKeyboardButton("ꜱᴜᴩᴩᴏʀᴛ", url="https://telegram.me/TechifySupport")],
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back"),
                 InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data="close")]
            ])
        )

    elif query.data == "about":
        await query.message.edit_text(
            text.ABOUT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💥 ʀᴇᴘᴏ", url="https://github.com/TechifyBots/ShortLink"),
                 InlineKeyboardButton("👨‍💻 ᴏᴡɴᴇʀ", user_id=int(ADMIN))],
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back"),
                 InlineKeyboardButton("ᴄʟᴏꜱᴇ", callback_data="close")]
            ])
        )

    elif query.data == "back":
        await query.message.edit_text(
            text.START.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about"),
                 InlineKeyboardButton("ʜᴇʟᴘ", callback_data="help")],
                [InlineKeyboardButton("♻ ᴅᴇᴠᴇʟᴏᴘᴇʀ ♻", user_id=int(ADMIN))]
            ])
        )
