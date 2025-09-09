# database.py - Clean Database Handler
import motor.motor_asyncio
from datetime import datetime
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(Config.DB_URL)
        self.db = self._client[Config.DB_NAME]
        self.users = self.db.users
        
    def new_user(self, user_id):
        return {
            "_id": user_id,
            "join_date": datetime.now(),
            "thumbnail": None,
            "caption": None,
            "prefix": "",
            "suffix": "",
            "metadata": {
                "enabled": False,
                "author": "Dazai Bot",
                "title": None
            },
            "settings": {
                "auto_rename": False,
                "show_progress": True
            },
            "stats": {
                "files_renamed": 0,
                "last_used": datetime.now()
            }
        }
    
    async def add_user(self, user_id, username=None):
        """Add new user if not exists"""
        if not await self.user_exists(user_id):
            user = self.new_user(user_id)
            if username:
                user["username"] = username
            await self.users.insert_one(user)
            logger.info(f"New user added: {user_id}")
            return True
        else:
            # Update last used time
            await self.users.update_one(
                {"_id": user_id},
                {"$set": {"stats.last_used": datetime.now()}}
            )
        return False
    
    async def user_exists(self, user_id):
        """Check if user exists"""
        user = await self.users.find_one({"_id": user_id})
        return bool(user)
    
    async def get_user(self, user_id):
        """Get user data"""
        user = await self.users.find_one({"_id": user_id})
        if not user:
            await self.add_user(user_id)
            user = await self.users.find_one({"_id": user_id})
        return user
    
    # Thumbnail methods
    async def set_thumbnail(self, user_id, file_id):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"thumbnail": file_id}}
        )
    
    async def get_thumbnail(self, user_id):
        user = await self.get_user(user_id)
        return user.get("thumbnail")
    
    async def delete_thumbnail(self, user_id):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"thumbnail": None}}
        )
    
    # Caption methods
    async def set_caption(self, user_id, caption):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"caption": caption}}
        )
    
    async def get_caption(self, user_id):
        user = await self.get_user(user_id)
        return user.get("caption")
    
    async def delete_caption(self, user_id):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"caption": None}}
        )
    
    # Prefix/Suffix methods
    async def set_prefix(self, user_id, prefix):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"prefix": prefix}}
        )
    
    async def get_prefix(self, user_id):
        user = await self.get_user(user_id)
        return user.get("prefix", "")
    
    async def set_suffix(self, user_id, suffix):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"suffix": suffix}}
        )
    
    async def get_suffix(self, user_id):
        user = await self.get_user(user_id)
        return user.get("suffix", "")
    
    # Metadata methods
    async def set_metadata(self, user_id, enabled=None, author=None, title=None):
        update_dict = {}
        if enabled is not None:
            update_dict["metadata.enabled"] = enabled
        if author:
            update_dict["metadata.author"] = author
        if title:
            update_dict["metadata.title"] = title
        
        if update_dict:
            await self.users.update_one(
                {"_id": user_id},
                {"$set": update_dict}
            )
    
    async def get_metadata(self, user_id):
        user = await self.get_user(user_id)
        return user.get("metadata", {})
    
    # Stats methods
    async def increment_renamed_count(self, user_id):
        await self.users.update_one(
            {"_id": user_id},
            {
                "$inc": {"stats.files_renamed": 1},
                "$set": {"stats.last_used": datetime.now()}
            }
        )
    
    async def get_stats(self, user_id):
        user = await self.get_user(user_id)
        return user.get("stats", {})
    
    # Admin methods
    async def total_users_count(self):
        return await self.users.count_documents({})
    
    async def get_all_users(self):
        return self.users.find({})
    
    async def delete_user(self, user_id):
        await self.users.delete_one({"_id": user_id})
    
    # Reset user settings
    async def reset_user_settings(self, user_id):
        """Reset all user settings to default"""
        await self.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "thumbnail": None,
                    "caption": None,
                    "prefix": "",
                    "suffix": "",
                    "metadata": {
                        "enabled": False,
                        "author": "Dazai Bot",
                        "title": None
                    }
                }
            }
        )

# Initialize database
db = Database()
