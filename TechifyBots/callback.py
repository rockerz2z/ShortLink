from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import httpx
from .db import get_user, log_withdraw, get_withdraw_history


# ----------- CALLBACK HANDLER -----------

@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    # Get user info from DB
    user = await get_user(user_id)
    if not user:
        return await query.message.edit_text("❌ You must set your API key first using /setapikey")

    api_key = user["api_key"]
    domain = user.get("domain", "https://get2short.com")
    min_withdraw = user.get("min_withdraw", 5.0)

    # ----------- CHECK BALANCE -----------
    if data == "check_balance":
        async with httpx.AsyncClient() as client_http:
            try:
                r = await client_http.get(f"{domain}/api/balance?api={api_key}")
                bal = r.json().get("balance", 0)
                await query.message.edit_text(f"💰 Your Balance: {bal} USD")
            except Exception as e:
                await query.message.edit_text(f"⚠️ Error: {e}")

    # ----------- REQUEST WITHDRAW -----------
    elif data == "withdraw":
        async with httpx.AsyncClient() as client_http:
            try:
                # Example withdraw call
                r = await client_http.get(f"{domain}/api/withdraw?api={api_key}")
                res = r.json()

                if res.get("status") == "success":
                    amount = res.get("amount", 0)
                    await log_withdraw(user_id, amount, "pending")
                    await query.message.edit_text(f"✅ Withdrawal of {amount}$ requested. Status: Pending")
                else:
                    await query.message.edit_text(f"❌ Withdraw failed: {res.get('message')}")
            except Exception as e:
                await query.message.edit_text(f"⚠️ Error: {e}")

    # ----------- WITHDRAW HISTORY -----------
    elif data == "withdraw_history":
        history = await get_withdraw_history(user_id, limit=5)
        if not history:
            return await query.message.edit_text("📜 No withdrawal history found.")

        text = "📜 **Your Last Withdrawals:**\n\n"
        for h in history:
            text += f"- {h['amount']}$ → `{h['status']}`\n"

        await query.message.edit_text(text)

    # ----------- PROFILE INFO -----------
    elif data == "profile":
        text = (
            f"👤 **Your Profile Info:**\n\n"
            f"🔑 API Key: `{api_key[:6]}...{api_key[-6:]}`\n"
            f"🌐 Domain: {domain}\n"
            f"💵 Min Withdraw Reminder: {min_withdraw}$\n"
        )
        await query.message.edit_text(text)

    # ----------- MAIN MENU -----------
    elif data == "menu":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Balance", callback_data="check_balance")],
            [InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("📜 History", callback_data="withdraw_history")],
            [InlineKeyboardButton("👤 Profile", callback_data="profile")]
        ])
        await query.message.edit_text("📍 Main Menu", reply_markup=kb)
