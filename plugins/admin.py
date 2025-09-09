# plugins/admin.py - Enhanced Admin Commands with Dazai Theme
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ParseMode
from Bot.config import Config, set_env_var, get_env_var, list_env_keys
from Bot.messages import Messages
from utils.database import db
from utils.helpers import humanbytes, get_random_quote
import time
import psutil
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("listenv") & filters.user(Config.ADMIN_ID))
async def listenv_command(client: Client, message: Message):
    """List all configurable environment variables"""
    try:
        keys = list_env_keys()
        
        if not keys:
            return await message.reply_text(
                "❌ **No Environment Variables Available**\n\n"
                "*\"Even the void has its own configuration.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Group keys by category for better organization
        categories = {
            'Bot Configuration': [],
            'Database & Storage': [],
            'Features & Limits': [],
            'Security & Admin': [],
            'Optional Settings': []
        }
        
        for key in sorted(keys):
            if any(word in key.lower() for word in ['token', 'hash', 'id']):
                categories['Security & Admin'].append(key)
            elif any(word in key.lower() for word in ['database', 'url', 'mongo']):
                categories['Database & Storage'].append(key)
            elif any(word in key.lower() for word in ['size', 'limit', 'max']):
                categories['Features & Limits'].append(key)
            elif any(word in key.lower() for word in ['pic', 'sticker', 'support', 'log']):
                categories['Optional Settings'].append(key)
            else:
                categories['Bot Configuration'].append(key)
        
        env_text = "🔑 **Environment Variables Configuration**\n\n"
        
        for category, cat_keys in categories.items():
            if cat_keys:
                env_text += f"**{category}:**\n"
                for key in cat_keys:
                    env_text += f"  • `{key}`\n"
                env_text += "\n"
        
        env_text += f"**Total Variables:** `{len(keys)}`\n\n"
        env_text += "**Commands:**\n"
        env_text += "• `/getenv KEY` - View variable value\n"
        env_text += "• `/setenv KEY VALUE` - Update variable\n\n"
        env_text += "*\"Configuration is the art of controlled chaos.\"*"
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Quick View", callback_data="admin_env_quick"),
                InlineKeyboardButton("⚙️ System Info", callback_data="admin_system_info")
            ],
            [
                InlineKeyboardButton("📊 Bot Stats", callback_data="admin_bot_stats"),
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
        
        await message.reply_text(
            env_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in listenv command: {e}")
        await message.reply_text(
            f"❌ **Error Loading Environment Variables**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"*\"Even administrators face technical mysteries.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command("getenv") & filters.user(Config.ADMIN_ID))
async def getenv_command(client: Client, message: Message):
    """Get specific environment variable value"""
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        return await message.reply_text(
            "**Usage:** `/getenv KEY`\n\n"
            "**Examples:**\n"
            "• `/getenv MAX_FILE_SIZE`\n"
            "• `/getenv BOT_PIC`\n"
            "• `/getenv DATABASE_URL`\n\n"
            "Use `/listenv` to see all available keys.\n\n"
            "*\"Precision in commands leads to clarity in results.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    key = parts[1].strip().upper()
    
    try:
        value = get_env_var(key)
        
        if value is None:
            await message.reply_text(
                f"❌ **Variable Not Found**\n\n"
                f"**Key:** `{key}`\n"
                f"**Status:** Not found or not allowed\n\n"
                f"Use `/listenv` to see available variables.\n\n"
                f"*\"Not all secrets are meant to be revealed.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Mask sensitive values for security
        sensitive_keys = ['token', 'hash', 'password', 'secret', 'key', 'session']
        is_sensitive = any(sensitive in key.lower() for sensitive in sensitive_keys)
        
        if is_sensitive and len(str(value)) > 10:
            display_value = f"{str(value)[:6]}...{str(value)[-4:]}"
            security_note = "🔒 *Value partially hidden for security*"
        else:
            display_value = str(value)
            security_note = ""
        
        # Format value based on type
        if key in ['MAX_FILE_SIZE']:
            try:
                size_bytes = int(value)
                human_readable = f"{humanbytes(size_bytes)} ({size_bytes:,} bytes)"
                display_value = human_readable
            except:
                pass
        
        result_text = f"🔍 **Environment Variable**\n\n"
        result_text += f"**Key:** `{key}`\n"
        result_text += f"**Value:** `{display_value}`\n"
        if security_note:
            result_text += f"\n{security_note}\n"
        result_text += f"\n*\"Current configuration retrieved successfully.\"*"
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit Value", callback_data=f"admin_edit_env_{key}"),
                InlineKeyboardButton("📋 All Variables", callback_data="admin_list_env")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
        
        await message.reply_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error getting environment variable {key}: {e}")
        await message.reply_text(
            f"❌ **Error Retrieving Variable**\n\n"
            f"**Key:** `{key}`\n"
            f"**Error:** `{str(e)}`\n\n"
            f"*\"Sometimes the system guards its secrets too well.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command("setenv") & filters.user(Config.ADMIN_ID))
async def setenv_command(client: Client, message: Message):
    """Set environment variable value"""
    parts = message.text.split(maxsplit=2)
    
    if len(parts) < 3:
        return await message.reply_text(
            "**Usage:** `/setenv KEY VALUE`\n\n"
            "**Examples:**\n"
            "• `/setenv MAX_FILE_SIZE 4294967296`\n"
            "• `/setenv BOT_PIC https://example.com/image.jpg`\n"
            "• `/setenv SUPPORT_CHAT your_channel`\n\n"
            "**Note:** Changes may require bot restart for full effect.\n\n"
            "*\"Change is the only constant in digital evolution.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    key = parts[1].strip().upper()
    value = parts[2].strip()
    
    # Validate certain key types
    validation_error = None
    
    if key == 'MAX_FILE_SIZE':
        try:
            size_value = int(value)
            if size_value <= 0:
                validation_error = "File size must be positive"
            elif size_value > 4294967296:  # 4GB
                validation_error = "File size exceeds maximum limit (4GB)"
        except ValueError:
            validation_error = "File size must be a valid number"
    
    elif key in ['ADMIN_ID', 'LOG_CHANNEL']:
        try:
            int(value.replace('-', ''))
        except ValueError:
            validation_error = "Must be a valid Telegram ID"
    
    if validation_error:
        return await message.reply_text(
            f"❌ **Validation Error**\n\n"
            f"**Key:** `{key}`\n"
            f"**Error:** {validation_error}\n\n"
            f"*\"Precision prevents problems.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    try:
        success = set_env_var(key, value)
        
        if success:
            # Show confirmation with appropriate formatting
            display_value = value
            if key == 'MAX_FILE_SIZE':
                try:
                    display_value = f"{humanbytes(int(value))} ({value} bytes)"
                except:
                    pass
            
            # Mask sensitive values in confirmation
            sensitive_keys = ['token', 'hash', 'password', 'secret', 'session']
            if any(sensitive in key.lower() for sensitive in sensitive_keys) and len(value) > 10:
                display_value = f"{value[:6]}...{value[-4:]}"
            
            success_text = f"✅ **Environment Variable Updated**\n\n"
            success_text += f"**Key:** `{key}`\n"
            success_text += f"**New Value:** `{display_value}`\n"
            success_text += f"**Timestamp:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
            success_text += f"**Note:** Some changes require bot restart for full effect.\n\n"
            success_text += f"*\"Configuration updated with administrative precision.\"*"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Reload Config", callback_data="admin_reload"),
                    InlineKeyboardButton("📋 View All", callback_data="admin_list_env")
                ],
                [
                    InlineKeyboardButton("❌ Close", callback_data="close")
                ]
            ]
            
            await message.reply_text(
                success_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Log the change
            logger.info(f"Admin {message.from_user.id} updated {key} = {value}")
            
        else:
            await message.reply_text(
                f"❌ **Update Failed**\n\n"
                f"**Key:** `{key}`\n"
                f"**Reason:** Variable not allowed or system error\n\n"
                f"Use `/listenv` to see allowed variables.\n\n"
                f"*\"Not all changes are permitted in this realm.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"Error setting environment variable {key}: {e}")
        await message.reply_text(
            f"❌ **System Error**\n\n"
            f"**Key:** `{key}`\n"
            f"**Error:** `{str(e)}`\n\n"
            f"*\"The system resists this particular change.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command(["adminstats", "systemstats"]) & filters.user(Config.ADMIN_ID))
async def admin_stats_command(client: Client, message: Message):
    """Comprehensive system and bot statistics"""
    try:
        # System statistics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Bot statistics
        total_users = await db.total_users_count()
        try:
            active_users_24h = await db.get_active_users_count(hours=24)
            files_today = await db.get_files_processed_today()
        except:
            active_users_24h = "N/A"
            files_today = "N/A"
        
        # Uptime calculation
        if hasattr(client, 'start_time'):
            uptime_seconds = int(time.time() - client.start_time)
        else:
            uptime_seconds = 0
        
        uptime_str = str(timedelta(seconds=uptime_seconds))
        
        # Network and process info
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            system_uptime = datetime.now() - boot_time
        except:
            system_uptime = "Unknown"
        
        stats_text = f"""📊 **System & Bot Statistics**

**🤖 Bot Statistics:**
👥 **Total Users:** `{total_users:,}`
🌟 **Active Users (24h):** `{active_users_24h}`
📁 **Files Processed Today:** `{files_today}`
⏱️ **Bot Uptime:** `{uptime_str}`

**💻 System Performance:**
🔥 **CPU Usage:** `{cpu_percent:.1f}%`
🧠 **Memory:** `{memory.percent:.1f}% used`
   └ `{humanbytes(memory.used)} / {humanbytes(memory.total)}`
💽 **Disk Usage:** `{disk.percent:.1f}% used`
   └ `{humanbytes(disk.used)} / {humanbytes(disk.total)}`
🖥️ **System Uptime:** `{str(system_uptime).split('.')[0]}`

*"{get_random_quote('success')}"*"""

        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh_stats"),
                InlineKeyboardButton("📈 Detailed Stats", callback_data="admin_detailed_stats")
            ],
            [
                InlineKeyboardButton("👥 User Analysis", callback_data="admin_user_stats"),
                InlineKeyboardButton("🔧 System Control", callback_data="admin_system_control")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]

        await message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error in admin stats: {e}")
        await message.reply_text(
            f"❌ **Error Loading Statistics**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"*\"Sometimes even the most sophisticated systems stumble.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID))
async def broadcast_command(client: Client, message: Message):
    """Enhanced broadcast system with progress tracking"""
    if not message.reply_to_message:
        return await message.reply_text(
            "📢 **Broadcast System**\n\n"
            "**Usage:** Reply to a message to broadcast it to all users.\n\n"
            "**Features:**\n"
            "• Real-time progress tracking\n"
            "• Error handling and reporting\n"
            "• Success/failure statistics\n\n"
            "*\"Words must be chosen before they can reach the masses.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

    broadcast_msg = message.reply_to_message
    
    try:
        # Get all users
        users_cursor = db.get_all_users()
        total_users = await db.total_users_count()
        
        if total_users == 0:
            return await message.reply_text(
                "❌ **No Users Found**\n\n"
                "There are no users to broadcast to.\n\n"
                "*\"An empty audience awaits no performance.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
        
        success = 0
        failed = 0
        start_time = time.time()
        
        # Initial status message
        status_text = Messages.ADMIN_BROADCAST_START + f"\n\n**Target Users:** `{total_users:,}`"
        status = await message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
        
        # Broadcast to all users
        async for user in users_cursor:
            try:
                await broadcast_msg.copy(user["_id"])
                success += 1
            except Exception as e:
                failed += 1
                logger.debug(f"Broadcast failed for user {user['_id']}: {e}")
            
            # Update progress every 25 users or on completion
            if (success + failed) % 25 == 0 or (success + failed) == total_users:
                progress = ((success + failed) / total_users) * 100
                elapsed = int(time.time() - start_time)
                remaining = total_users - success - failed
                
                progress_text = f"📡 **Broadcasting in Progress...**\n\n"
                progress_text += f"📊 **Progress:** `{progress:.1f}%`\n"
                progress_text += f"✅ **Successful:** `{success:,}`\n"
                progress_text += f"❌ **Failed:** `{failed:,}`\n"
                progress_text += f"⏳ **Remaining:** `{remaining:,}`\n"
                progress_text += f"⏱️ **Elapsed:** `{elapsed}s`\n\n"
                progress_text += f"*\"Progress flows like ink across paper...\"*"
                
                try:
                    await status.edit_text(progress_text, parse_mode=ParseMode.MARKDOWN)
                except:
                    pass  # Ignore edit conflicts
        
        # Final results
        total_time = int(time.time() - start_time)
        completion_rate = (success / total_users * 100) if total_users > 0 else 0
        
        final_text = Messages.ADMIN_BROADCAST_COMPLETE.format(
            success=success,
            failed=failed,
            total=total_users
        )
        
        final_text += f"\n\n**📈 Broadcast Analytics:**\n"
        final_text += f"⏱️ **Total Time:** `{total_time}s`\n"
        final_text += f"⚡ **Rate:** `{success/total_time:.1f} msg/s`\n"
        final_text += f"✅ **Success Rate:** `{completion_rate:.1f}%`\n\n"
        final_text += f"*\"Message delivered with administrative efficiency.\"*"
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Detailed Report", callback_data="admin_broadcast_report"),
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
        
        await status.edit_text(
            final_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log broadcast completion
        logger.info(f"Broadcast completed: {success} success, {failed} failed, {total_time}s")
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await message.reply_text(
            f"❌ **Broadcast Failed**\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"*\"Even the best communication systems face interference.\"*",
            parse_mode=ParseMode.MARKDOWN
        )

@Client.on_message(filters.command("reload") & filters.user(Config.ADMIN_ID))
async def reload_command(client: Client, message: Message):
    """Enhanced reload command with system information"""
    try:
        # Check what can be reloaded vs what needs restart
        reload_info = {
            'immediate': [
                'Environment variables (most)',
                'Message templates', 
                'User settings cache',
                'Temporary data cleanup'
            ],
            'restart_required': [
                'Bot token changes',
                'Database connection changes',
                'FFmpeg binary paths',
                'Plugin loading changes'
            ]
        }
        
        reload_text = f"🔄 **System Reload Information**\n\n"
        
        reload_text += f"**✅ Applied Immediately:**\n"
        for item in reload_info['immediate']:
            reload_text += f"• {item}\n"
        
        reload_text += f"\n**🔄 Requires Bot Restart:**\n"
        for item in reload_info['restart_required']:
            reload_text += f"• {item}\n"
        
        reload_text += f"\n**🎛️ Current System Status:**\n"
        reload_text += f"⏱️ **Uptime:** `{str(timedelta(seconds=int(time.time() - getattr(client, 'start_time', time.time()))))}`\n"
        reload_text += f"💾 **Memory:** `{psutil.virtual_memory().percent:.1f}% used`\n"
        reload_text += f"🔧 **Config:** Live updates enabled\n\n"
        reload_text += f"*\"Some changes flow like water, others require reconstruction.\"*"
        
        keyboard = [
            [
                InlineKeyboardButton("⚡ Soft Reload", callback_data="admin_soft_reload"),
                InlineKeyboardButton("🔄 Full Restart Info", callback_data="admin_restart_info")
            ],
            [
                InlineKeyboardButton("📊 System Status", callback_data="admin_system_status"),
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
        
        await message.reply_text(
            reload_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Reload command error: {e}")
        await message.reply_text(
            f"❌ **Reload Information Error**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"*\"Even reload mechanisms need occasional maintenance.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
