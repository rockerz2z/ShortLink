from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from configs import *


@Client.on_callback_query()
async def callback(bot, query):
    me = await bot.get_me()
    data = query.data
    msg = query.message

    if data == "delete":
        await msg.delete()
        try:
            await msg.reply_to_message.delete()
        except:
            pass

    elif data == "help":
        await msg.edit(
            HELP_TXT.format(me.mention),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Repo", url="https://github.com/TechifyBots/ShortLink-Bot"),
                     InlineKeyboardButton("Support", url="https://telegram.me/TechifySupport")],
                    [InlineKeyboardButton("Back", callback_data="start")]
                ]
            )
        )
      
    elif data == "about":
        await msg.edit(
            ABOUT_TXT.format(me.mention),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Back", callback_data="start"),
                     InlineKeyboardButton("Close", callback_data="delete")]
                ]
            )
        )

    elif data == "start":
        await msg.edit(
            START_TXT.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("About", callback_data="about"),
                     InlineKeyboardButton("Help", callback_data="help")],
                    [InlineKeyboardButton("Developer", url="https://youtube.com/@techifybots")]
                ]
            )
        )
