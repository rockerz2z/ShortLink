import asyncio
import time
import datetime
import os
import aiofiles
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked
from configs import *
from .database import db

async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return 200, None
    except FloodWait as e:
        wait_time = e.value
        if wait_time > 600:  # Stop retrying if flood wait exceeds 10 minutes
            return 500, f"{user_id} : FloodWait too long ({wait_time}s)\n"
        await asyncio.sleep(wait_time)
        return await send_msg(user_id, message)
    except (InputUserDeactivated, UserIsBlocked):
        return 400, f"{user_id} : User Deactivated/Blocked\n"
    except Exception as e:
        return 500, f"{user_id} : {str(e)}\n"

@Client.on_message(filters.private & filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast(c, m):
    broadcast_msg = m.reply_to_message

    # Fetch all users directly inside the function
    all_users = [user async for user in db.coll.find({}, {"id": 1})]
    total_users = len(all_users)

    if total_users == 0:
        return await m.reply_text("No users found in the database!")

    out = await m.reply_text(text="Broadcast Started!")
    start_time = time.time()

    done = failed = success = 0
    async with aiofiles.open("broadcast.txt", "w") as broadcast_log_file:
        for user in all_users:
            user_id = user["id"]
            sts, msg = await send_msg(user_id, broadcast_msg)
            if msg:
                await broadcast_log_file.write(msg)
            if sts == 200:
                success += 1
            else:
                failed += 1
            done += 1

    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await out.delete()

    caption = f"Broadcast completed in `{completed_in}`\n\nTotal: {total_users}\n✅ Success: {success}\n❌ Failed: {failed}"
    if failed == 0:
        await m.reply_text(text=caption, quote=True)
    else:
        await m.reply_document(document="broadcast.txt", caption=caption)
        os.remove("broadcast.txt")
