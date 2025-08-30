from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import *
import asyncio
import re
from config import ADMIN
from .db import tb

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
        await message.reply(f"👥 **Total Users:** {len(users)}",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎭 Close", callback_data="close")]]))
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
            failed += 1

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
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import ADMIN
from .db import tb
from .notifications import send_withdrawal_notification

@Client.on_message(filters.command("withdrawals") & filters.user(ADMIN))
async def view_withdrawals(c, m: Message):
    """View all pending withdrawal requests"""
    try:
        # Get pending withdrawals
        pending_withdrawals = await tb.withdrawals.find(
            {'status': 'pending'}
        ).sort('created_at', -1).limit(10).to_list(None)
        
        if not pending_withdrawals:
            return await m.reply_text(
                "📋 **Withdrawal Requests**\n\n"
                "✅ No pending withdrawal requests!"
            )
        
        requests_text = "📋 **Pending Withdrawal Requests**\n\n"
        
        for i, withdrawal in enumerate(pending_withdrawals, 1):
            requests_text += (
                f"**{i}. Request #{str(withdrawal['_id'])}**\n"
                f"👤 User ID: `{withdrawal['user_id']}`\n"
                f"💰 Amount: `₹{withdrawal['amount']:.2f}`\n"
                f"🏦 Method: `{withdrawal['method']}`\n"
                f"📋 Details: `{withdrawal['details']}`\n"
                f"📅 Date: `{withdrawal['created_at'].strftime('%d/%m/%Y %H:%M')}`\n\n"
            )
        
        keyboard = []
        for withdrawal in pending_withdrawals[:5]:  # Show buttons for first 5
            withdrawal_id = str(withdrawal['_id'])
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ Approve #{withdrawal_id[:8]}", 
                    callback_data=f"approve_{withdrawal_id}"
                ),
                InlineKeyboardButton(
                    f"❌ Reject #{withdrawal_id[:8]}", 
                    callback_data=f"reject_{withdrawal_id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="all_withdrawals")])
        
        await m.reply_text(
            requests_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await m.reply_text(f"❌ Error fetching withdrawals: {e}")

@Client.on_message(filters.command("withdrawal_stats") & filters.user(ADMIN))
async def withdrawal_stats(c, m: Message):
    """Get withdrawal statistics"""
    try:
        # Get stats from database
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        week_ago = datetime.now() - timedelta(days=7)
        month_ago = datetime.now() - timedelta(days=30)
        
        # Count withdrawals by status
        total_pending = await tb.withdrawals.count_documents({'status': 'pending'})
        total_approved = await tb.withdrawals.count_documents({'status': 'approved'})
        total_completed = await tb.withdrawals.count_documents({'status': 'completed'})
        total_rejected = await tb.withdrawals.count_documents({'status': 'rejected'})
        
        # Amount statistics
        pipeline = [
            {'$group': {
                '_id': '$status',
                'total_amount': {'$sum': '$amount'},
                'count': {'$sum': 1}
            }}
        ]
        
        amount_stats = {}
        async for result in tb.withdrawals.aggregate(pipeline):
            amount_stats[result['_id']] = {
                'amount': result['total_amount'],
                'count': result['count']
            }
        
        # Today's statistics
        today_withdrawals = await tb.withdrawals.count_documents({
            'created_at': {'$gte': datetime.combine(today, datetime.min.time())}
        })
        
        stats_text = (
            f"📊 **Withdrawal Statistics**\n\n"
            f"📋 **Status Overview**\n"
            f"⏳ Pending: {total_pending}\n"
            f"✅ Approved: {total_approved}\n"
            f"💚 Completed: {total_completed}\n"
            f"🚫 Rejected: {total_rejected}\n\n"
            f"💰 **Amount Statistics**\n"
        )
        
        for status, data in amount_stats.items():
            stats_text += f"{status.title()}: ₹{data['amount']:.2f} ({data['count']} requests)\n"
        
        stats_text += f"\n📅 **Today's Requests:** {today_withdrawals}"
        
        await m.reply_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 View Pending", callback_data="all_withdrawals")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="withdrawal_stats")]
            ])
        )
        
    except Exception as e:
        await m.reply_text(f"❌ Error fetching stats: {e}")

@Client.on_message(filters.command("add_balance") & filters.user(ADMIN))
async def add_balance_admin(c, m: Message):
    """Add balance to user account"""
    args = m.text.split()
    
    if len(args) < 3:
        return await m.reply_text(
            "❌ **Invalid Format**\n\n"
            "Use: `/add_balance <user_id> <amount>`\n"
            "Example: `/add_balance 123456789 10.50`"
        )
    
    try:
        user_id = int(args[1])
        amount = float(args[2])
        
        if amount <= 0:
            return await m.reply_text("❌ Amount must be positive!")
        
        # Check if user exists
        user = await tb.get_user(user_id)
        if not user:
            return await m.reply_text("❌ User not found!")
        
        # Add balance
        await tb.add_balance(user_id, amount)
        new_balance = await tb.get_balance(user_id)
        
        # Notify user
        try:
            await c.send_message(
                user_id,
                f"💰 **Balance Added**\n\n"
                f"💵 Amount Added: `₹{amount:.2f}`\n"
                f"💎 New Balance: `₹{new_balance:.2f}`\n\n"
                f"🎉 Congratulations! Your balance has been updated.\n\n"
                f">❤️‍🔥 By: @R2k_bots"
            )
            notification_status = "✅ User notified"
        except Exception:
            notification_status = "❌ Failed to notify user"
        
        await m.reply_text(
            f"✅ **Balance Added Successfully**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💵 Amount Added: `₹{amount:.2f}`\n"
            f"💎 New Balance: `₹{new_balance:.2f}`\n\n"
            f"📧 {notification_status}"
        )
        
    except ValueError:
        await m.reply_text("❌ Invalid user ID or amount!")
    except Exception as e:
        await m.reply_text(f"❌ Error adding balance: {e}")
