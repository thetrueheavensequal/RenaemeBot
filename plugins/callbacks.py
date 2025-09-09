# plugins/callbacks.py - Callback Query Handlers
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from utils.database import db
from utils.helpers import progress_for_pyrogram, remove_path, humanbytes
from Bot.config import Config, Messages
import time
import logging
import os

logger = logging.getLogger(__name__)

@Client.on_callback_query(filters.regex(r"^upload\|"))
async def handle_upload_callback(client: Client, query):
    """Handle file upload type selection"""
    try:
        data_parts = query.data.split("|")
        if len(data_parts) < 4:
            return await query.answer("Invalid upload data", show_alert=True)
        
        _, upload_type, file_path, filename = data_parts
        user_id = query.from_user.id
        
        # Verify file exists
        if not os.path.exists(file_path):
            await query.message.edit_text("❌ File not found. Please try again.")
            return
        
        # Update status
        status_msg = await query.message.edit_text(
            f"📤 **Uploading as {upload_type.title()}**\n\n"
            f"📁 **File:** `{filename}`\n"
            f"💾 **Size:** `{humanbytes(os.path.getsize(file_path))}`\n\n"
            "*\"Patience is a virtue, even for the impatient.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Get user settings
        user_data = await db.get_user_data(user_id)
        caption_template = user_data.get("caption")
        thumbnail = user_data.get("thumbnail")
        
        # Prepare caption
        file_size = os.path.getsize(file_path)
        caption = None
        if caption_template:
            caption = caption_template.format(
                filename=filename,
                filesize=humanbytes(file_size),
                duration="N/A",  # Could be enhanced to get actual duration
                filetype=upload_type
            )
        
        start_time = time.time()
        
        try:
            if upload_type == "document":
                await client.send_document(
                    chat_id=query.message.chat.id,
                    document=file_path,
                    file_name=filename,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=(Messages.UPLOAD_PROGRESS, status_msg, start_time)
                )
            
            elif upload_type == "video":
                await client.send_video(
                    chat_id=query.message.chat.id,
                    video=file_path,
                    caption=caption or filename,
                    thumb=thumbnail,
                    progress=progress_for_pyrogram,
                    progress_args=(Messages.UPLOAD_PROGRESS, status_msg, start_time)
                )
            
            elif upload_type == "audio":
                await client.send_audio(
                    chat_id=query.message.chat.id,
                    audio=file_path,
                    caption=caption or filename,
                    progress=progress_for_pyrogram,
                    progress_args=(Messages.UPLOAD_PROGRESS, status_msg, start_time)
                )
            
            # Update user stats
            await db.increment_renamed_count(user_id)
            
            # Success message
            await status_msg.edit_text(
                f"✅ **Upload Complete**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"📤 **Type:** {upload_type.title()}\n"
                f"⏱️ **Time:** {int(time.time() - start_time)}s\n\n"
                f"*\"Another masterpiece completed.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.exception(f"Upload failed for user {user_id}")
            await status_msg.edit_text(
                f"❌ **Upload Failed**\n\n"
                f"Error: `{str(e)}`\n\n"
                f"*\"Even the best plans sometimes go awry.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        logger.exception("Upload callback error")
        await query.answer("Upload failed. Please try again.", show_alert=True)
    
    finally:
        # Clean up files
        try:
            data_parts = query.data.split("|")
            if len(data_parts) >= 3:
                file_path = data_parts[2]
                await remove_path(file_path)
        except:
            pass

@Client.on_callback_query(filters.regex(r"^close"))
async def close_menu_callback(client: Client, query):
    """Handle close menu button"""
    await query.message.delete()
    await query.answer()

@Client.on_callback_query(filters.regex(r"^cancel"))
async def cancel_operation_callback(client: Client, query):
    """Handle cancel operation button"""
    await query.message.edit_text(
        "❌ **Operation Cancelled**\n\n"
        "*\"Sometimes retreat is the wisest strategy.\"*",
        parse_mode=ParseMode.MARKDOWN
    )
    await query.answer()

@Client.on_callback_query(filters.regex(r"^help"))
async def help_callback(client: Client, query):
    """Handle help button"""
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back", callback_data="start"),
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ]
    
    await query.message.edit_text(
        Messages.HELP,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_callback_query(filters.regex(r"^about"))
async def about_callback(client: Client, query):
    """Handle about button"""
    bot_info = await client.get_me()
    about_text = Messages.ABOUT.format(
        bot_name=bot_info.first_name,
        pyrogram_version="2.0.106"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back", callback_data="start"),
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ]
    
    await query.message.edit_text(
        about_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_callback_query(filters.regex(r"^start"))
async def start_callback(client: Client, query):
    """Handle start/main menu button"""
    keyboard = [
        [
            InlineKeyboardButton("📚 Help", callback_data="help"),
            InlineKeyboardButton("🎭 About", callback_data="about")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ]
    ]
    
    if Config.SUPPORT_CHAT:
        keyboard.append([
            InlineKeyboardButton("💬 Support", url=f"https://t.me/{Config.SUPPORT_CHAT}")
        ])
    
    await query.message.edit_text(
        Messages.START.format(user=query.from_user.mention),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_callback_query(filters.regex(r"^settings"))
async def settings_callback(client: Client, query):
    """Handle settings button"""
    user_id = query.from_user.id
    user_data = await db.get_user_data(user_id)
    
    caption = user_data.get("caption", "Not set")
    prefix = user_data.get("prefix", "Not set")
    suffix = user_data.get("suffix", "Not set")
    has_thumb = "✅ Set" if user_data.get("thumbnail") else "❌ Not set"
    metadata = user_data.get("metadata", {})
    meta_status = "✅ Enabled" if metadata.get("enabled") else "❌ Disabled"
    
    # Truncate long values
    def truncate(text, max_len=25):
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text
    
    settings_text = f"""⚙️ **Your Settings**

📝 **Caption:** `{truncate(caption)}`
🔤 **Prefix:** `{truncate(prefix)}`
🔤 **Suffix:** `{truncate(suffix)}`
🖼️ **Thumbnail:** {has_thumb}
📊 **Metadata:** {meta_status}

*"Settings are the foundation of our digital expression."*

Use commands to modify settings or /reset_all to reset everything."""
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Caption Help", callback_data="help_caption"),
            InlineKeyboardButton("🖼️ Thumb Help", callback_data="help_thumb")
        ],
        [
            InlineKeyboardButton("🔤 Prefix/Suffix", callback_data="help_prefix"),
            InlineKeyboardButton("📊 Metadata", callback_data="help_metadata")
        ],
        [
            InlineKeyboardButton("🔄 Reset All", callback_data="reset_confirm"),
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]
    ]
    
    await query.message.edit_text(
        settings_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_callback_query(filters.regex(r"^stats"))
async def stats_callback(client: Client, query):
    """Handle stats button"""
    user_id = query.from_user.id
    user_stats = await db.get_user_stats(user_id)
    
    files_renamed = user_stats.get('files_renamed', 0)
    join_date = user_stats.get('join_date', 'Unknown')
    last_used = user_stats.get('last_used', 'Never')
    
    if hasattr(join_date, 'strftime'):
        join_date = join_date.strftime('%Y-%m-%d')
    if hasattr(last_used, 'strftime'):
        last_used = last_used.strftime('%Y-%m-%d %H:%M')
    
    stats_text = f"""📊 **Your Statistics**

📁 **Files Renamed:** `{files_renamed}`
📅 **Member Since:** `{join_date}`
⏰ **Last Activity:** `{last_used}`

*"Numbers tell stories that words sometimes cannot."*"""
    
    keyboard = [[
        InlineKeyboardButton("🔙 Back", callback_data="start")
    ]]
    
    await query.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_callback_query(filters.regex(r"^reset_confirm"))
async def reset_confirm_callback(client: Client, query):
    """Handle reset confirmation"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Reset All", callback_data="reset_execute"),
            InlineKeyboardButton("❌ Cancel", callback_data="settings")
        ]
    ]
    
    await query.message.edit_text(
        "⚠️ **Reset All Settings**\n\n"
        "This will permanently delete:\n"
        "• Caption template\n"
        "• Thumbnail image\n"
        "• Prefix and suffix\n"
        "• Metadata configuration\n\n"
        "**This action cannot be undone!**\n\n"
        "*\"Sometimes we must destroy to rebuild.\"*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_callback_query(filters.regex(r"^reset_execute"))
async def reset_execute_callback(client: Client, query):
    """Execute settings reset"""
    user_id = query.from_user.id
    await db.reset_user_settings(user_id)
    
    await query.message.edit_text(
        "✅ **All Settings Reset**\n\n"
        "Your account has been restored to default settings.\n"
        "You can now configure everything fresh.\n\n"
        "*\"A clean slate awaits your new story.\"*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await query.answer("Settings reset successfully!", show_alert=True)

# Help callbacks
@Client.on_callback_query(filters.regex(r"^help_"))
async def help_callbacks(client: Client, query):
    """Handle help topic callbacks"""
    topic = query.data.replace("help_", "")
    
    help_texts = {
        "caption": """📝 **Caption Help**

Set custom caption templates for your files.

**Available variables:**
• `{filename}` - Original file name
• `{filesize}` - File size (e.g., 1.5 GB)
• `{duration}` - Video/audio duration
• `{filetype}` - File type

**Commands:**
• `/set_caption` - Set new template
• `/view_caption` - View current
• `/del_caption` - Remove template

**Example:**
```
📁 {filename}
💾 {filesize}
⏱️ {duration}

Dazai Bot 🎭
```""",

        "thumb": """🖼️ **Thumbnail Help**

Set custom thumbnails for video files.

**How to use:**
• Send any photo to set as thumbnail
• Applies to all renamed videos
• Only works with video files

**Commands:**
• Send photo - Set thumbnail
• `/view_thumb` - Preview current
• `/del_thumb` - Remove thumbnail

*"A good thumbnail is like a book cover - it tells the story before you open it."*""",

        "prefix": """🔤 **Prefix & Suffix Help**

Add text before or after filenames.

**Prefix Examples:**
• `/set_prefix [BSD]` → `[BSD] file.mp4`
• `/set_prefix Dazai_` → `Dazai_file.mp4`

**Suffix Examples:**
• `/set_suffix - Renamed` → `file - Renamed.mp4`
• `/set_suffix _BSD` → `file_BSD.mp4`

**Commands:**
• `/set_prefix` & `/set_suffix` - Set text
• `/view_prefix` & `/view_suffix` - View current
• `/del_prefix` & `/del_suffix` - Remove""",

        "metadata": """📊 **Metadata Help**

Embed information into your files.

**What it does:**
• Adds author & title to file metadata
• Works with video and audio files
• Information stored within the file

**Commands:**
• `/metadata` - Configure settings
• Enable/disable embedding
• Set author and title information

*"Metadata is like a signature - it identifies the creator's touch."*"""
    }
    
    help_text = help_texts.get(topic, "Help topic not found.")
    
    keyboard = [[
        InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")
    ]]
    
    await query.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
