# plugins/rename.py - Enhanced File Renaming Core with Dazai Theme
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pyrogram.enums import MessageMediaType, ParseMode, ChatType
from pyrogram.errors import FloodWait
import asyncio
import os
import time
from datetime import datetime
from utils.database import db
from utils.helpers import (
    humanbytes, 
    progress_for_pyrogram, 
    add_prefix_suffix,
    extract_file_info,
    format_caption,
    create_temp_filename,
    remove_path,
    sanitize_filename,
    get_random_quote,
    temp_data
)
from utils.ffmpeg import ffmpeg_handler, change_metadata
from Bot.config import Config
from Bot.messages import Messages
import logging

logger = logging.getLogger(__name__)

# In-memory storage for rename sessions to handle restarts gracefully
rename_sessions = {}

class RenameSession:
    """Class to manage rename sessions"""
    def __init__(self, user_id, file_message, chat_id):
        self.user_id = user_id
        self.file_message = file_message
        self.chat_id = chat_id
        self.timestamp = time.time()
        self.new_filename = None
        self.status = "waiting_for_name"
    
    def is_expired(self, max_age=1800):  # 30 minutes
        return time.time() - self.timestamp > max_age

def clean_expired_sessions():
    """Clean up expired rename sessions"""
    expired_keys = [k for k, v in rename_sessions.items() if v.is_expired()]
    for key in expired_keys:
        del rename_sessions[key]

# Handle files sent to bot (works in both private and groups)
@Client.on_message(filters.document | filters.video | filters.audio)
async def rename_file_handler(client: Client, message: Message):
    """Handle file uploads for renaming"""
    
    # Clean expired sessions periodically
    if len(rename_sessions) > 100:
        clean_expired_sessions()
    
    # Check if in group and bot was mentioned or replied to
    if message.chat.type != ChatType.PRIVATE:
        bot_me = await client.get_me()
        if not (message.reply_to_message and 
                message.reply_to_message.from_user and 
                message.reply_to_message.from_user.is_self):
            # Check if bot is mentioned
            if f"@{bot_me.username}" not in (message.text or "") and \
               f"@{bot_me.username}" not in (message.caption or ""):
                return
    
    user_id = message.from_user.id
    
    try:
        # Add user to database and update activity
        await db.add_user(user_id, message.from_user.username)
        await db.update_user_activity(user_id)
        
        # Get file info
        file = message.document or message.video or message.audio
        if not file:
            return
        
        file_info = extract_file_info(file)
        
        # Check file size limits
        max_size = Config.MAX_FILE_SIZE
        
        # Check if premium session is available and file is larger than free limit
        if hasattr(Config, 'STRING_SESSION') and Config.STRING_SESSION:
            max_size = max(max_size, 4 * 1024 * 1024 * 1024)  # 4GB for premium
        
        if file_info['file_size'] > max_size:
            size_error = Messages.ERROR_FILE_TOO_LARGE.format(
                filesize=humanbytes(file_info['file_size']),
                maxsize=humanbytes(max_size)
            )
            return await message.reply_text(size_error, parse_mode=ParseMode.MARKDOWN)
        
        # Create rename session
        session_key = f"{message.chat.id}_{user_id}"
        rename_sessions[session_key] = RenameSession(user_id, message, message.chat.id)
        
        # Create enhanced rename prompt
        prompt_text = Messages.RENAME_PROMPT.format(
            filename=file_info['file_name'] or 'unknown',
            filesize=humanbytes(file_info['file_size']),
            filetype=get_file_type_display(file_info['mime_type'])
        )
        
        # Add quick action buttons for common operations
        keyboard = [
            [
                InlineKeyboardButton("🔄 Keep Original", callback_data=f"keep_original_{session_key}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_rename_{session_key}")
            ]
        ]
        
        # Send prompt with ForceReply
        prompt_msg = await message.reply_text(
            prompt_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send ForceReply for filename input
        await message.reply_text(
            "✍️ **Enter New Filename:**\n\n"
            "*Reply to this message with your desired filename*",
            reply_markup=ForceReply(
                placeholder="Enter new filename...",
                selective=True
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.debug(f"Rename session created for user {user_id}, file: {file_info['file_name']}")
        
    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
        await message.reply_text(
            f"❌ **Error Processing File**\n\n"
            f"Please try again or contact support.\n\n"
            f"*\"{get_random_quote('error')}\"*",
            parse_mode=ParseMode.MARKDOWN
        )

def get_file_type_display(mime_type):
    """Get user-friendly file type display"""
    if not mime_type:
        return "Document"
    
    if mime_type.startswith('video/'):
        return "Video"
    elif mime_type.startswith('audio/'):
        return "Audio"
    elif mime_type.startswith('image/'):
        return "Image"
    else:
        return "Document"

# Handle rename response (when user replies with new filename)
@Client.on_message(filters.reply & filters.text)
async def handle_rename_response(client: Client, message: Message):
    """Handle user's filename response"""
    
    # Check if this is a reply to our ForceReply prompt
    if not (message.reply_to_message and 
            message.reply_to_message.from_user and 
            message.reply_to_message.from_user.is_self and
            message.reply_to_message.reply_markup and
            isinstance(message.reply_to_message.reply_markup, ForceReply)):
        return
    
    user_id = message.from_user.id
    session_key = f"{message.chat.id}_{user_id}"
    
    # Check if we have an active rename session
    if session_key not in rename_sessions:
        return await message.reply_text(
            "❌ **Session Expired**\n\n"
            "Please send the file again to rename it.\n\n"
            f"*\"{get_random_quote('error')}\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    session = rename_sessions[session_key]
    if session.is_expired():
        del rename_sessions[session_key]
        return await message.reply_text(
            "⏰ **Session Expired**\n\n"
            "Please send the file again to rename it.\n\n"
            f"*\"Time waits for no one, not even for perfect names.\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    new_filename = message.text.strip()
    
    # Validate filename
    if not new_filename or len(new_filename) > 255:
        return await message.reply_text(
            Messages.ERROR_INVALID_FILENAME,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # Sanitize filename
    new_filename = sanitize_filename(new_filename)
    
    # Get original file
    original_msg = session.file_message
    file = original_msg.document or original_msg.video or original_msg.audio
    
    if not file:
        del rename_sessions[session_key]
        return await message.reply_text("❌ **Original file not found!**")
    
    # Add extension if missing
    if "." not in new_filename and file.file_name and "." in file.file_name:
        original_ext = file.file_name.rsplit(".", 1)[-1]
        new_filename = f"{new_filename}.{original_ext}"
    elif "." not in new_filename:
        # Default extensions based on file type
        if file == original_msg.video:
            new_filename = f"{new_filename}.mp4"
        elif file == original_msg.audio:
            new_filename = f"{new_filename}.mp3"
        else:
            new_filename = f"{new_filename}.file"
    
    # Get user settings and apply prefix/suffix
    try:
        user_data = await db.get_user_data(user_id)
        prefix = user_data.get("prefix", "")
        suffix = user_data.get("suffix", "")
        final_filename = add_prefix_suffix(new_filename, prefix, suffix)
    except:
        final_filename = new_filename
    
    # Store the filename in session
    session.new_filename = final_filename
    session.status = "choosing_format"
    
    # Show upload format selection
    file_type = get_file_type_display(file.mime_type)
    
    keyboard = []
    
    # Add format options based on file type
    if file == original_msg.video or file.mime_type.startswith('video/'):
        keyboard.append([
            InlineKeyboardButton("🎬 Upload as Video", callback_data=f"upload_video_{session_key}"),
            InlineKeyboardButton("📄 Upload as Document", callback_data=f"upload_document_{session_key}")
        ])
    elif file == original_msg.audio or file.mime_type.startswith('audio/'):
        keyboard.append([
            InlineKeyboardButton("🎵 Upload as Audio", callback_data=f"upload_audio_{session_key}"),
            InlineKeyboardButton("📄 Upload as Document", callback_data=f"upload_document_{session_key}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("📄 Upload as Document", callback_data=f"upload_document_{session_key}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_rename_{session_key}")
    ])
    
    format_text = f"📋 **Choose Upload Format**\n\n"
    format_text += f"**New filename:** `{final_filename}`\n"
    format_text += f"**File size:** `{humanbytes(file.file_size)}`\n"
    format_text += f"**Original type:** {file_type}\n\n"
    format_text += f"*\"The format shapes the experience, like death shapes life.\"*"
    
    await message.reply_text(
        format_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Clean up the ForceReply message
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except:
        pass

# Handle upload format selection callbacks
@Client.on_callback_query(filters.regex(r"^upload_(video|audio|document)_"))
async def handle_upload_format(client: Client, query):
    """Handle upload format selection"""
    
    try:
        parts = query.data.split("_", 2)
        upload_format = parts[1]
        session_key = parts[2]
        
        if session_key not in rename_sessions:
            return await query.answer("❌ Session expired! Please try again.", show_alert=True)
        
        session = rename_sessions[session_key]
        
        if session.is_expired():
            del rename_sessions[session_key]
            return await query.answer("⏰ Session expired! Please try again.", show_alert=True)
        
        if query.from_user.id != session.user_id:
            return await query.answer("❌ This is not your session!", show_alert=True)
        
        # Start the rename process
        await query.message.edit_text(
            f"🎭 **Processing Your Request**\n\n"
            f"*\"{get_random_quote('waiting')}\"*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Process the rename
        success = await process_file_rename(
            client, 
            session, 
            upload_format,
            query.message
        )
        
        # Clean up session
        del rename_sessions[session_key]
        
        if success:
            await query.message.edit_text(
                Messages.SUCCESS_FILE_RENAMED.format(
                    filename=session.new_filename,
                    filesize=humanbytes(session.file_message.document.file_size if session.file_message.document 
                                      else session.file_message.video.file_size if session.file_message.video
                                      else session.file_message.audio.file_size),
                    duration="Processing completed"
                ),
                parse_mode=ParseMode.MARKDOWN
            )
        
    except Exception as e:
        logger.error(f"Error in upload format callback: {e}")
        await query.answer("❌ An error occurred. Please try again.", show_alert=True)

async def process_file_rename(client: Client, session: RenameSession, upload_format: str, progress_msg: Message):
    """Process the actual file renaming and upload"""
    
    try:
        user_id = session.user_id
        original_msg = session.file_message
        new_filename = session.new_filename
        
        file = original_msg.document or original_msg.video or original_msg.audio
        
        # Create unique temporary filename
        temp_filename = create_temp_filename(new_filename, user_id)
        download_path = f"downloads/{temp_filename}"
        
        # Ensure downloads directory exists
        os.makedirs("downloads", exist_ok=True)
        
        # Update progress message
        await progress_msg.edit_text(
            f"📥 **Downloading File**\n\n"
            f"**File:** `{file.file_name}`\n"
            f"**Size:** `{humanbytes(file.file_size)}`\n\n"
            f"*\"{get_random_quote('waiting')}\"*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Download file with progress
        start_time = time.time()
        try:
            downloaded_file = await client.download_media(
                original_msg,
                file_name=download_path,
                progress=progress_for_pyrogram,
                progress_args=(Messages.DOWNLOAD_PROGRESS, progress_msg, start_time)
            )
        except Exception as e:
            logger.error(f"Download failed: {e}")
            error_msg = Messages.ERROR_DOWNLOAD_FAILED.format(error=str(e))
            await progress_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)
            return False
        
        # Get user settings
        try:
            user_data = await db.get_user_data(user_id)
            
            # Prepare metadata if enabled
            metadata = user_data.get("metadata", {})
            if metadata.get("enabled") and ffmpeg_handler.is_available():
                metadata_str = ""
                if metadata.get("author"):
                    metadata_str += f"--change-author {metadata['author']} "
                if metadata.get("title"):
                    metadata_str += f"--change-title {metadata['title']} "
                
                if metadata_str:
                    # Apply metadata
                    await progress_msg.edit_text(
                        f"⚙️ **Processing Metadata**\n\n"
                        f"*\"Adding the author's signature to the work...\"*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    output_path = f"{download_path}.processed"
                    if await change_metadata(download_path, output_path, metadata_str.strip()):
                        # Replace original with processed file
                        await remove_path(download_path)
                        os.rename(output_path, download_path)
                        downloaded_file = download_path
            
            # Prepare for upload
            await progress_msg.edit_text(
                f"📤 **Preparing Upload**\n\n"
                f"**Format:** {upload_format.title()}\n"
                f"**Name:** `{new_filename}`\n\n"
                f"*\"{get_random_quote('waiting')}\"*",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Get caption and thumbnail
            caption_template = user_data.get("caption")
            thumbnail = user_data.get("thumbnail")
            
            # Format caption
            file_info = extract_file_info(file)
            if caption_template:
                caption = format_caption(caption_template, file_info, {
                    'bot_name': 'Dazai Rename Bot'
                })
            else:
                caption = f"**{new_filename}**\n\n*Renamed with artistic precision by Dazai Bot*"
            
            # Download thumbnail if available
            thumb_path = None
            if thumbnail and upload_format in ['video', 'audio']:
                try:
                    thumb_path = await client.download_media(thumbnail, f"downloads/thumb_{user_id}.jpg")
                except Exception as e:
                    logger.debug(f"Thumbnail download failed: {e}")
            
            # Upload the file
            start_time = time.time()
            
            upload_kwargs = {
                'progress': progress_for_pyrogram,
                'progress_args': (Messages.UPLOAD_PROGRESS, progress_msg, start_time),
                'file_name': new_filename
            }
            
            if upload_format == "video":
                upload_kwargs.update({
                    'caption': caption,
                    'thumb': thumb_path,
                    'duration': getattr(file, 'duration', 0),
                    'width': getattr(file, 'width', 0),
                    'height': getattr(file, 'height', 0)
                })
                await client.send_video(
                    chat_id=session.chat_id,
                    video=downloaded_file,
                    **upload_kwargs
                )
            
            elif upload_format == "audio":
                upload_kwargs.update({
                    'caption': caption,
                    'thumb': thumb_path,
                    'duration': getattr(file, 'duration', 0)
                })
                await client.send_audio(
                    chat_id=session.chat_id,
                    audio=downloaded_file,
                    **upload_kwargs
                )
            
            else:  # document
                upload_kwargs['caption'] = caption
                await client.send_document(
                    chat_id=session.chat_id,
                    document=downloaded_file,
                    **upload_kwargs
                )
            
            # Update user statistics
            await db.increment_renamed_count(user_id)
            
            # Check for milestones
            user_stats = await db.get_user_stats(user_id)
            files_count = user_stats.get('files_renamed', 0)
            milestone_msg = Messages.get_milestone_message(files_count)
            
            if milestone_msg:
                await client.send_message(session.chat_id, milestone_msg, parse_mode=ParseMode.MARKDOWN)
            
            logger.info(f"File renamed successfully for user {user_id}: {new_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            error_msg = Messages.ERROR_UPLOAD_FAILED.format(error=str(e))
            await progress_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)
            return False
        
        finally:
            # Clean up temporary files
            await remove_path(downloaded_file, thumb_path)
    
    except Exception as e:
        logger.error(f"Process rename error: {e}")
        await progress_msg.edit_text(
            f"❌ **Processing Failed**\n\n"
            f"An unexpected error occurred: `{str(e)}`\n\n"
            f"*\"{get_random_quote('error')}\"*",
            parse_mode=ParseMode.MARKDOWN
        )
        return False

# Handle other callback queries
@Client.on_callback_query(filters.regex(r"^(keep_original|cancel_rename)_"))
async def handle_rename_actions(client: Client, query):
    """Handle keep original and cancel actions"""
    
    action, session_key = query.data.rsplit("_", 1)
    
    if session_key not in rename_sessions:
        return await query.answer("❌ Session expired!", show_alert=True)
    
    session = rename_sessions[session_key]
    
    if query.from_user.id != session.user_id:
        return await query.answer("❌ Not your session!", show_alert=True)
    
    if action == "keep_original":
        # Keep original filename but still process the file
        original_msg = session.file_message
        file = original_msg.document or original_msg.video or original_msg.audio
        
        if file and file.file_name:
            session.new_filename = file.file_name
            session.status = "choosing_format"
            
            # Show format selection
            keyboard = [
                [InlineKeyboardButton("📄 Upload as Document", callback_data=f"upload_document_{session_key}")],
                [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_rename_{session_key}")]
            ]
            
            await query.message.edit_text(
                f"📋 **Upload Original File**\n\n"
                f"**Filename:** `{file.file_name}`\n"
                f"**Size:** `{humanbytes(file.file_size)}`\n\n"
                f"*\"Sometimes the original holds its own beauty.\"*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            del rename_sessions[session_key]
            await query.message.edit_text(
                "❌ **No original filename found**\n\n"
                f"*\"Even originals need their identity.\"*",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif action == "cancel_rename":
        del rename_sessions[session_key]
        await query.message.edit_text(
            "❌ **Rename Cancelled**\n\n"
            f"*\"{get_random_quote('error')}\"*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    await query.answer()
