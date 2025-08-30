
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import ADMIN
from .db import tb
from datetime import datetime

@Client.on_message(filters.command('balance') & filters.private)
async def balance_handler(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")
    
    user_id = m.from_user.id
    balance = await tb.get_balance(user_id)
    
    await m.reply_text(
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

@Client.on_message(filters.command('withdraw') & filters.private)
async def withdraw_handler(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")
    
    user_id = m.from_user.id
    balance = await tb.get_balance(user_id)
    
    if balance < 5.0:
        return await m.reply_text(
            f"❌ **Insufficient Balance**\n\n"
            f"💵 Your Balance: `₹{balance:.2f}`\n"
            f"💸 Minimum Withdrawal: `₹5.00`\n\n"
            f"💡 You need `₹{5.0 - balance:.2f}` more to withdraw!"
        )
    
    await m.reply_text(
        f"💸 **Withdrawal Request**\n\n"
        f"💵 Available Balance: `₹{balance:.2f}`\n\n"
        f"📝 **Instructions:**\n"
        f"Reply with: `/withdraw_request <amount> <method> <details>`\n\n"
        f"**Example:**\n"
        f"`/withdraw_request 10 UPI 9876543210@paytm`\n"
        f"`/withdraw_request 25 Bank ACCOUNT_NUMBER`\n\n"
        f"**Supported Methods:** UPI, Bank, PayPal, Paytm"
    )

@Client.on_message(filters.command('withdraw_request') & filters.private)
async def withdraw_request_handler(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")
    
    args = m.text.split(maxsplit=3)
    if len(args) < 4:
        return await m.reply_text(
            "❌ **Invalid Format**\n\n"
            "Use: `/withdraw_request <amount> <method> <details>`\n"
            "Example: `/withdraw_request 10 UPI 9876543210@paytm`"
        )
    
    try:
        amount = float(args[1])
        method = args[2].upper()
        details = args[3]
    except ValueError:
        return await m.reply_text("❌ **Invalid amount!** Please enter a valid number.")
    
    user_id = m.from_user.id
    balance = await tb.get_balance(user_id)
    
    if amount < 5.0:
        return await m.reply_text("❌ **Minimum withdrawal amount is ₹5.00**")
    
    if amount > balance:
        return await m.reply_text(f"❌ **Insufficient balance!** You have ₹{balance:.2f}")
    
    if method not in ['UPI', 'BANK', 'PAYPAL', 'PAYTM']:
        return await m.reply_text("❌ **Invalid method!** Use: UPI, Bank, PayPal, or Paytm")
    
    withdrawal_id = await tb.create_withdrawal(user_id, amount, method, details)
    
    if withdrawal_id:
        # Notify admin
        try:
            await c.send_message(
                ADMIN,
                f"💸 **New Withdrawal Request**\n\n"
                f"👤 User: {m.from_user.mention}\n"
                f"🆔 User ID: `{user_id}`\n"
                f"💰 Amount: `₹{amount:.2f}`\n"
                f"🏦 Method: `{method}`\n"
                f"📋 Details: `{details}`\n"
                f"🆔 Request ID: `{withdrawal_id}`\n\n"
                f"⏰ Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{withdrawal_id}"),
                     InlineKeyboardButton("❌ Reject", callback_data=f"reject_{withdrawal_id}")],
                    [InlineKeyboardButton("📋 All Requests", callback_data="all_withdrawals")]
                ])
            )
        except Exception as e:
            print(f"Error notifying admin: {e}")
        
        await m.reply_text(
            f"✅ **Withdrawal Request Submitted**\n\n"
            f"🆔 Request ID: `{withdrawal_id}`\n"
            f"💰 Amount: `₹{amount:.2f}`\n"
            f"🏦 Method: `{method}`\n"
            f"📋 Details: `{details}`\n\n"
            f"⏳ Status: **Pending**\n"
            f"📧 You will be notified once processed!\n\n"
            f">❤️‍🔥 By: @R2k_bots"
        )
    else:
        await m.reply_text("❌ **Error creating withdrawal request!** Please try again.")

@Client.on_message(filters.command('withdraw_history') & filters.private)
async def withdraw_history_handler(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")
    
    user_id = m.from_user.id
    withdrawals = await tb.get_withdrawals(user_id, 10)
    
    if not withdrawals:
        return await m.reply_text(
            "📋 **Withdrawal History**\n\n"
            "❌ No withdrawal requests found!\n\n"
            "💡 Start earning by sharing links!"
        )
    
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
    
    await m.reply_text(
        history_text + ">❤️‍🔥 By: @R2k_bots",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
    )

@Client.on_message(filters.command('analytics') & filters.private)
async def analytics_handler(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")
    
    user_id = m.from_user.id
    
    await m.reply_text(
        "📊 **Select Analytics Period**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Daily", callback_data="analytics_daily"),
             InlineKeyboardButton("📈 Weekly", callback_data="analytics_weekly")],
            [InlineKeyboardButton("📊 Monthly", callback_data="analytics_monthly"),
             InlineKeyboardButton("📋 Profile", callback_data="profile")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )

@Client.on_message(filters.command('profile') & filters.private)
async def profile_handler(c, m):
    if await tb.is_user_banned(m.from_user.id):
        return await m.reply("**🚫 You are banned from using this bot**")
    
    user_id = m.from_user.id
    user_data = await tb.get_user(user_id)
    
    if not user_data:
        return await m.reply_text("❌ User data not found!")
    
    balance = user_data.get('balance', 0.0)
    total_links = user_data.get('total_links', 0)
    total_clicks = user_data.get('total_clicks', 0)
    joined_date = user_data.get('joined_date', datetime.now())
    shortner = user_data.get('shortner', 'Not Set')
    
    earnings_per_click = 0.01  # ₹0.01 per click
    estimated_earnings = total_clicks * earnings_per_click
    
    await m.reply_text(
        f"👤 **Profile Information**\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"👤 Name: {m.from_user.mention}\n"
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
