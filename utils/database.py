# utils/database.py - Enhanced Database Handler with Dazai Theme
import motor.motor_asyncio
from datetime import datetime, timedelta
from Bot.config import Config
import logging
from typing import Optional, Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)

class EnhancedDatabase:
    """Enhanced database handler with comprehensive user management"""
    
    def __init__(self):
        self._client = None
        self.db = None
        self.users = None
        self._connection_lock = asyncio.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                Config.DATABASE_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=50
            )
            
            # Extract database name from URL or use default
            db_name = getattr(Config, 'DB_NAME', 'dazai_rename_bot')
            if hasattr(Config, 'DATABASE_URL') and '/' in Config.DATABASE_URL:
                try:
                    db_name = Config.DATABASE_URL.split('/')[-1]
                except:
                    pass
            
            self.db = self._client[db_name]
            self.users = self.db.users
            
            logger.info(f"Database initialized: {db_name}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _ensure_connection(self):
        """Ensure database connection is active"""
        async with self._connection_lock:
            try:
                await self._client.admin.command('ismaster')
            except Exception as e:
                logger.warning(f"Database connection lost, reconnecting: {e}")
                self._initialize_database()
    
    def create_user_document(self, user_id: int, username: Optional[str] = None) -> Dict[str, Any]:
        """Create new user document with default settings"""
        now = datetime.now()
        
        user_doc = {
            "_id": user_id,
            "username": username,
            "join_date": now,
            "last_used": now,
            
            # File processing settings
            "thumbnail": None,
            "caption": None,
            "prefix": "",
            "suffix": "",
            
            # Metadata configuration
            "metadata": {
                "enabled": False,
                "author": "",
                "title": ""
            },
            
            # User preferences
            "settings": {
                "auto_rename": False,
                "show_progress": True,
                "default_format": "document",
                "language": "en"
            },
            
            # Statistics
            "stats": {
                "files_renamed": 0,
                "total_size_processed": 0,
                "last_file_date": None,
                "favorite_format": "document",
                "sessions_count": 0
            },
            
            # Activity tracking
            "activity": {
                "last_seen": now,
                "total_commands": 0,
                "daily_usage": {},
                "streak_days": 0
            }
        }
        
        return user_doc
    
    async def add_user(self, user_id: int, username: Optional[str] = None) -> bool:
        """Add new user to database if not exists"""
        try:
            await self._ensure_connection()
            
            # Check if user already exists
            existing_user = await self.users.find_one({"_id": user_id})
            
            if existing_user is None:
                # Create new user
                user_doc = self.create_user_document(user_id, username)
                await self.users.insert_one(user_doc)
                logger.info(f"New user added to database: {user_id}")
                return True
            else:
                # Update username if provided and different
                if username and existing_user.get("username") != username:
                    await self.users.update_one(
                        {"_id": user_id},
                        {"$set": {"username": username, "last_used": datetime.now()}}
                    )
                return False
                
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    async def user_exists(self, user_id: int) -> bool:
        """Check if user exists in database"""
        try:
            await self._ensure_connection()
            user = await self.users.find_one({"_id": user_id}, {"_id": 1})
            return bool(user)
        except Exception as e:
            logger.error(f"Error checking user existence {user_id}: {e}")
            return False
    
    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get complete user data"""
        try:
            await self._ensure_connection()
            user = await self.users.find_one({"_id": user_id})
            
            if not user:
                # Create user if doesn't exist
                await self.add_user(user_id)
                user = await self.users.find_one({"_id": user_id})
            
            return user or {}
            
        except Exception as e:
            logger.error(f"Error getting user data {user_id}: {e}")
            return {}
    
    async def update_user_activity(self, user_id: int):
        """Update user's last activity"""
        try:
            await self._ensure_connection()
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            
            await self.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "last_used": now,
                        "activity.last_seen": now
                    },
                    "$inc": {
                        "activity.total_commands": 1,
                        f"activity.daily_usage.{today}": 1
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating user activity {user_id}: {e}")
    
    # Thumbnail Management
    async def set_thumbnail(self, user_id: int, file_id: str) -> bool:
        """Set user's thumbnail"""
        try:
            await self._ensure_connection()
            result = await self.users.update_one(
                {"_id": user_id},
                {"$set": {"thumbnail": file_id}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error setting thumbnail for {user_id}: {e}")
            return False
    
    async def get_thumbnail(self, user_id: int) -> Optional[str]:
        """Get user's thumbnail"""
        try:
            user_data = await self.get_user_data(user_id)
            return user_data.get("thumbnail")
        except Exception as e:
            logger.error(f"Error getting thumbnail for {user_id}: {e}")
            return None
    
    async def delete_thumbnail(self, user_id: int) -> bool:
        """Delete user's thumbnail"""
        try:
            await self._ensure_connection()
            result = await self.users.update_one(
                {"_id
