from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from Script import text
from config import ADMIN
from .db import tb
from .analytics import send_analytics
from .notifications import send_withdrawal_notification

@Client.on_callback_query()
async def callback_query_handler(client, query: CallbackQuery):
    if query.data == "start":
        await query.message.edit_caption(
            caption=text.START.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ℹ️ 𝖠𝖻𝗈𝗎𝗍", callback_data="about"),
                 InlineKeyboardButton("📚 𝖧𝖾𝗅𝗉", callback_data="help")],
                [InlineKeyboardButton("👨‍💻 𝖣𝖾𝗏𝖾𝗅𝗈𝗉𝖾𝗋 👨‍💻", url="https://t.me/ProfessorR2K")]

            ])
        )

    elif query.data == "help":
        await query.message.edit_caption(
            caption=text.HELP,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 𝖴𝗉𝖽𝖺𝗍𝖾𝗌", url="https://telegram.me/R2K_Bots"),
                 InlineKeyboardButton("💬 𝖲𝗎𝗉𝗉𝗈𝗋𝗍", url="https://telegram.me/ProfessorR2K")],
                [InlineKeyboardButton("↩️ 𝖡𝖺𝖼𝗄", callback_data="start"),
                 InlineKeyboardButton("❌ 𝖢𝗅𝗈𝗌𝖾", callback_data="close")]
            ])
        )

    elif query.data == "about":
        await query.message.edit_caption(
            caption=text.ABOUT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👨‍💻 𝖣𝖾𝗏𝖾𝗅𝗈𝗉𝖾𝗋 👨‍💻", url="https://t.me/ProfessorR2K")],
                [InlineKeyboardButton("↩️ 𝖡𝖺𝖼𝗄", callback_data="start"),
                 InlineKeyboardButton("❌ 𝖢𝗅𝗈𝗌𝖾", callback_data="close")]
            ])
        )

    elif query.data == "close":
        await query.message.delete()

    # Balance and Analytics callbacks
    elif query.data == "check_balance":
        user_id = query.from_user.id
        balance = await tb.get_balance(user_id)
        
        await query.message.edit_text(
            f"💰 **Your Balance**\n\n"
            f"💵 Current Balance: `₹{balance:.2f}`\n"
            f"💸 Minimum Withdrawal: `₹5.00`\n\n"
            f"💡 **Tip:** Share more links to earn more money!\n\n"
            f">❤️‍🔥 By: @R2k_bots",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
                 InlineKeyboardButton("📊 Analytics", callback_data="analytics")],
                [InlineKeyboardButton("📈 Profile", callback_data="profile"),
                 InlineKeyboardButton("📋 History", callback_data="withdraw_history")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    elif query.data == "withdraw":
        user_id = query.from_user.id
        balance = await tb.get_balance(user_id)
        
        if balance < 5.0:
            await query.answer(
                f"❌ Insufficient Balance! You have ₹{balance:.2f}. Minimum ₹5.00 required.",
                show_alert=True
            )
        else:
            await query.message.edit_text(
                f"💸 **Withdrawal Request**\n\n"
                f"💵 Available Balance: `₹{balance:.2f}`\n\n"
                f"📝 **Instructions:**\n"
                f"Use command: `/withdraw_request <amount> <method> <details>`\n\n"
                f"**Example:**\n"
                f"`/withdraw_request 10 UPI 9876543210@paytm`\n"
                f"`/withdraw_request 25 Bank ACCOUNT_NUMBER`\n\n"
                f"**Supported Methods:** UPI, Bank, PayPal, Paytm",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 History", callback_data="withdraw_history"),
                     InlineKeyboardButton("💰 Balance", callback_data="check_balance")],
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )

    elif query.data == "analytics":
        await query.message.edit_text(
            "📊 **Select Analytics Period**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📅 Daily", callback_data="analytics_daily"),
                 InlineKeyboardButton("📈 Weekly", callback_data="analytics_weekly")],
                [InlineKeyboardButton("📊 Monthly", callback_data="analytics_monthly"),
                 InlineKeyboardButton("📋 Profile", callback_data="profile")],
                [InlineKeyboardButton("💰 Balance", callback_data="check_balance"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    elif query.data.startswith("analytics_"):
        period = query.data.split("_")[1]
        await send_analytics(query.message, period)

    elif query.data == "profile":
        user_id = query.from_user.id
        user_data = await tb.get_user(user_id)
        
        if not user_data:
            await query.answer("❌ User data not found!", show_alert=True)
            return
        
        balance = user_data.get('balance', 0.0)
        total_links = user_data.get('total_links', 0)
        total_clicks = user_data.get('total_clicks', 0)
        joined_date = user_data.get('joined_date')
        shortner = user_data.get('shortner', 'Not Set')
        
        from datetime import datetime
        if not joined_date:
            joined_date = datetime.now()
        
        earnings_per_click = 0.01
        estimated_earnings = total_clicks * earnings_per_click
        
        await query.message.edit_text(
            f"👤 **Profile Information**\n\n"
            f"🆔 User ID: `{user_id}`\n"
            f"👤 Name: {query.from_user.mention}\n"
            f"📅 Joined: `{joined_date.strftime('%d/%m/%Y')}`\n\n"
            f"💰 **Financial Summary**\n"
            f"💵 Balance: `₹{balance:.2f}`\n"
            f"💎 Estimated Earnings: `₹{estimated_earnings:.2f}`\n\n"
            f"📊 **Statistics**\n"
            f"🔗 Total Links: `{total_links}`\n"
            f"👆 Total Clicks: `{total_clicks}`\n"
            f"📈 Click Rate: `{(total_clicks/total_links*100):.1f}%`\n\n" if total_links > 0 else f"📈 Click Rate: `0%`\n\n"
            f"🌐 **Settings**\n"
            f"🔗 Shortener: `{shortner}`\n\n"
            f">❤️‍🔥 By: @R2k_bots",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Balance", callback_data="check_balance"),
                 InlineKeyboardButton("📊 Analytics", callback_data="analytics")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    elif query.data == "withdraw_history":
        user_id = query.from_user.id
        withdrawals = await tb.get_withdrawals(user_id, 10)
        
        if not withdrawals:
            await query.message.edit_text(
                "📋 **Withdrawal History**\n\n"
                "❌ No withdrawal requests found!\n\n"
                "💡 Start earning by sharing links!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
            )
            return
        
        history_text = "📋 **Withdrawal History** (Last 10)\n\n"
        
        for w in withdrawals:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'completed': '💚',
                'cancelled': '❌',
                'rejected': '🚫'
            }.get(w['status'], '❓')
            
            history_text += (
                f"{status_emoji} **₹{w['amount']:.2f}** - {w['method']}\n"
                f"📅 {w['created_at'].strftime('%d/%m/%Y %H:%M')}\n"
                f"📊 Status: {w['status'].title()}\n\n"
            )
        
        await query.message.edit_text(
            history_text + ">❤️‍🔥 By: @R2k_bots",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Balance", callback_data="check_balance"),
                 InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    # Admin withdrawal management callbacks
    elif query.data.startswith("approve_") and query.from_user.id == ADMIN:
        withdrawal_id = query.data.split("_")[1]
        success = await tb.update_withdrawal_status(withdrawal_id, "approved")
        
        if success:
            # Get withdrawal details to notify user
            from bson import ObjectId
            withdrawal = await tb.withdrawals.find_one({'_id': ObjectId(withdrawal_id)})
            if withdrawal:
                await send_withdrawal_notification(
                    query.bot, 
                    withdrawal['user_id'], 
                    withdrawal_id, 
                    "approved", 
                    withdrawal['amount']
                )
            
            await query.message.edit_text(
                f"✅ **Withdrawal Approved**\n\n"
                f"🆔 Request ID: `{withdrawal_id}`\n"
                f"📧 User has been notified.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Mark Completed", callback_data=f"complete_{withdrawal_id}")],
                    [InlineKeyboardButton("📋 All Requests", callback_data="all_withdrawals")]
                ])
            )
        else:
            await query.answer("❌ Failed to approve withdrawal!", show_alert=True)

    elif query.data.startswith("reject_") and query.from_user.id == ADMIN:
        withdrawal_id = query.data.split("_")[1]
        
        # Get withdrawal details to refund user
        from bson import ObjectId
        withdrawal = await tb.withdrawals.find_one({'_id': ObjectId(withdrawal_id)})
        if withdrawal:
            # Refund the amount
            await tb.add_balance(withdrawal['user_id'], withdrawal['amount'])
            
            success = await tb.update_withdrawal_status(withdrawal_id, "rejected")
            
            if success:
                await send_withdrawal_notification(
                    query.bot, 
                    withdrawal['user_id'], 
                    withdrawal_id, 
                    "rejected", 
                    withdrawal['amount']
                )
                
                await query.message.edit_text(
                    f"🚫 **Withdrawal Rejected**\n\n"
                    f"🆔 Request ID: `{withdrawal_id}`\n"
                    f"💰 Amount refunded to user balance\n"
                    f"📧 User has been notified.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 All Requests", callback_data="all_withdrawals")]
                    ])
                )
            else:
                await query.answer("❌ Failed to reject withdrawal!", show_alert=True)

    elif query.data.startswith("complete_") and query.from_user.id == ADMIN:
        withdrawal_id = query.data.split("_")[1]
        success = await tb.update_withdrawal_status(withdrawal_id, "completed")
        
        if success:
            # Get withdrawal details to notify user
            from bson import ObjectId
            withdrawal = await tb.withdrawals.find_one({'_id': ObjectId(withdrawal_id)})
            if withdrawal:
                await send_withdrawal_notification(
                    query.bot, 
                    withdrawal['user_id'], 
                    withdrawal_id, 
                    "completed", 
                    withdrawal['amount']
                )
            
            await query.message.edit_text(
                f"💚 **Withdrawal Completed**\n\n"
                f"🆔 Request ID: `{withdrawal_id}`\n"
                f"📧 User has been notified.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 All Requests", callback_data="all_withdrawals")]
                ])
            )
        else:
            await query.answer("❌ Failed to complete withdrawal!", show_alert=True)
