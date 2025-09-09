# plugins/start_commands.py - Core Commands
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ParseMode, ChatType
from database import db
from Bot.config import Config, Messages
from datetime import datetime
import psutil
import time

# Start command - works in both private and groups
@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Add user to database
    is_new = await db.add_user(user_id, username)
    
    # Create inline keyboard
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
    
    # Send welcome message
    welcome_text = Messages.START.format(user=message.from_user.mention)
    
    if Config.BOT_PIC:
        await message.reply_photo(
            Config.BOT_PIC,
            caption=welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # Log new user if it's a new user
    if is_new and Config.LOG_CHANNEL:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"🌸 **New User Joined**\n\n"
            f"👤 User: {message.from_user.mention}\n"
            f"🆔 ID: `{user_id}`\n"
            f"📝 Username: @{username if username else 'None'}\n"
            f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

# Help command
@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    keyboard = [[
        InlineKeyboardButton("🔙 Back", callback_data="start"),
        InlineKeyboardButton("❌ Close", callback_data="close")
    ]]
    
    await message.reply_text(
        Messages.HELP,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Settings command
@Client.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    # Get user settings
    caption = user_data.get("caption", "Not set")
    prefix = user_data.get("prefix", "Not set")
    suffix = user_data.get("suffix", "Not set")
    has_thumb = "✅ Set" if user_data.get("thumbnail") else "❌ Not set"
    metadata = user_data.get("metadata", {})
    meta_status = "✅ Enabled" if metadata.get("enabled") else "❌ Disabled"
    
    settings_text = f"""
⚙️ **Your Settings**

📝 **Caption:** `{caption}`
🔤 **Prefix:** `{prefix}`
🔤 **Suffix:** `{suffix}`
🖼 **Thumbnail:** {has_thumb}
📊 **Metadata:** {meta_status}

*"Settings are like preferences in death - very personal."*

Use /reset to reset all settings."""
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Set Caption", callback_data="set_caption"),
            InlineKeyboardButton("🖼 Set Thumbnail", callback_data="set_thumb")
        ],
        [
            InlineKeyboardButton("🔤 Prefix", callback_data="set_prefix"),
            InlineKeyboardButton("🔤 Suffix", callback_data="set_suffix")
        ],
        [
            InlineKeyboardButton("📊 Metadata", callback_data="metadata"),
            InlineKeyboardButton("🔄 Reset All", callback_data="reset_all")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]
    ]
    
    await message.reply_text(
        settings_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Reset command
@Client.on_message(filters.command("reset"))
async def reset_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    keyboard = [[
        InlineKeyboardButton("✅ Yes, Reset", callback_data="confirm_reset"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    ]]
    
    await message.reply_text(
        "⚠️ **Are you sure?**\n\n"
        "This will reset all your settings including:\n"
        "• Caption template\n"
        "• Thumbnail\n"
        "• Prefix & Suffix\n"
        "• Metadata settings\n\n"
        "*\"Sometimes a fresh start is all we need.\"*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Admin commands (only for ADMIN_ID)
@Client.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def admin_stats(client: Client, message: Message):
    # Get system stats
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    # Get bot stats
    total_users = await db.total_users_count()
    uptime = time.time() - client.uptime.timestamp()
    hours, remainder = divmod(int(uptime), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    stats_text = f"""
📊 **Bot Statistics**

👥 **Total Users:** `{total_users}`
⏱ **Uptime:** `{hours}h {minutes}m {seconds}s`

**System Stats:**
💻 **CPU:** `{cpu_usage}%`
🧠 **RAM:** `{ram_usage}%`
💾 **Disk:** `{disk_usage}%`

*"Numbers are poetry in disguise."*"""
    
    await message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID))
async def broadcast_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast it.")
    
    broadcast_msg = message.reply_to_message
    users = await db.get_all_users()
    
    success = 0
    failed = 0
    
    status = await message.reply_text("📤 Broadcasting...")
    
    async for user in users:
        try:
            await broadcast_msg.copy(user["_id"])
            success += 1
        except:
            failed += 1
        
        if (success + failed) % 20 == 0:
            await status.edit(f"📤 Broadcasting...\n✅ Success: {success}\n❌ Failed: {failed}")
    
    await status.edit(
        f"✅ **Broadcast Complete**\n\n"
        f"Success: `{success}`\n"
        f"Failed: `{failed}`"
    )

# Callback query handler
@Client.on_callback_query()
async def callback_handler(client: Client, query):
    data = query.data
    
    if data == "start":
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
    
    elif data == "help":
        keyboard = [[
            InlineKeyboardButton("🔙 Back", callback_data="start"),
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]]
        
        await query.message.edit_text(
            Messages.HELP,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "about":
        bot_info = await client.get_me()
        about_text = Messages.ABOUT.format(
            bot_name=bot_info.first_name,
            pyrogram_version="2.0.106"
        )
        
        keyboard = [[
            InlineKeyboardButton("🔙 Back", callback_data="start"),
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]]
        
        await query.message.edit_text(
            about_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "close":
        await query.message.delete()
    
    elif data == "confirm_reset":
        user_id = query.from_user.id
        await db.reset_user_settings(user_id)
        await query.answer("✅ All settings have been reset!", show_alert=True)
        await query.message.edit_text(
            "✅ **Settings Reset Successfully**\n\n"
            "*\"A clean slate, like a blank page waiting for a story.\"*"
        )
    
    elif data == "cancel":
        await query.message.edit_text("❌ Operation cancelled.")
    
    elif data == "stats":
        user_id = query.from_user.id
        stats = await db.get_stats(user_id)
        
        stats_text = f"""
📊 **Your Statistics**

📁 **Files Renamed:** `{stats.get('files_renamed', 0)}`
⏰ **Last Active:** `{stats.get('last_used', 'Never').strftime('%Y-%m-%d %H:%M')}`

*"Statistics are just stories waiting to be told."*"""
        
        keyboard = [[
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]]
        
        await query.message.edit_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
