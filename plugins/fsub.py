from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from configs import AUTH_CHANNELS
from pyrogram.errors import RPCError

async def get_fsub(c, m):
    user_id = m.from_user.id  # Use m instead of message
    not_joined = []

    for channel_id in AUTH_CHANNELS:
        try:
            member = await c.get_chat_member(channel_id, user_id)  # Use c instead of bot

            if member.status in ["left", "kicked", "restricted"]:
                not_joined.append(channel_id)

        except RPCError:
            not_joined.append(channel_id)

    if not not_joined:
        return True

    buttons = []
    temp_buttons = []

    for i, channel_id in enumerate(not_joined, start=1):
        try:
            chat = await c.get_chat(channel_id)  # Use c instead of bot
            channel_link = chat.invite_link

            if not channel_link:
                raise ValueError("No invite link available")

        except Exception:
            channel_link = "https://telegram.me/Techifybots"

        temp_buttons.append(InlineKeyboardButton(f"🔰 Channel {i} 🔰", url=channel_link))

        if len(temp_buttons) == 2:
            buttons.append(temp_buttons)
            temp_buttons = []

    if temp_buttons:
        buttons.append(temp_buttons)  # Add remaining buttons if any

    await m.reply(  # Use m instead of message
        f"Dear {m.from_user.mention()},\n\n"
        "You need to join our update channels to access all the features of this bot. "
        "Due to server overload, only members of our channels can use the bot. "
        "Thank you for your understanding! 😊\n\n"
        "Please join the following channels to proceed:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return False
