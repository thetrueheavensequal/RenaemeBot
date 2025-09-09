# plugins/rename.py - File Renaming Core
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pyrogram.enums import MessageMediaType, ParseMode, ChatType
from pyrogram.errors import FloodWait
import asyncio
import os
import time
from datetime import datetime
from database import db
from config import Config, Messages
from utils import (
    humanbytes, 
    progress_callback, 
    add_prefix_suffix,
    extract_file_info
)
import logging

logger = logging.getLogger(__name__)

# Handle files sent to bot (works in both private and groups)
@Client.on_message(filters.document | filters.video | filters.audio)
async def rename_file(client: Client, message: Message):
    # Check if in group and bot was mentioned or replied to
    if message.chat.type != ChatType.PRIVATE:
        # In groups, only process if bot is mentioned or message is a reply to bot
        if not (message.reply_to_message and 
                message.reply_to_message.from_user and 
                message.reply_to_message.from_user.is_self):
            # Check if bot is mentioned
            bot_username = (await client.get_me()).username
            if f"@{bot_username}" not in (message.text or "") and \
               f"@{bot_username}" not in (message.caption or ""):
                return
    
    user_id = message.from_user.id
    await db.add_user(user_id, message.from_user.username)
    
    # Get file info
    file = message.document or message.video or message.audio
    file_info = extract_file_info(file)
    
    # Check file size
    max_size = 4 * 1024 * 1024 * 1024 if client.premium_client else Config.MAX_FILE_SIZE
    if file.file_size > max_size:
        return await message.reply_text(
            f"❌ **File Too Large**\n\n"
            f"Maximum size: `{humanbytes(max_size)}`\n"
            f"Your file: `{humanbytes(file.file_size)}`\n\n"
            f"*\"Even I have my limits, unlike my desire for death.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Create rename prompt
    prompt_text = Messages.RENAME_PROMPT.format(
        filename=file_info['filename'],
        filesize=file_info['filesize'],
        filetype=file_info['type']
    )
    
    # Store file reference for later use
    await message.reply_text(
        prompt_text,
        reply_to_message_id=message.id,
        reply_markup=ForceReply(selective=True),
        parse_mode=ParseMode.MARKDOWN
    )

# Handle rename response
@Client.on_message(filters.private & filters.reply)
async def handle_rename_response(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.reply_markup:
        return
    
    if not isinstance(message.reply_to_message.reply_markup, ForceReply):
        return
    
    user_id = message.from_user.id
    new_filename = message.text.strip()
    
    # Get the original file message
    original_msg = message.reply_to_message.reply_to_message
    if not original_msg:
        return await message.reply_text("❌ Original file not found!")
    
    file = original_msg.document or original_msg.video or original_msg.audio
    if not file:
        return await message.reply_text("❌ No file found in the original message!")
    
    # Add extension if missing
    if "." not in new_filename:
        if "." in file.file_name:
            ext = file.file_name.rsplit(".", 1)[-1]
            new_filename = f"{new_filename}.{ext}"
        else:
            new_filename = f"{new_filename}.mkv"  # Default for videos
    
    # Get user settings
    user_data = await db.get_user(user_id)
    prefix = user_data.get("prefix", "")
    suffix = user_data.get("suffix", "")
    
    # Apply prefix and suffix
    final_filename = add_prefix_suffix(new_filename, prefix, suffix)
    
    # Show upload type selection for videos
    if isinstance(file, (original_msg.video, original_msg.document)):
        keyboard = [
            [
                InlineKeyboardButton("📹 As Video", callback_data=f"upload_video|{message.id}"),
                InlineKeyboardButton("📄 As Document", callback_data=f"upload_doc|{message.id}")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_rename")
            ]
        ]
        
        await message.reply_text(
            f"**How would you like to upload?**\n\n"
            f"📁 New name: `{final_filename}`\n\n"
            f"*\"Choose your path, like choosing between life and death.\"*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Store the new filename for later use
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"temp_rename": {
                "filename": final_filename,
                "original_msg_id": original_msg.id,
                "chat_id": message.chat.id
            }}}
        )
    else:
        # For audio, proceed directly
        await process_rename(client, message, original_msg, final_filename, "audio")

async def process_rename(client, message, original_msg, new_filename, upload_type):
    """Process the actual file renaming"""
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    file = original_msg.document or original_msg.video or original_msg.audio
    
    # Progress message
    progress_msg = await message.reply_text(
        "🎭 *\"Let me work my magic...\"*\n\n"
        "Starting download...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Download file
    try:
        start_time = time.time()
        file_path = await client.download_media(
            original_msg,
            file_name=f"downloads/{user_id}_{time.time()}",
            progress=progress_callback,
            progress_args=(
                "📥 Downloading",
                progress_msg,
                start_time
            )
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        return await progress_msg.edit(
            f"❌ **Download Failed**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"*\"Even failures have their beauty.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Get caption and thumbnail
    caption_template = user_data.get("caption")
    thumbnail = user_data.get("thumbnail")
    
    # Prepare caption
    if caption_template:
        try:
            caption = caption_template.format(
                filename=new_filename,
                filesize=humanbytes(file.file_size),
                duration=str(file.duration) if hasattr(file, 'duration') else "N/A"
            )
        except:
            caption = new_filename
    else:
        caption = f"**{new_filename}**\n\n*Renamed by Dazai Bot*"
    
    # Download thumbnail if exists
    thumb_path = None
    if thumbnail:
        try:
            thumb_path = await client.download_media(thumbnail, f"thumbs/{user_id}.jpg")
        except:
            pass
    
    # Upload file
    await progress_msg.edit(
        "📤 *\"Almost there, like approaching the perfect death...\"*\n\n"
        "Uploading file...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        start_time = time.time()
        
        # Choose upload method based on file size and available clients
        use_premium = file.file_size > Config.MAX_FILE_SIZE and client.premium_client
        upload_client = client.premium_client if use_premium else client
        
        if upload_type == "video":
            await upload_client.send_video(
                chat_id=message.chat.id,
                video=file_path,
                caption=caption,
                thumb=thumb_path,
                duration=file.duration if hasattr(file, 'duration') else 0,
                progress=progress_callback,
                progress_args=(
                    "📤 Uploading",
                    progress_msg,
                    start_time
                ),
                file_name=new_filename
            )
        elif upload_type == "audio":
            await upload_client.send_audio(
                chat_id=message.chat.id,
                audio=file_path,
                caption=caption,
                thumb=thumb_path,
                duration=file.duration if hasattr(file, 'duration') else 0,
                progress=progress_callback,
                progress_args=(
                    "📤 Uploading",
                    progress_msg,
                    start_time
                ),
                file_name=new_filename
            )
        else:  # document
            await upload_client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=caption,
                thumb=thumb_path,
                progress=progress_callback,
                progress_args=(
                    "📤 Uploading",
                    progress_msg,
                    start_time
                ),
                file_name=new_filename
            )
        
        # Update stats
        await db.increment_renamed_count(user_id)
        
        # Success message
        await progress_msg.edit(
            "✅ **File Renamed Successfully!**\n\n"
            f"*\"Perfect, like a successful suicide attempt... wait, that's not right.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await progress_msg.edit(
            f"❌ **Upload Failed**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"*\"Sometimes even I fail at things.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    finally:
        # Cleanup
        try:
            os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except:
            pass

# Handle callback for upload type selection
@Client.on_callback_query(filters.regex(r"upload_(video|doc|audio)\|"))
async def handle_upload_type(client: Client, query):
    user_id = query.from_user.id
    data = query.data.split("|")
    upload_type = data[0].replace("upload_", "")
    
    # Get stored rename data
    user_data = await db.get_user(user_id)
    temp_data = user_data.get("temp_rename")
    
    if not temp_data:
        return await query.answer("❌ Session expired! Please try again.", show_alert=True)
    
    # Get original message
    try:
        original_msg = await client.get_messages(
            temp_data["chat_id"],
            temp_data["original_msg_id"]
        )
    except:
        return await query.answer("❌ Original file not found!", show_alert=True)
    
    await query.message.edit("🎭 Processing your request...")
    
    # Map upload type
    if upload_type == "doc":
        upload_type = "document"
    
    # Process rename
    await process_rename(
        client,
        query.message,
        original_msg,
        temp_data["filename"],
        upload_type
    )
    
    # Clear temp data
    await db.users.update_one(
        {"_id": user_id},
        {"$unset": {"temp_rename": ""}}
    )

@Client.on_callback_query(filters.regex("cancel_rename"))
async def cancel_rename(client: Client, query):
    await query.message.edit(
        "❌ **Rename Cancelled**\n\n"
        "*\"Sometimes giving up is the wisest choice.\"*",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Clear temp data
    await db.users.update_one(
        {"_id": query.from_user.id},
        {"$unset": {"temp_rename": ""}}
    )
