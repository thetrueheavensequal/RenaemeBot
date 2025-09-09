# plugins/basic.py - Enhanced Core Commands with Dazai Theme
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ParseMode, ChatType
from utils.database import db
from utils.helpers import humanbytes, get_random_quote, temp_data
from Bot.config import Config
from Bot.messages import Messages
from datetime import datetime
import psutil
import time
import logging

logger = logging.getLogger(__name__)

# Start command - Enhanced for both private and group usage
@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Check if in group and handle appropriately
    is_group = message.chat.type != ChatType.PRIVATE
    
    if is_group:
        bot_me = await client.get_me()
        # In groups, only respond if mentioned or replied to
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    # Add user to database
    try:
        is_new_user = await db.add_user(user_id, username)
        
        # Update user activity
        await db.update_user_activity(user_id)
        
    except Exception as e:
        logger.error(f"Database error in start command: {e}")
        is_new_user = False
    
    # Create dynamic inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("📚 Help", callback_data="help"),
            InlineKeyboardButton("🎭 About", callback_data="about")
        ]
    ]
    
    # Add settings and stats for private chats
    if not is_group:
        keyboard.append([
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 My Stats", callback_data="stats")
        ])
    
    # Add support chat if configured
    if Config.SUPPORT_CHAT:
        keyboard.append([
            InlineKeyboardButton("💬 Support Chat", url=f"https://t.me/{Config.SUPPORT_CHAT}")
        ])
    
    # Add group usage info for groups
    if is_group:
        keyboard.append([
            InlineKeyboardButton("ℹ️ Group Usage", callback_data="group_info")
        ])
    
    # Format welcome message with user mention
    bot_info = await client.get_me()
    welcome_text = Messages.START.format(
        user=message.from_user.mention,
        bot_username=bot_info.username
    )
    
    # Send welcome message with optional photo
    try:
        if Config.BOT_PIC and not is_group:  # Only send photo in private chats
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
    except Exception as e:
        logger.error(f"Failed to send start message: {e}")
        # Fallback without photo
        await message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    # Log new user joining (admin notification)
    if is_new_user and Config.LOG_CHANNEL and not is_group:
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"🌸 **New User Joined Dazai's Atelier**\n\n"
                f"👤 **User:** {message.from_user.mention}\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"📝 **Username:** @{username if username else 'None'}\n"
                f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔗 **Profile:** [View Profile](tg://user?id={user_id})\n\n"
                f"*\"Another soul seeking the art of file perfection.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to send log message: {e}")

# Help command with enhanced information
@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    # Check group usage
    is_group = message.chat.type != ChatType.PRIVATE
    
    if is_group:
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    keyboard = [
        [
            InlineKeyboardButton("📋 Commands", callback_data="help_commands"),
            InlineKeyboardButton("🎯 Examples", callback_data="help_examples")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="start"),
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ]
    
    # Get bot info for dynamic help
    bot_info = await client.get_me()
    help_text = Messages.HELP.format(bot_username=bot_info.username)
    
    await message.reply_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Enhanced settings command
@Client.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group usage
    is_group = message.chat.type != ChatType.PRIVATE
    
    if is_group:
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    try:
        # Get comprehensive user data
        user_data = await db.get_user_data(user_id)
        
        if not user_data:
            # Initialize user if not exists
            await db.add_user(user_id, message.from_user.username)
            user_data = {}
        
        # Extract settings with defaults
        caption = user_data.get("caption") or "Not set"
        prefix = user_data.get("prefix") or "Not set"
        suffix = user_data.get("suffix") or "Not set"
        has_thumb = "✅ Set" if user_data.get("thumbnail") else "❌ Not set"
        metadata = user_data.get("metadata", {})
        meta_status = "✅ Enabled" if metadata.get("enabled") else "❌ Disabled"
        
        # Truncate long settings for display
        def truncate_setting(text, max_len=25):
            if len(str(text)) > max_len:
                return str(text)[:max_len] + "..."
            return str(text)
        
        settings_text = f"""⚙️ **Your Current Settings**

📝 **Caption Template:** `{truncate_setting(caption)}`
🔤 **Filename Prefix:** `{truncate_setting(prefix)}`
🔤 **Filename Suffix:** `{truncate_setting(suffix)}`
🖼️ **Video Thumbnail:** {has_thumb}
📊 **File Metadata:** {meta_status}

*"{get_random_quote('start')}"*

**Quick Actions:**
Use the buttons below or these commands:
• `/set_caption` - Configure caption template
• `/set_prefix` & `/set_suffix` - Set filename additions
• Send photo - Set video thumbnail
• `/metadata` - Configure file metadata
• `/reset_all` - Reset everything"""
        
        # Create settings keyboard
        keyboard = [
            [
                InlineKeyboardButton("📝 Caption", callback_data="help_caption"),
                InlineKeyboardButton("🖼️ Thumbnail", callback_data="help_thumb")
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
        
        await message.reply_text(
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Settings command error: {e}")
        await message.reply_text(
            "❌ **Error Loading Settings**\n\n"
            "There was an issue accessing your settings. Please try again.\n\n"
            f"*\"Even the best systems encounter occasional hiccups.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

# Enhanced stats command for users
@Client.on_message(filters.command(["stats", "mystats"]))
async def user_stats_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group usage
    is_group = message.chat.type != ChatType.PRIVATE
    
    if is_group:
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    try:
        user_stats = await db.get_user_stats(user_id)
        
        files_renamed = user_stats.get('files_renamed', 0)
        join_date = user_stats.get('join_date', 'Unknown')
        last_used = user_stats.get('last_used', 'Never')
        
        # Format dates
        if hasattr(join_date, 'strftime'):
            join_date_str = join_date.strftime('%Y-%m-%d')
        else:
            join_date_str = str(join_date)
            
        if hasattr(last_used, 'strftime'):
            last_used_str = last_used.strftime('%Y-%m-%d %H:%M')
        else:
            last_used_str = str(last_used)
        
        # Check for milestones
        milestone_msg = Messages.get_milestone_message(files_renamed)
        
        stats_text = f"""📊 **Your Statistics**

📁 **Files Renamed:** `{files_renamed}`
📅 **Member Since:** `{join_date_str}`
⏰ **Last Activity:** `{last_used_str}`

{milestone_msg}

*"Statistics tell the story of our digital journey."*"""
        
        keyboard = [[
            InlineKeyboardButton("🔙 Back", callback_data="start"),
            InlineKeyboardButton("🔄 Refresh", callback_data="stats")
        ]]
        
        await message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"User stats error: {e}")
        await message.reply_text(
            "❌ **Error Loading Statistics**\n\n"
            "Unable to retrieve your statistics at the moment.\n\n"
            f"*\"Numbers sometimes hide behind the fog of technical difficulties.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

# Reset command with confirmation
@Client.on_message(filters.command(["reset", "reset_all"]))
async def reset_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check group usage
    is_group = message.chat.type != ChatType.PRIVATE
    
    if is_group:
        bot_me = await client.get_me()
        if not (f"@{bot_me.username}" in (message.text or "") or 
                (message.reply_to_message and message.reply_to_message.from_user.is_self)):
            return
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Reset Everything", callback_data=f"reset_confirmed_{user_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="settings")
        ]
    ]
    
    await message.reply_text(
        Messages.CONFIRM_RESET_ALL,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# Admin-only commands
@Client.on_message(filters.command("adminstats") & filters.user(Config.ADMIN_ID))
async def admin_stats_command(client: Client, message: Message):
    try:
        # Get system stats
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # Get bot stats
        total_users = await db.total_users_count()
        active_users_24h = await db.get_active_users_count(hours=24)
        files_today = await db.get_files_processed_today()
        
        # Calculate uptime
        if hasattr(client, 'start_time'):
            uptime_seconds = time.time() - client.start_time
        else:
            uptime_seconds = 0
        
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        # Format memory usage
        ram_total = humanbytes(ram.total)
        ram_used = humanbytes(ram.used)
        disk_total = humanbytes(disk.total)
        disk_used = humanbytes(disk.used)
        
        stats_text = Messages.ADMIN_STATS.format(
            total_users=total_users,
            active_users=active_users_24h,
            files_today=files_today,
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            disk_usage=disk_usage,
            uptime=uptime_str,
            ram_info=f"{ram_used}/{ram_total}",
            disk_info=f"{disk_used}/{disk_total}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh_stats"),
                InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_detailed_stats")
            ],
            [
                InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
                InlineKeyboardButton("⚙️ System Control", callback_data="admin_system")
            ]
        ]
        
        await message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        await message.reply_text(f"❌ Error getting stats: `{e}`")

@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID))
async def broadcast_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(
            "**Broadcast Usage:**\n"
            "Reply to a message to broadcast it to all users.\n\n"
            "*\"Words must first be chosen before they can be spread.\"*"
        )
    
    broadcast_msg = message.reply_to_message
    
    try:
        users = await db.get_all_users()
        total_users = await db.total_users_count()
        
        success = 0
        failed = 0
        
        status = await message.reply_text(Messages.ADMIN_BROADCAST_START)
        
        async for user in users:
            try:
                await broadcast_msg.copy(user["_id"])
                success += 1
            except Exception as e:
                logger.debug(f"Broadcast failed for user {user['_id']}: {e}")
                failed += 1
            
            # Update progress every 20 users
            if (success + failed) % 20 == 0:
                try:
                    progress = ((success + failed) / total_users) * 100
                    await status.edit_text(
                        f"📡 **Broadcasting...**\n\n"
                        f"Progress: {progress:.1f}%\n"
                        f"✅ Successful: `{success}`\n"
                        f"❌ Failed: `{failed}`\n"
                        f"⏳ Remaining: `{total_users - success - failed}`"
                    )
                except:
                    pass
        
        # Final broadcast results
        broadcast_complete = Messages.ADMIN_BROADCAST_COMPLETE.format(
            success=success,
            failed=failed,
            total=total_users
        )
        
        await status.edit_text(broadcast_complete)
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await message.reply_text(f"❌ Broadcast failed: `{e}`")

# Environment management commands (Admin only)
@Client.on_message(filters.command("listenv") & filters.user(Config.ADMIN_ID))
async def list_env_command(client: Client, message: Message):
    from Bot.config import list_env_keys
    
    keys = list_env_keys()
    
    env_text = "🔑 **Available Environment Variables:**\n\n"
    for i, key in enumerate(keys, 1):
        env_text += f"`{i:2d}.` `{key}`\n"
    
    env_text += f"\n**Total:** `{len(keys)}` variables\n"
    env_text += "\n*Use `/getenv KEY` to view values*\n"
    env_text += "*Use `/setenv KEY VALUE` to modify*"
    
    await message.reply_text(env_text, parse_mode=ParseMode.MARKDOWN)

@Client.on_message(filters.command("getenv") & filters.user(Config.ADMIN_ID))
async def get_env_command(client: Client, message: Message):
    from Bot.config import get_env_var
    
    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/getenv KEY`\n\n"
            "**Example:** `/getenv MAX_FILE_SIZE`\n\n"
            "Use `/listenv` to see available keys."
        )
    
    key = message.command[1].strip().upper()
    value = get_env_var(key)
    
    if value is None:
        await message.reply_text(f"❌ Variable `{key}` not found or not allowed.")
    else:
        # Hide sensitive values
        if any(sensitive in key.lower() for sensitive in ['token', 'hash', 'password', 'key']):
            display_value = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display_value = value
            
        await message.reply_text(
            f"🔍 **Environment Variable**\n\n"
            f"**Key:** `{key}`\n"
            f"**Value:** `{display_value}`\n\n"
            f"*Current configuration retrieved.*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command("setenv") & filters.user(Config.ADMIN_ID))
async def set_env_command(client: Client, message: Message):
    from Bot.config import set_env_var
    
    if len(message.command) < 3:
        return await message.reply_text(
            "**Usage:** `/setenv KEY VALUE`\n\n"
            "**Example:** `/setenv MAX_FILE_SIZE 4294967296`\n\n"
            "Use `/listenv` to see available keys."
        )
    
    key = message.command[1].strip().upper()
    value = " ".join(message.command[2:]).strip()
    
    success = set_env_var(key, value)
    
    if success:
        await message.reply_text(
            f"✅ **Environment Updated**\n\n"
            f"**Variable:** `{key}`\n"
            f"**New Value:** `{value}`\n\n"
            f"*Configuration updated successfully.*",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.reply_text(
            f"❌ **Update Failed**\n\n"
            f"Variable `{key}` is not allowed or update failed.\n"
            f"Use `/listenv` to see available variables."
        )

@Client.on_message(filters.command("reload") & filters.user(Config.ADMIN_ID))
async def reload_command(client: Client, message: Message):
    await message.reply_text(
        "🔄 **Configuration Reload**\n\n"
        "Some settings are applied immediately, but for full effect:\n"
        "• Restart the bot service\n"
        "• Re-initialize database connections\n"
        "• Clear temporary data\n\n"
        "*\"Sometimes a complete refresh is necessary for true change.\"*",
        parse_mode=ParseMode.MARKDOWN
    )
