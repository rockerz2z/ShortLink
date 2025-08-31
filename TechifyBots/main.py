import asyncio
import httpx
import re
from pyrogram import Client, filters
from pyrogram.types import Message

from TechifyBots.db import get_user, save_user

# ================ HELPERS =================
async def api_request(domain: str, api_key: str, params: dict):
    url = f"https://{domain}/api"
    params["api"] = api_key
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ================ COMMANDS =================
async def start_cmd(client: Client, m: Message):
    await m.reply_text(
        "👋 Welcome!\n\n"
        "Use /setapi <domain> <apikey> to connect your shortener account.\n"
        "Example: /setapi touchurl.xyz myapikey"
    )


async def setapi_cmd(client: Client, m: Message):
    try:
        _, domain, api_key = m.text.split(maxsplit=2)
    except:
        return await m.reply_text("Usage: /setapi <domain> <apikey>")
    save_user(m.from_user.id, domain, api_key)
    await m.reply_text(f"✅ API connected for {domain}")


async def shorten_cmd(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user:
        return await m.reply_text("❌ Set your API first using /setapi")
    try:
        url = m.text.split(maxsplit=1)[1]
    except:
        return await m.reply_text("Usage: /shorten <url>")
    if "t.me" in url or "telegram.me" in url:
        return await m.reply_text("⏩ Skipped Telegram link")
    domain, api_key, _ = user
    data = await api_request(domain, api_key, {"url": url})
    if data.get("status") == "success":
        await m.reply_text(f"🔗 {data['shortenedUrl']}")
    else:
        await m.reply_text(f"❌ Error: {data.get('message')}")


async def bulk_cmd(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user:
        return await m.reply_text("❌ Set your API first using /setapi")
    try:
        links = m.text.split(maxsplit=1)[1].splitlines()
    except:
        return await m.reply_text("Usage: /bulk <link1>\n<link2>\n...")
    domain, api_key, _ = user
    result = []
    for link in links:
        if "t.me" in link:
            result.append(f"⏩ Skipped: {link}")
            continue
        data = await api_request(domain, api_key, {"url": link})
        if data.get("status") == "success":
            result.append(data['shortenedUrl'])
        else:
            result.append(f"❌ {link}")
    await m.reply_text("\n".join(result))


async def forwarded_handler(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user or not m.text:
        return
    domain, api_key, _ = user
    urls = re.findall(r'https?://\S+', m.text)
    if not urls:
        return
    result = []
    for url in urls:
        if "t.me" in url:
            result.append(f"⏩ Skipped: {url}")
            continue
        data = await api_request(domain, api_key, {"url": url})
        if data.get("status") == "success":
            result.append(data['shortenedUrl'])
        else:
            result.append(f"❌ {url}")
    await m.reply_text("\n".join(result))


async def balance_cmd(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user:
        return await m.reply_text("❌ Set your API first using /setapi")
    domain, api_key, _ = user
    data = await api_request(domain, api_key, {"type": "balance"})
    await m.reply_text(str(data))


async def profile_cmd(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user:
        return await m.reply_text("❌ Set your API first using /setapi")
    domain, api_key, _ = user
    data = await api_request(domain, api_key, {"type": "user"})
    await m.reply_text(str(data))


async def withdraw_cmd(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user:
        return await m.reply_text("❌ Set your API first using /setapi")
    try:
        amount = m.text.split(maxsplit=1)[1]
    except:
        return await m.reply_text("Usage: /withdraw <amount>")
    domain, api_key, _ = user
    data = await api_request(domain, api_key, {"type": "withdraw", "amount": amount})
    await m.reply_text(str(data))


async def withdraw_history_cmd(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user:
        return await m.reply_text("❌ Set your API first using /setapi")
    domain, api_key, _ = user
    data = await api_request(domain, api_key, {"type": "withdraw_history"})
    await m.reply_text(str(data))


async def stats_cmd(client: Client, m: Message):
    user = get_user(m.from_user.id)
    if not user:
        return await m.reply_text("❌ Set your API first using /setapi")
    try:
        period = m.text.split(maxsplit=1)[1]
    except:
        return await m.reply_text("Usage: /stats <daily|weekly|monthly>")
    domain, api_key, _ = user
    data = await api_request(domain, api_key, {"type": "stats", "period": period})
    await m.reply_text(str(data))


# =========== Notifications & Reminders ===========
async def notify_withdrawals(app: Client):
    while True:
        users = get_user("all")
        for u in users:
            user_id, domain, api_key, threshold = u
            bal = await api_request(domain, api_key, {"type": "balance"})
            if isinstance(bal, dict) and float(bal.get("balance", 0)) >= threshold:
                try:
                    await app.send_message(user_id, f"💰 Your balance {bal['balance']} reached the threshold. Time to withdraw!")
                except:
                    pass
        await asyncio.sleep(3600)  # check every hour


# ================ REGISTER HANDLERS =================
def register_handlers(app: Client):
    app.add_handler(filters.command("start"), start_cmd)
    app.add_handler(filters.command("setapi"), setapi_cmd)
    app.add_handler(filters.command("shorten"), shorten_cmd)
    app.add_handler(filters.command("bulk"), bulk_cmd)
    app.add_handler(filters.forwarded, forwarded_handler)
    app.add_handler(filters.command("balance"), balance_cmd)
    app.add_handler(filters.command("profile"), profile_cmd)
    app.add_handler(filters.command("withdraw"), withdraw_cmd)
    app.add_handler(filters.command("withdraw_history"), withdraw_history_cmd)
    app.add_handler(filters.command("stats"), stats_cmd)
