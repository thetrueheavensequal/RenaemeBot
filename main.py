# bot.py - Dazai Themed Rename Bot
import asyncio
import logging
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from datetime import datetime
import pytz

# Elegant logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [Dazai] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('dazai_bot.log'),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class DazaiRenameBot(Client):
    def __init__(self):
        super().__init__(
            name="DazaiRenameBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15
        )
        
    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username
        self.uptime = datetime.now()
        
        # Optional premium session for 4GB+ files
        if Config.STRING_SESSION:
            try:
                self.premium_client = Client(
                    "PremiumSession",
                    api_id=Config.API_ID,
                    api_hash=Config.API_HASH,
                    session_string=Config.STRING_SESSION
                )
                await self.premium_client.start()
                logger.info("Premium session connected for 4GB+ file support")
            except Exception as e:
                logger.error(f"Premium session failed: {e}")
                self.premium_client = None
        else:
            self.premium_client = None
        
        # Notify admin
        startup_msg = (
            f"🎭 **{me.first_name} has awakened**\n\n"
            f"*\"Life is a tragedy when seen in close-up,*\n"
            f"*but a comedy in long-shot.\"*\n"
            f"— Dazai Osamu\n\n"
            f"📚 Version: `v{__version__} (Layer {layer})`\n"
            f"🌸 Time: `{datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        
        if Config.ADMIN_ID:
            try:
                await self.send_message(Config.ADMIN_ID, startup_msg)
            except:
                pass
                
        if Config.LOG_CHANNEL:
            try:
                await self.send_message(Config.LOG_CHANNEL, startup_msg)
            except:
                logger.warning("Could not send to log channel")
        
        logger.info(f"🎭 {me.first_name} is ready for double suicide... I mean, renaming files!")
        
    async def stop(self, *args):
        if hasattr(self, 'premium_client') and self.premium_client:
            await self.premium_client.stop()
        
        if Config.ADMIN_ID:
            try:
                await self.send_message(
                    Config.ADMIN_ID,
                    "🌙 *\"Goodbye... I'm off to find a beautiful way to die.\"*\n— Bot stopping"
                )
            except:
                pass
        
        logger.info("Bot stopped gracefully")
        await super().stop()

if __name__ == "__main__":
    bot = DazaiRenameBot()
    bot.run()
