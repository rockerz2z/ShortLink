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
        self.analytics = db["analytics"]
        self.withdrawals = db["withdrawals"]
        self.notifications = db["notifications"]
        self.cache: dict[int, dict[str, Any]] = {}

    async def add_user(self, user_id: int, name: str) -> dict[str, Any] | None:
        try:
            user: dict[str, Any] = {
                "user_id": user_id,
                "name": name,
                "shortner": None,
                "api": None,
                "balance": 0.0,
                "total_links": 0,
                "total_clicks": 0,
                "today_links": 0,
                "today_clicks": 0,
                "last_click_update": datetime.now(),
                "min_withdraw": 5.0,
                "joined_date": datetime.now()
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

    # Balance related methods
    async def add_balance(self, user_id: int, amount: float):
        try:
            await self.users.update_one(
                {'user_id': user_id},
                {'$inc': {'balance': amount}},
                upsert=True
            )
            if user_id in self.cache:
                self.cache[user_id]['balance'] = self.cache[user_id].get('balance', 0) + amount
        except Exception as e:
            print("Error in add_balance:", e)

    async def get_balance(self, user_id: int) -> float:
        try:
            user = await self.users.find_one({'user_id': user_id})
            return user.get('balance', 0.0) if user else 0.0
        except Exception as e:
            print("Error in get_balance:", e)
            return 0.0

    # Analytics methods
    async def add_link_click(self, user_id: int, clicks: int = 1):
        try:
            today = datetime.now().date()
            await self.users.update_one(
                {'user_id': user_id},
                {
                    '$inc': {
                        'total_clicks': clicks,
                        'today_clicks': clicks
                    },
                    '$set': {'last_click_update': datetime.now()}
                },
                upsert=True
            )
            
            # Store daily analytics
            await self.analytics.update_one(
                {'user_id': user_id, 'date': today},
                {
                    '$inc': {'clicks': clicks},
                    '$set': {'updated_at': datetime.now()}
                },
                upsert=True
            )
        except Exception as e:
            print("Error in add_link_click:", e)

    async def add_link_created(self, user_id: int, count: int = 1):
        try:
            today = datetime.now().date()
            await self.users.update_one(
                {'user_id': user_id},
                {
                    '$inc': {
                        'total_links': count,
                        'today_links': count
                    }
                },
                upsert=True
            )
            
            # Store daily analytics
            await self.analytics.update_one(
                {'user_id': user_id, 'date': today},
                {
                    '$inc': {'links_created': count},
                    '$set': {'updated_at': datetime.now()}
                },
                upsert=True
            )
        except Exception as e:
            print("Error in add_link_created:", e)

    async def get_analytics(self, user_id: int, period: str = "daily"):
        try:
            user = await self.users.find_one({'user_id': user_id})
            if not user:
                return None

            if period == "daily":
                return {
                    'today_links': user.get('today_links', 0),
                    'today_clicks': user.get('today_clicks', 0),
                    'total_links': user.get('total_links', 0),
                    'total_clicks': user.get('total_clicks', 0)
                }
            elif period == "weekly":
                week_ago = datetime.now() - timedelta(days=7)
                analytics = await self.analytics.find({
                    'user_id': user_id,
                    'date': {'$gte': week_ago.date()}
                }).to_list(None)
                
                total_clicks = sum(item.get('clicks', 0) for item in analytics)
                total_links = sum(item.get('links_created', 0) for item in analytics)
                
                return {
                    'weekly_links': total_links,
                    'weekly_clicks': total_clicks,
                    'total_links': user.get('total_links', 0),
                    'total_clicks': user.get('total_clicks', 0)
                }
            elif period == "monthly":
                month_ago = datetime.now() - timedelta(days=30)
                analytics = await self.analytics.find({
                    'user_id': user_id,
                    'date': {'$gte': month_ago.date()}
                }).to_list(None)
                
                total_clicks = sum(item.get('clicks', 0) for item in analytics)
                total_links = sum(item.get('links_created', 0) for item in analytics)
                
                return {
                    'monthly_links': total_links,
                    'monthly_clicks': total_clicks,
                    'total_links': user.get('total_links', 0),
                    'total_clicks': user.get('total_clicks', 0)
                }
        except Exception as e:
            print("Error in get_analytics:", e)
            return None

    # Withdrawal methods
    async def create_withdrawal(self, user_id: int, amount: float, method: str, details: str):
        try:
            withdrawal = {
                'user_id': user_id,
                'amount': amount,
                'method': method,
                'details': details,
                'status': 'pending',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            result = await self.withdrawals.insert_one(withdrawal)
            
            # Deduct from user balance
            await self.users.update_one(
                {'user_id': user_id},
                {'$inc': {'balance': -amount}}
            )
            
            return str(result.inserted_id)
        except Exception as e:
            print("Error in create_withdrawal:", e)
            return None

    async def get_withdrawals(self, user_id: int, limit: int = 10):
        try:
            withdrawals = await self.withdrawals.find(
                {'user_id': user_id}
            ).sort('created_at', -1).limit(limit).to_list(None)
            return withdrawals
        except Exception as e:
            print("Error in get_withdrawals:", e)
            return []

    async def update_withdrawal_status(self, withdrawal_id: str, status: str):
        try:
            from bson import ObjectId
            result = await self.withdrawals.update_one(
                {'_id': ObjectId(withdrawal_id)},
                {
                    '$set': {
                        'status': status,
                        'updated_at': datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print("Error in update_withdrawal_status:", e)
            return False

    async def check_min_withdraw_threshold(self, user_id: int):
        try:
            user = await self.users.find_one({'user_id': user_id})
            if user:
                balance = user.get('balance', 0.0)
                min_withdraw = user.get('min_withdraw', 5.0)
                return balance >= min_withdraw
            return False
        except Exception as e:
            print("Error in check_min_withdraw_threshold:", e)
            return False

tb = Techifybots()
