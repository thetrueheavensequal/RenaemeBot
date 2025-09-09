# config.py - Dazai Bot Configuration
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Required Settings
    API_ID = int(os.environ.get("API_ID", ""))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # Database
    DB_URL = os.environ.get("DB_URL", "")  # MongoDB URL
    DB_NAME = os.environ.get("DB_NAME", "DazaiRenameBot")
    
    # Admin & Logging
    ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # Your user ID for admin commands
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))  # Optional log channel
    
    # Optional Premium Session (for 4GB+ files)
    STRING_SESSION = os.environ.get("STRING_SESSION", "")  # Premium account session
    
    # Bot Settings
    PORT = int(os.environ.get("PORT", "8080"))
    MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB for normal, 4GB+ with premium session
    
    # Customization
    BOT_PIC = os.environ.get("BOT_PIC", "")  # Optional bot picture URL
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "")  # Optional support group/channel

class Messages:
    START = """
🎭 **Konnichiwa, {user}!**

*"I've been thinking about it for a while now... The perfect double suicide requires the perfect partner, don't you think?"*

I'm **Dazai Bot**, inspired by Osamu Dazai from Bungo Stray Dogs. Instead of finding creative ways to die, I help you rename your files with style and elegance.

✨ **What I Can Do:**
• Rename any file with custom names
• Add beautiful captions to your files  
• Set custom thumbnails for videos
• Add prefix/suffix to filenames
• Modify file metadata
• Handle files up to 2GB (4GB+ with premium session)

*"Life is too short to have boring filenames, wouldn't you agree?"*

Use /help to see all my abilities."""

    HELP = """
📚 **Dazai's Guide to File Renaming**

*"The beauty is in the details, my friend."*

**🎯 Core Commands:**
• Send any file to rename it
• `/metadata` - Configure file metadata
• `/set_caption` - Set custom caption
• `/set_prefix` - Add prefix to filenames
• `/set_suffix` - Add suffix to filenames

**🖼 Thumbnail Commands:**
• Send a photo to set as thumbnail
• `/view_thumb` - View current thumbnail
• `/del_thumb` - Remove thumbnail

**📝 Caption Commands:**
• `/set_caption` - Set caption template
• `/see_caption` - View current caption
• `/del_caption` - Remove caption

**⚙️ Settings:**
• `/settings` - View all your settings
• `/reset` - Reset all settings

**Variables for Caption:**
`{filename}` - File name
`{filesize}` - File size
`{duration}` - Video duration

*"Even files deserve a touch of poetry."*"""

    ABOUT = """
🎭 **About Dazai Rename Bot**

*"Life and death are but a dream, and dreams are always beautiful."*

🌸 **Bot Name:** {bot_name}
📚 **Version:** 2.0 (Bungo Edition)
🎨 **Theme:** Osamu Dazai (Bungo Stray Dogs)
⚡ **Framework:** Pyrogram {pyrogram_version}
🗄 **Database:** MongoDB

**Created with the aesthetic of:**
• Clean, minimal code
• Fast performance
• Elegant user experience
• No unnecessary complexity

*"Simplicity is the ultimate sophistication."*
— Not Dazai, but he'd agree"""

    RENAME_PROMPT = """
📝 **File Information:**

**Current Name:** `{filename}`
**Size:** `{filesize}`
**Type:** `{filetype}`

*"What beautiful name shall we give this file?"*

**Reply with the new filename** (include extension)
Example: `Dazai's Guide.pdf`"""

    UPLOAD_PROGRESS = """
📤 **Uploading Your File...**

{progress_bar}
**Progress:** {percentage}%
**Speed:** {speed}
**ETA:** {eta}

*"Good things come to those who wait..."*"""

    DOWNLOAD_PROGRESS = """
📥 **Downloading Your File...**

{progress_bar}
**Progress:** {percentage}%
**Speed:** {speed}
**ETA:** {eta}

*"Patience is a virtue I'm still learning..."*"""
