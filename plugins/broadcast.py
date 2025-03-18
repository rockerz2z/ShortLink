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
        if wait_time > 600:  # If flood wait is more than 10 minutes, stop retrying
            return 500, f"{user_id} : FloodWait too long ({wait_time}s)\n"
        await asyncio.sleep(wait_time)
        return await send_msg(user_id, message)
    except (InputUserDeactivated, UserIsBlocked):
        return 400, f"{user_id} : User Deactivated/Blocked\n"
    except Exception as e:
        return 500, f"{user_id} : {str(e)}\n"

@Client.on_message(filters.private & filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast(c, m):
    broadcast_ids = {}
    
    all_users = [user async for user in db.coll.find()]
    broadcast_msg = m.reply_to_message
    
    out = await m.reply_text(text="Broadcast Started!")
    start_time = time.time()
    total_users = await db.total_users()
    done = 0
    failed = 0
    success = 0
    broadcast_ids["broadcast"] = {"total": total_users, "current": done, "failed": failed, "success": success}

    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        for user in all_users:
            user_id = int(user['id'])
            sts, msg = await send_msg(user_id=user_id, message=broadcast_msg)
            if msg is not None:
                await broadcast_log_file.write(msg)
            if sts == 200:
                success += 1
            else:
                failed += 1
            done += 1

            broadcast_ids["broadcast"].update({"current": done, "failed": failed, "success": success})

    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    
    if failed == 0:
        await m.reply_text(
            text=f"Broadcast completed in `{completed_in}`\n\nTotal users: {total_users}.\nDone: {done}, Success: {success}, Failed: {failed}",
            quote=True
        )
    else:
        await m.reply_document(
            document='broadcast.txt',
            caption=f"Broadcast completed in `{completed_in}`\n\nTotal users: {total_users}.\nDone: {done}, Success: {success}, Failed: {failed}"
        )
    
    os.remove('broadcast.txt')
