# plugins/settings.py - Complete Settings Management with Dazai Theme
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pyrogram.enums import ParseMode
from utils.database import db
from Bot.config import Config
import asyncio
import logging

logger = logging.getLogger(__name__)

# Dazai-themed quotes for settings
DAZAI_QUOTES = {
    "caption_set": "Words are the dress of thoughts, and I've just tailored yours perfectly.",
    "prefix_set": "Every story needs a proper beginning, don't you think?", 
    "suffix_set": "And every tale deserves its elegant conclusion.",
    "thumbnail_set": "A picture speaks volumes, much like the silence between words.",
    "metadata_enabled": "Even files deserve their identity properly documented.",
    "settings_reset": "Sometimes we need to start over completely, like turning to a blank page.",
    "no_caption": "Silence can be more eloquent than words sometimes.",
    "no_thumbnail": "The absence of image is also a form of expression.",
    "operation_cancelled": "Wise decision. Even I know when to retreat."
}

# Caption Management Commands
@Client.on_message(filters.command("set_caption") & (filters.private | filters.group))
async def set_caption_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if in group and handle mentions
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    if len(message.command) > 1:
        # Caption provided directly with command
        caption = " ".join(message.command[1:])
        await db.set_caption(user_id, caption)
        await message.reply_text(
            f"📝 **Caption Set Successfully**\n\n"
            f"Your new caption:\n`{caption}`\n\n"
            f"*\"{DAZAI_QUOTES['caption_set']}\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Ask for caption using ForceReply
        await message.reply_text(
            "📝 **Set Custom Caption**\n\n"
            "Send me your caption template. You can use these variables:\n"
            "• `{filename}` - Original file name\n"
            "• `{filesize}` - File size in human readable format\n"
            "• `{duration}` - Duration for videos/audio\n"
            "• `{filetype}` - File type (video/document/audio)\n\n"
            "**Example:**\n"
            "`📁 {filename}\n💾 Size: {filesize}\n⏱️ Duration: {duration}`\n\n"
            "*Send your caption or /cancel to abort*",
            reply_markup=ForceReply(placeholder="Enter your caption template..."),
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command(["view_caption", "see_caption"]) & (filters.private | filters.group))
async def view_caption_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    caption = await db.get_caption(user_id)
    
    if caption:
        await message.reply_text(
            f"📝 **Your Current Caption Template:**\n\n"
            f"`{caption}`\n\n"
            "Use /del_caption to remove it or /set_caption to change it.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(
            f"❌ **No Caption Template Set**\n\n"
            f"Use /set_caption to create one.\n\n"
            f"*\"{DAZAI_QUOTES['no_caption']}\"*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command(["del_caption", "delete_caption"]) & (filters.private | filters.group))
async def delete_caption_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention  
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    caption = await db.get_caption(user_id)
    
    if not caption:
        return await message.reply_text("❌ You don't have any caption template set.")
    
    await db.delete_caption(user_id)
    await message.reply_text(
        "✅ **Caption Template Deleted**\n\n"
        "*\"Back to the pure essence of simplicity.\"*",
        parse_mode=ParseMode.MARKDOWN
    )

# Thumbnail Management
@Client.on_message(filters.photo & (filters.private | filters.group))
async def handle_thumbnail_photo(client: Client, message: Message):
    user_id = message.from_user.id
    
    # In groups, only process if bot is mentioned or replied to
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.caption or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    # Save thumbnail
    await db.set_thumbnail(user_id, message.photo.file_id)
    
    await message.reply_text(
        "✅ **Thumbnail Set Successfully**\n\n"
        "This image will be used as thumbnail for your videos.\n"
        "• Use /view_thumb to preview it\n"
        "• Use /del_thumb to remove it\n\n"
        f"*\"{DAZAI_QUOTES['thumbnail_set']}\"*",
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_message(filters.command(["view_thumb", "viewthumb"]) & (filters.private | filters.group))
async def view_thumbnail_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    thumb = await db.get_thumbnail(user_id)
    
    if thumb:
        await message.reply_photo(
            thumb,
            caption="🖼️ **Your Current Thumbnail**\n\n"
                   "This will be applied to your renamed videos.\n"
                   "Use /del_thumb to remove it.\n\n"
                   "*\"Beauty captured within a frame, like memories preserved in time.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(
            f"❌ **No Thumbnail Set**\n\n"
            f"Send me a photo to set it as your video thumbnail.\n\n"
            f"*\"{DAZAI_QUOTES['no_thumbnail']}\"*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command(["del_thumb", "delete_thumb"]) & (filters.private | filters.group))
async def delete_thumbnail_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    thumb = await db.get_thumbnail(user_id)
    
    if not thumb:
        return await message.reply_text("❌ You don't have any thumbnail set.")
    
    await db.delete_thumbnail(user_id)
    await message.reply_text(
        "✅ **Thumbnail Deleted**\n\n"
        "*\"Sometimes emptiness holds more meaning than fullness.\"*",
        parse_mode=ParseMode.MARKDOWN
    )

# Prefix & Suffix Management
@Client.on_message(filters.command("set_prefix") & (filters.private | filters.group))
async def set_prefix_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/set_prefix [your prefix]`\n\n"
            "**Examples:**\n"
            "• `/set_prefix [Dazai]` → `[Dazai] filename.mp4`\n"
            "• `/set_prefix BSD_` → `BSD_filename.mp4`\n"
            "• `/set_prefix 📁` → `📁 filename.mp4`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    prefix = " ".join(message.command[1:])
    await db.set_prefix(user_id, prefix)
    
    await message.reply_text(
        f"✅ **Prefix Set Successfully**\n\n"
        f"Your prefix: `{prefix}`\n\n"
        f"Example: `{prefix} filename.ext`\n\n"
        f"*\"{DAZAI_QUOTES['prefix_set']}\"*",
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_message(filters.command("set_suffix") & (filters.private | filters.group))
async def set_suffix_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/set_suffix [your suffix]`\n\n"
            "**Examples:**\n"
            "• `/set_suffix - BSD` → `filename - BSD.mp4`\n"
            "• `/set_suffix _Dazai` → `filename_Dazai.mp4`\n"
            "• `/set_suffix 🎭` → `filename 🎭.mp4`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    suffix = " ".join(message.command[1:])
    await db.set_suffix(user_id, suffix)
    
    await message.reply_text(
        f"✅ **Suffix Set Successfully**\n\n"
        f"Your suffix: `{suffix}`\n\n"
        f"Example: `filename{suffix}.ext`\n\n"
        f"*\"{DAZAI_QUOTES['suffix_set']}\"*",
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_message(filters.command(["view_prefix", "see_prefix"]) & (filters.private | filters.group))
async def view_prefix_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    prefix = await db.get_prefix(user_id)
    
    if prefix:
        await message.reply_text(
            f"🔤 **Your Current Prefix:**\n\n"
            f"`{prefix}`\n\n"
            f"Example output: `{prefix} filename.ext`\n\n"
            "Use /del_prefix to remove it.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(
            "❌ **No Prefix Set**\n\n"
            "Use /set_prefix to set one.",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command(["view_suffix", "see_suffix"]) & (filters.private | filters.group))
async def view_suffix_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    suffix = await db.get_suffix(user_id)
    
    if suffix:
        await message.reply_text(
            f"🔤 **Your Current Suffix:**\n\n"
            f"`{suffix}`\n\n"
            f"Example output: `filename{suffix}.ext`\n\n"
            "Use /del_suffix to remove it.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(
            "❌ **No Suffix Set**\n\n"
            "Use /set_suffix to set one.",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command(["del_prefix", "delete_prefix"]) & (filters.private | filters.group))
async def delete_prefix_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    prefix = await db.get_prefix(user_id)
    
    if not prefix:
        return await message.reply_text("❌ You don't have any prefix set.")
    
    await db.set_prefix(user_id, "")
    await message.reply_text(
        "✅ **Prefix Deleted**\n\n"
        "*\"Back to the beginning, where all stories start.\"*",
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_message(filters.command(["del_suffix", "delete_suffix"]) & (filters.private | filters.group))
async def delete_suffix_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    suffix = await db.get_suffix(user_id)
    
    if not suffix:
        return await message.reply_text("❌ You don't have any suffix set.")
    
    await db.set_suffix(user_id, "")
    await message.reply_text(
        "✅ **Suffix Deleted**\n\n"
        "*\"Endings are just new beginnings in disguise.\"*",
        parse_mode=ParseMode.MARKDOWN
    )

# Metadata Management
@Client.on_message(filters.command("metadata") & (filters.private | filters.group))
async def metadata_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    metadata = await db.get_metadata(user_id)
    
    status = "✅ Enabled" if metadata.get("enabled") else "❌ Disabled"
    author = metadata.get("author", "Not set")
    title = metadata.get("title", "Not set")
    
    keyboard = [
        [
            InlineKeyboardButton(
                "❌ Disable" if metadata.get("enabled") else "✅ Enable",
                callback_data=f"meta_toggle_{user_id}"
            )
        ],
        [
            InlineKeyboardButton("📝 Set Author", callback_data=f"meta_author_{user_id}"),
            InlineKeyboardButton("📝 Set Title", callback_data=f"meta_title_{user_id}")
        ],
        [
            InlineKeyboardButton("🔄 Reset", callback_data=f"meta_reset_{user_id}"),
            InlineKeyboardButton("❌ Close", callback_data="close_menu")
        ]
    ]
    
    await message.reply_text(
        f"📊 **Metadata Settings**\n\n"
        f"**Status:** {status}\n"
        f"**Author:** `{author}`\n" 
        f"**Title:** `{title}`\n\n"
        f"Metadata adds author and title information to your files.\n\n"
        f"*\"{DAZAI_QUOTES['metadata_enabled']}\"*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Settings Overview Command
@Client.on_message(filters.command("settings") & (filters.private | filters.group))
async def settings_overview(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    # Get all user settings
    user_data = await db.get_user_data(user_id)
    
    caption = user_data.get("caption") or "Not set"
    prefix = user_data.get("prefix") or "Not set" 
    suffix = user_data.get("suffix") or "Not set"
    has_thumb = "✅ Set" if user_data.get("thumbnail") else "❌ Not set"
    metadata = user_data.get("metadata", {})
    meta_status = "✅ Enabled" if metadata.get("enabled") else "❌ Disabled"
    
    # Truncate long values for display
    def truncate(text, max_len=30):
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text
    
    settings_text = f"""
⚙️ **Your Current Settings**

📝 **Caption:** `{truncate(caption)}`
🔤 **Prefix:** `{truncate(prefix)}`
🔤 **Suffix:** `{truncate(suffix)}`
🖼️ **Thumbnail:** {has_thumb}
📊 **Metadata:** {meta_status}

*"Settings shape our reality, like words shape our thoughts."*

**Available Commands:**
• `/set_caption` - Set custom caption template
• `/set_prefix` - Add prefix to filenames  
• `/set_suffix` - Add suffix to filenames
• Send photo - Set as thumbnail
• `/metadata` - Configure file metadata
• `/reset_all` - Reset all settings
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Caption", callback_data=f"help_caption_{user_id}"),
            InlineKeyboardButton("🖼️ Thumbnail", callback_data=f"help_thumb_{user_id}")
        ],
        [
            InlineKeyboardButton("🔤 Prefix/Suffix", callback_data=f"help_prefix_{user_id}"),
            InlineKeyboardButton("📊 Metadata", callback_data=f"meta_info_{user_id}")
        ],
        [
            InlineKeyboardButton("🔄 Reset All", callback_data=f"reset_confirm_{user_id}"),
            InlineKeyboardButton("❌ Close", callback_data="close_menu")
        ]
    ]
    
    await message.reply_text(
        settings_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Reset All Settings
@Client.on_message(filters.command("reset_all") & (filters.private | filters.group))
async def reset_all_settings(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group mention
    if message.chat.type.name != "PRIVATE":
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    keyboard = [[
        InlineKeyboardButton("✅ Yes, Reset Everything", callback_data=f"reset_confirmed_{user_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data="close_menu")
    ]]
    
    await message.reply_text(
        "⚠️ **Reset All Settings**\n\n"
        "This will permanently delete:\n"
        "• Caption template\n"
        "• Thumbnail image\n" 
        "• Prefix and suffix\n"
        "• Metadata configuration\n\n"
        "**This action cannot be undone!**\n\n"
        f"*\"{DAZAI_QUOTES['settings_reset']}\"*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Handle ForceReply responses for caption setting
@Client.on_message(filters.reply & filters.text & filters.private)
async def handle_caption_reply(client: Client, message: Message):
    # Check if this is a reply to our caption prompt
    if (message.reply_to_message and 
        message.reply_to_message.from_user.is_self and
        "Set Custom Caption" in message.reply_to_message.text):
        
        user_id = message.from_user.id
        new_caption = message.text.strip()
        
        if new_caption.lower() == "/cancel":
            await message.reply_text(
                f"❌ **Caption Setting Cancelled**\n\n"
                f"*\"{DAZAI_QUOTES['operation_cancelled']}\"*",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await db.set_caption(user_id, new_caption)
        
        await message.reply_text(
            f"✅ **Caption Set Successfully**\n\n"
            f"Your new caption template:\n`{new_caption}`\n\n"
            f"*\"{DAZAI_QUOTES['caption_set']}\"*",
            parse_mode=ParseMode.MARKDOWN
        )

# Callback Query Handlers
@Client.on_callback_query()
async def handle_settings_callbacks(client: Client, query):
    data = query.data
    user_id = query.from_user.id
    
    # Security check - ensure user can only modify their own settings
    if "_" in data and data.split("_")[-1].isdigit():
        target_user_id = int(data.split("_")[-1])
        if target_user_id != user_id:
            await query.answer("❌ You can only modify your own settings!", show_alert=True)
            return
    
    if data.startswith("meta_toggle_"):
        metadata = await db.get_metadata(user_id)
        current_status = metadata.get("enabled", False)
        await db.set_metadata(user_id, enabled=not current_status)
        
        status_text = "disabled" if current_status else "enabled"
        await query.answer(f"✅ Metadata {status_text}!", show_alert=True)
        
        # Refresh the metadata menu
        await metadata_command(client, query.message)
    
    elif data.startswith("meta_author_"):
        await query.message.edit_text(
            "📝 **Set Metadata Author**\n\n"
            "Send me the author name for your files.\n"
            "This will be embedded in the file metadata.\n\n" 
            "*Send the author name or /cancel to abort*",
            parse_mode=ParseMode.MARKDOWN
        )
        # Note: You'd need to implement a state system to handle the response
    
    elif data.startswith("meta_title_"):
        await query.message.edit_text(
            "📝 **Set Metadata Title**\n\n"
            "Send me the default title template for your files.\n"
            "This will be embedded in the file metadata.\n\n"
            "*Send the title or /cancel to abort*", 
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("meta_reset_"):
        await db.set_metadata(user_id, enabled=False, title="", author="")
        await query.answer("✅ Metadata settings reset!", show_alert=True)
        await metadata_command(client, query.message)
    
    elif data.startswith("reset_confirmed_"):
        # Reset all user settings
        await db.reset_user_settings(user_id)
        await query.answer("✅ All settings have been reset!", show_alert=True)
        await query.message.edit_text(
            f"✅ **All Settings Reset Successfully**\n\n"
            f"Your account is now back to default settings.\n\n"
            f"*\"{DAZAI_QUOTES['settings_reset']}\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "close_menu":
        await query.message.delete()
        await query.answer()

# Help callbacks for different setting types
    elif data.startswith("help_caption_"):
        help_text = """
📝 **Caption Template Help**

Use these variables in your caption:
• `{filename}` - Original file name
• `{filesize}` - File size (e.g., 1.5 GB)
• `{duration}` - Video/audio duration
• `{filetype}` - File type (video/document/audio)

**Example template:**
```
📁 File: {filename}
💾 Size: {filesize}
⏱️ Duration: {duration}
🎬 Type: {filetype}

Renamed by Dazai Bot 🎭
```

Commands:
• `/set_caption` - Set new template
• `/view_caption` - View current template  
• `/del_caption` - Remove template
"""
        await query.message.edit_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("help_thumb_"):
        help_text = """
🖼️ **Thumbnail Help**

Set a custom thumbnail for your video files:

**How to set:**
• Send any photo to the bot
• The photo will be saved as your thumbnail
• It will be applied to all renamed videos

**Commands:**
• Send photo - Set as thumbnail
• `/view_thumb` - Preview current thumbnail
• `/del_thumb` - Remove thumbnail

**Note:** Thumbnails only apply to video files, not documents or audio.
"""
        await query.message.edit_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("help_prefix_"):
        help_text = """
🔤 **Prefix & Suffix Help**

Add text before (prefix) or after (suffix) filenames:

**Prefix Examples:**
• `/set_prefix [Dazai]` → `[Dazai] filename.mp4`  
• `/set_prefix BSD_` → `BSD_filename.mp4`

**Suffix Examples:**
• `/set_suffix - BSD` → `filename - BSD.mp4`
• `/set_suffix _Renamed` → `filename_Renamed.mp4`

**Commands:**
• `/set_prefix` - Set filename prefix
• `/set_suffix` - Set filename suffix
• `/view_prefix` - View current prefix
• `/view_suffix` - View current suffix
• `/del_prefix` - Remove prefix
• `/del_suffix` - Remove suffix
"""
        await query.message.edit_text(help_text, parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("meta_info_"):
        help_text = """
📊 **Metadata Help**

Embed author and title information into your files:

**What is metadata?**
File metadata is information stored within the file that describes its properties like author, title, etc.

**Features:**
• Add author name to files
• Set custom title for files  
• Enable/disable metadata embedding
• Works with video and audio files

**Commands:**
• `/metadata` - Open metadata settings
• Metadata is applied during the rename process

**Note:** Not all file types support metadata embedding.
"""
        await query.message.edit_text(help_text, parse_mode=ParseMode.MARKDOWN)
