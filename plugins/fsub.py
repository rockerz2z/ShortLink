from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from configs import AUTH_CHANNELS, ADMINS
from pyrogram.errors import RPCError


async def get_fsub(client, message):
    bot = client
    user_id = message.from_user.id
    not_joined = []
    for channel_id in AUTH_CHANNELS:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status == "kicked":
                await message.reply("**🚫 You are banned from using this bot**",
                                    reply_markup=InlineKeyboardMarkup(
                                        [[InlineKeyboardButton("Support", user_id=int(ADMIN))]]
                                    ))
            if member.status in ["left", "restricted"]:
                not_joined.append(channel_id)
        except RPCError:
            not_joined.append(channel_id)
    if not not_joined:
        return True
    buttons = []
    for index, channel_id in enumerate(not_joined, 1):
        try:
            chat = await bot.get_chat(channel_id)
            channel_link = chat.invite_link
            if not channel_link:
                raise ValueError("No invite link available")
            buttons.append(InlineKeyboardButton(f"🔰 Channel {index} 🔰", url=channel_link))
        except Exception as e:
            print(f"Error fetching channel data: {e}")
    formatted_buttons = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    await message.reply(
        f"Dear {message.from_user.mention},\n\n"
        "You need to join our update channels to access all the features of this bot. "
        "Due to server overload, only members of our channels can use the bot. "
        "Thank you for your understanding! 😊\n\n"
        "Please join the following channels to proceed:",
        reply_markup=InlineKeyboardMarkup(formatted_buttons)
    )
    return False
