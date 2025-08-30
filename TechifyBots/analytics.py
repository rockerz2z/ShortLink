
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from .db import tb
from datetime import datetime, timedelta

async def send_analytics(m, period: str):
    user_id = m.from_user.id
    analytics = await tb.get_analytics(user_id, period)
    
    if not analytics:
        return await m.edit_text(
            "❌ **No analytics data found!**\n\n"
            "💡 Start creating links to see your analytics.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )
    
    period_name = period.title()
    period_key = f"{period}_links" if period != "daily" else "today_links"
    clicks_key = f"{period}_clicks" if period != "daily" else "today_clicks"
    
    links_created = analytics.get(period_key, 0)
    clicks_received = analytics.get(clicks_key, 0)
    total_links = analytics.get('total_links', 0)
    total_clicks = analytics.get('total_clicks', 0)
    
    # Calculate earnings (₹0.01 per click)
    period_earnings = clicks_received * 0.01
    total_earnings = total_clicks * 0.01
    
    # Calculate click rate
    click_rate = (clicks_received / links_created * 100) if links_created > 0 else 0
    
    analytics_text = (
        f"📊 **{period_name} Analytics**\n\n"
        f"📈 **{period_name} Performance**\n"
        f"🔗 Links Created: `{links_created}`\n"
        f"👆 Clicks Received: `{clicks_received}`\n"
        f"💰 Earnings: `₹{period_earnings:.2f}`\n"
        f"📊 Click Rate: `{click_rate:.1f}%`\n\n"
        f"📊 **Total Performance**\n"
        f"🔗 Total Links: `{total_links}`\n"
        f"👆 Total Clicks: `{total_clicks}`\n"
        f"💎 Total Earnings: `₹{total_earnings:.2f}`\n\n"
        f">❤️‍🔥 By: @R2k_bots"
    )
    
    await m.edit_text(
        analytics_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Daily", callback_data="analytics_daily"),
             InlineKeyboardButton("📈 Weekly", callback_data="analytics_weekly")],
            [InlineKeyboardButton("📊 Monthly", callback_data="analytics_monthly"),
             InlineKeyboardButton("💰 Balance", callback_data="check_balance")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )
