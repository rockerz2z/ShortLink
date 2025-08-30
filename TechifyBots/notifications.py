
from pyrogram import Client
from .db import tb
from config import ADMIN
from datetime import datetime
import asyncio

async def send_withdrawal_notification(client: Client, user_id: int, withdrawal_id: str, status: str, amount: float):
    """Send withdrawal status notification to user"""
    status_messages = {
        'pending': '⏳ **Withdrawal Pending**\n\nYour withdrawal request is being reviewed.',
        'approved': '✅ **Withdrawal Approved**\n\nYour withdrawal has been approved and will be processed soon.',
        'completed': '💚 **Withdrawal Completed**\n\nYour withdrawal has been successfully processed!',
        'cancelled': '❌ **Withdrawal Cancelled**\n\nYour withdrawal request has been cancelled.',
        'rejected': '🚫 **Withdrawal Rejected**\n\nYour withdrawal request has been rejected.'
    }
    
    message = (
        f"{status_messages.get(status, '❓ Withdrawal Status Updated')}\n\n"
        f"💰 Amount: `₹{amount:.2f}`\n"
        f"🆔 Request ID: `{withdrawal_id}`\n"
        f"📅 Time: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n\n"
        f">❤️‍🔥 By: @R2k_bots"
    )
    
    try:
        await client.send_message(user_id, message)
    except Exception as e:
        print(f"Error sending notification to {user_id}: {e}")

async def check_withdraw_threshold_reminders(client: Client):
    """Check and send withdrawal threshold reminders"""
    try:
        all_users = await tb.get_all_users()
        
        for user in all_users:
            user_id = user['user_id']
            if await tb.check_min_withdraw_threshold(user_id):
                balance = await tb.get_balance(user_id)
                
                # Check if reminder was sent recently (avoid spam)
                last_reminder = user.get('last_withdraw_reminder')
                if last_reminder:
                    time_diff = datetime.now() - last_reminder
                    if time_diff.days < 7:  # Don't remind more than once a week
                        continue
                
                reminder_message = (
                    f"💰 **Withdrawal Reminder**\n\n"
                    f"🎉 Great news! You have reached the minimum withdrawal threshold.\n\n"
                    f"💵 Current Balance: `₹{balance:.2f}`\n"
                    f"💸 Minimum Withdrawal: `₹5.00`\n\n"
                    f"💡 **Ready to withdraw?** Use /withdraw command!\n\n"
                    f">❤️‍🔥 By: @R2k_bots"
                )
                
                try:
                    await client.send_message(user_id, reminder_message)
                    # Update last reminder time
                    await tb.users.update_one(
                        {'user_id': user_id},
                        {'$set': {'last_withdraw_reminder': datetime.now()}}
                    )
                except Exception as e:
                    print(f"Error sending reminder to {user_id}: {e}")
                
                # Add small delay to avoid rate limits
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Error in check_withdraw_threshold_reminders: {e}")

async def start_notification_scheduler(client: Client):
    """Start the notification scheduler"""
    while True:
        try:
            await check_withdraw_threshold_reminders(client)
        except Exception as e:
            print(f"Error in notification scheduler: {e}")
        
        # Run every 24 hours
        await asyncio.sleep(86400)
