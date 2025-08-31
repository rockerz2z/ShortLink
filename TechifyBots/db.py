from typing import Any
from config import *
from motor import motor_asyncio
from datetime import datetime, timedelta

client: motor_asyncio.AsyncIOMotorClient[Any] = motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]

class Techifybots:
    def __init__(self):
        self.users = db["users"]
        self.banned_users = db["banned_users"]
        self.withdrawals = db["withdrawals"]
        self.analytics = db["analytics"]
        self.cache: dict[int, dict[str, Any]] = {}

    async def add_user(self, user_id: int, name: str) -> dict[str, Any] | None:
        try:
            user: dict[str, Any] = {
                "user_id": user_id,
                "name": name,
                "shortner": None,
                "api": None,
                "balance": 0.0,
                "last_shorten_date": None
            }
            await self.users.insert_one(user)
            self.cache[user_id] = user
            return user
        except Exception as e:
            print("Error in addUser:", e)

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        try:
            if user_id in self.cache:
                return self.cache[user_id]
            user = await self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            print("Error in getUser:", e)
            return None

    async def get_all_users(self) -> list[dict[str, Any]]:
        try:
            users: list[dict[str, Any]] = []
            async for user in self.users.find():
                users.append(user)
            return users
        except Exception as e:
            print("Error in getAllUsers:", e)
            return []

    async def ban_user(self, user_id: int, reason: str = None) -> bool:
        try:
            ban = {"user_id": user_id, "reason": reason}
            await self.banned_users.insert_one(ban)
            return True
        except Exception as e:
            print("Error in banUser:", e)
            return False

    async def unban_user(self, user_id: int) -> bool:
        try:
            result = await self.banned_users.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            print("Error in unbanUser:", e)
            return False

    async def is_user_banned(self, user_id: int) -> bool:
        try:
            user = await self.banned_users.find_one({"user_id": user_id})
            return user is not None
        except Exception as e:
            print("Error in isUserBanned:", e)
            return False

    async def set_shortner(self, user_id: int, shortner: str, api: str):
        try:
            await self.users.update_one(
                {'user_id': user_id},
                {'$set': {'shortner': shortner, 'api': api}},
                upsert=True
            )
        except Exception as e:
            print("Error in set_shortner:", e)

    async def get_value(self, key: str, user_id: int):
        try:
            user = await self.users.find_one({'user_id': user_id})
            if user:
                return user.get(key)
        except Exception as e:
            print("Error in get_value:", e)
            return None
            
    async def get_user_balance(self, user_id: int) -> float:
        user = await self.users.find_one({"user_id": user_id})
        return user.get("balance", 0.0) if user else 0.0

    async def update_user_balance(self, user_id: int, amount: float):
        await self.users.update_one({"user_id": user_id}, {"$inc": {"balance": amount}})
        
    async def record_withdrawal_request(self, user_id: int, amount: float, method: str):
        withdrawal_request = {
            "user_id": user_id,
            "amount": amount,
            "method": method,
            "status": "pending",
            "timestamp": datetime.now()
        }
        await self.withdrawals.insert_one(withdrawal_request)
        
    async def get_withdrawal_history(self, user_id: int) -> list[dict[str, Any]]:
        return await self.withdrawals.find({"user_id": user_id}).sort("timestamp", -1).to_list(length=None)

    async def record_analytics(self, user_id: int, event_type: str, data: dict = {}):
        analytics_data = {
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": datetime.now(),
            "data": data
        }
        await self.analytics.insert_one(analytics_data)
        
    async def get_analytics_data(self, start_date: datetime, end_date: datetime) -> dict:
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
        ]
        results = await self.analytics.aggregate(pipeline).to_list(length=None)
        return {item["_id"]: item["count"] for item in results}

tb = Techifybots()
