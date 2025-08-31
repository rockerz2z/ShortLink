from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import *
import asyncio
import re
from config import ADMIN
from .db import tb
from datetime import datetime
from config import WITHDRAWAL_NOTIFICATION_CHANNEL

def parse_button_markup(text: str):
    lines = text.split("\n")
    buttons = []
    final_text_lines = []
    for line in lines:
        row = []
        parts = line.split("||")
        is_button_line = True
        for part in parts:
            match = re.fullmatch(r"\[(.+?)\]\((https?://[^\s]+)\)", part.strip())
            if match:
                row.append(InlineKeyboardButton(match[1], url=match[2]))
            else:
                is_button_line = False
                break
        if is_button_line and row:
            buttons.append(row)
        else:
            final_text_lines.append(line)
    return InlineKeyboardMarkup(buttons) if buttons else None, "\n".join(final_text_lines).strip()


@Client.on_message(filters.command("stats") & filters.private & filters.user(ADMIN))
async def total_users(client, message):
    try:
        users = await tb.get_all_users()
        pending_withdrawals_count = await tb.withdrawals.count_documents({"status": "pending"})
        await message.reply(
            f"👥 **Total Users:** {len(users)}\n\n"
            f"💰 **Pending Withdrawals:** {pending_withdrawals_count}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎭 Close", callback_data="close")]])
        )
    except Exception as e:
        r=await message.reply(f"❌ *Error:* `{str(e)}`")
        await asyncio.sleep(30)
        await r.delete()

@Client.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN))
async def broadcasting_func(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply("<b>Reply to a message to broadcast.</b>")

    msg = await message.reply_text("Processing broadcast...")
    to_copy_msg = message.reply_to_message
    users_list = await tb.get_all_users()
    completed = 0
    failed = 0
    raw_text = to_copy_msg.caption or to_copy_msg.text or ""
    reply_markup, cleaned_text = parse_button_markup(raw_text)

    for i, user in enumerate(users_list):
        user_id = user.get("user_id")
        if not user_id:
            continue
        try:
            if to_copy_msg.text:
                await client.send_message(user_id, cleaned_text, reply_markup=reply_markup)
            elif to_copy_msg.photo:
                await client.send_photo(user_id, to_copy_msg.photo.file_id, caption=cleaned_text, reply_markup=reply_markup)
            elif to_copy_msg.video:
                await client.send_video(user_id, to_copy_msg.video.file_id, caption=cleaned_text, reply_markup=reply_markup)
            elif to_copy_msg.document:
                await client.send_document(user_id, to_copy_msg.document.file_id, caption=cleaned_text, reply_markup=reply_markup)
            else:
                await to_copy_msg.copy(user_id)
            completed += 1
        except (UserIsBlocked, PeerIdInvalid, InputUserDeactivated):
            await tb.delete_user(user_id)
            failed += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await to_copy_msg.copy(user_id)
                completed += 1
            except:
                failed += 1
        except Exception as e:
            print(f"Broadcast to {user_id} failed: {e}")

        await msg.edit(f"Total: {i + 1}\nCompleted: {completed}\nFailed: {failed}")
        await asyncio.sleep(0.1)
    await msg.edit(
        f"😶‍🌫 <b>Broadcast Completed</b>\n\n👥 Total Users: <code>{len(users_list)}</code>\n✅ Successful: <code>{completed}</code>\n🤯 Failed: <code>{failed}</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎭 Close", callback_data="close")]])
    )

@Client.on_message(filters.command("ban") & filters.private & filters.user(ADMIN))
async def ban(c: Client, m: Message):
    try:
        command_parts = m.text.split()
        if len(command_parts) < 2:
            await m.reply_text("Usage: /ban user_id {reason}")
            return
        user_id = int(command_parts[1])
        reason = " ".join(command_parts[2:]) if len(command_parts) > 2 else None
        try:
            user = await c.get_users(user_id)
        except Exception:
            await m.reply_text("Unable to find user.")
            return
        if await tb.ban_user(user_id, reason):
            ban_message = f"User {user.mention} has been banned."
            if reason:
                ban_message += f"\nReason: {reason}"
            await m.reply_text(ban_message)
            try:
                notify = f"You have been banned from using the bot."
                if reason:
                    notify += f"\nReason: {reason}"
                await c.send_message(user_id, notify)
            except Exception:
                await m.reply_text("User banned, but could not send message (maybe they blocked the bot).")
        else:
            await m.reply_text("Failed to ban user.")
    except ValueError:
        await m.reply_text("Please provide a valid user ID.")
    except Exception as e:
        await m.reply_text(f"An error occurred: {str(e)}")

@Client.on_message(filters.command("unban") & filters.private & filters.user(ADMIN))
async def unban(c: Client, m: Message):
    try:
        command_parts = m.text.split()
        if len(command_parts) < 2:
            await m.reply_text("Usage: /unban user_id")
            return
        user_id = int(command_parts[1])
        try:
            user = await c.get_users(user_id)
        except Exception:
            await m.reply_text("Unable to find user.")
            return
        if await tb.unban_user(user_id):
            await m.reply_text(f"User {user.mention} has been unbanned.")
            try:
                await c.send_message(user_id, "You have been unbanned. You can now use the bot again.")
            except Exception:
                await m.reply_text("User unbanned, but could not send message (maybe they blocked the bot).")
        else:
            await m.reply_text("Failed to unban user or user was not banned.")
    except ValueError:
        await m.reply_text("Please provide a valid user ID.")
    except Exception as e:
        await m.reply_text(f"An error occurred: {str(e)}")

@Client.on_message(filters.command('banlist') & filters.private & filters.user(ADMIN))
async def banlist(client, message):
    response = await message.reply("<b>Fetching banned users...</b>")
    try:
        banned_users = await tb.banned_users.find().to_list(length=None)
        if not banned_users:
            return await response.edit("<b>No users are currently banned.</b>")
        text = "<b>🚫 Banned Users:</b>\n\n"
        for user in banned_users:
            user_id = user.get("user_id")
            reason = user.get("reason", "No reason provided")
            text += f"• <code>{user_id}</code> — {reason}\n"
        await response.edit(text)
    except Exception as e:
        await response.edit(f"<b>Error:</b> <code>{str(e)}</code>")

# New admin commands for withdrawal management
@Client.on_message(filters.command("viewwithdrawals") & filters.private & filters.user(ADMIN))
async def view_withdrawals(c, m):
    try:
        pending_withdrawals = await tb.withdrawals.find({"status": "pending"}).to_list(length=None)
        if not pending_withdrawals:
            return await m.reply("<b>No pending withdrawal requests.</b>")
        
        msg = "<b>💰 Pending Withdrawal Requests:</b>\n\n"
        for req in pending_withdrawals:
            user_info = await c.get_users(req["user_id"])
            msg += f"ID: `{req['_id']}`\n"
            msg += f"User: {user_info.mention} (`{req['user_id']}`)\n"
            msg += f"Amount: `{req['amount']}`\n"
            msg += f"Method: `{req['method']}`\n"
            msg += f"Date: `{req['timestamp'].strftime('%Y-%m-%d %H:%M')}`\n\n"
        
        await m.reply(msg)
    except Exception as e:
        await m.reply(f"Error fetching withdrawals: {str(e)}")

@Client.on_message(filters.command("approvewithdraw") & filters.private & filters.user(ADMIN))
async def approve_withdrawal(c, m):
    try:
        req_id = m.text.split(maxsplit=1)[1]
        
        result = await tb.withdrawals.update_one(
            {"_id": ObjectId(req_id), "status": "pending"},
            {"$set": {"status": "approved", "processed_date": datetime.now()}}
        )
        
        if result.modified_count == 1:
            withdrawal_req = await tb.withdrawals.find_one({"_id": ObjectId(req_id)})
            user_id = withdrawal_req["user_id"]
            await m.reply(f"✅ Withdrawal request `{req_id}` approved. Notifying user...")
            try:
                await c.send_message(user_id, f"✅ Your withdrawal request for `{withdrawal_req['amount']}` has been **approved**.")
            except:
                pass
        else:
            await m.reply("❌ Failed to approve. Request not found or not pending.")
    except Exception as e:
        await m.reply(f"Error approving withdrawal: {str(e)}")

@Client.on_message(filters.command("rejectwithdraw") & filters.private & filters.user(ADMIN))
async def reject_withdrawal(c, m):
    try:
        command_parts = m.text.split(maxsplit=2)
        if len(command_parts) < 3:
            return await m.reply("Usage: /rejectwithdraw [request_id] [reason]")
        
        req_id = command_parts[1]
        reason = command_parts[2]
        
        withdrawal_req = await tb.withdrawals.find_one({"_id": ObjectId(req_id), "status": "pending"})
        if not withdrawal_req:
            return await m.reply("❌ Request not found or not pending.")
        
        result = await tb.withdrawals.update_one(
            {"_id": ObjectId(req_id)},
            {"$set": {"status": "rejected", "rejection_reason": reason, "processed_date": datetime.now()}}
        )
        
        if result.modified_count == 1:
            user_id = withdrawal_req["user_id"]
            # Refund the balance
            await tb.update_user_balance(user_id, withdrawal_req["amount"])
            
            await m.reply(f"❌ Withdrawal request `{req_id}` rejected. Notifying user and refunding balance...")
            try:
                await c.send_message(user_id, f"❌ Your withdrawal request for `{withdrawal_req['amount']}` has been **rejected**.\nReason: `{reason}`\n\nYour balance has been refunded.")
            except:
                pass
        else:
            await m.reply("❌ Failed to reject. Request not found.")
    except Exception as e:
        await m.reply(f"Error rejecting withdrawal: {str(e)}")
