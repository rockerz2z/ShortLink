import motor.motor_asyncio

# MongoDB connection (update with your DB URL if not set in env)
MONGO_URL = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client["shortlink_bot"]

users_col = db["users"]
withdraws_col = db["withdrawals"]


# ----------------- USER MANAGEMENT -----------------

async def add_user(user_id: int, api_key: str, domain: str = "https://get2short.com", min_withdraw: float = 5.0):
    """Add new user or update existing user"""
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {
            "api_key": api_key,
            "domain": domain,
            "min_withdraw": min_withdraw
        }},
        upsert=True
    )


async def get_user(user_id: int):
    """Fetch user settings"""
    return await users_col.find_one({"user_id": user_id})


async def update_threshold(user_id: int, min_withdraw: float):
    """Update minimum withdraw threshold"""
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"min_withdraw": min_withdraw}}
    )


# ----------------- WITHDRAWALS -----------------

async def log_withdraw(user_id: int, amount: float, status: str = "pending"):
    """Log a new withdraw request"""
    await withdraws_col.insert_one({
        "user_id": user_id,
        "amount": amount,
        "status": status
    })


async def update_withdraw_status(user_id: int, withdraw_id, status: str):
    """Update withdrawal status"""
    await withdraws_col.update_one(
        {"_id": withdraw_id, "user_id": user_id},
        {"$set": {"status": status}}
    )


async def get_withdraw_history(user_id: int, limit: int = 10):
    """Fetch last few withdrawal records"""
    cursor = withdraws_col.find({"user_id": user_id}).sort("_id", -1).limit(limit)
    return await cursor.to_list(length=limit)
