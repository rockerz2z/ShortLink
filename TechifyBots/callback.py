from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from TechifyBots.db import db

@Client.on_callback_query()
async def callback_handlers(client, query: CallbackQuery):
    user_id = query.from_user.id

    if query.data == "balance":
        balance = db.get_balance(user_id)
        await query.message.edit_text(f"💰 Your current balance: {balance} INR")

    elif query.data == "withdraw":
        min_withdraw = db.get_min_withdraw(user_id)
        balance = db.get_balance(user_id)
        if balance >= min_withdraw:
            db.create_withdraw_request(user_id, balance)
            await query.message.edit_text("✅ Withdrawal request submitted.")
        else:
            await query.message.edit_text(f"⚠️ Minimum withdraw is {min_withdraw} INR.")

    elif query.data == "history":
        history = db.get_withdraw_history(user_id)
        if history:
            text = "📜 Your Withdrawal History:\n\n"
            for h in history:
                text += f"💵 {h['amount']} INR - {h['status']}\n"
        else:
            text = "ℹ️ No withdrawal history found."
        await query.message.edit_text(text)

    elif query.data == "profile":
        profile = db.get_user_profile(user_id)
        text = (f"👤 Profile Info:\n\n"
                f"ID: {user_id}\n"
                f"Name: {profile['name']}\n"
                f"Domain: {profile['domain']}\n"
                f"API Key: {profile['api_key'][:6]}... (hidden)")
        await query.message.edit_text(text)
