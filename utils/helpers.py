# utils/helpers.py - Enhanced Utility Functions with Dazai Theme
import math
import time
import os
import asyncio
import aiofiles
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Progress bar characters for elegant display
PROGRESS_BAR = {
    'filled': '█',
    'empty': '░',
    'partial': ['▏', '▎', '▍', '▌', '▋', '▊', '▉']
}

# Dazai-themed progress messages
PROGRESS_MESSAGES = [
    "Even the longest journey begins with a single step...",
    "Patience is a virtue I'm still learning...",
    "Progress, like poetry, takes time to perfect...",
    "Every moment brings us closer to completion...",
    "The art of waiting is often underappreciated..."
]

async def progress_for_pyrogram(current: int, total: int, ud_type: str, message, start_time: float):
    """Enhanced progress callback with Dazai-themed messages"""
    now = time.time()
    diff = now - start_time
    
    # Only update every 3 seconds or on completion to avoid flooding
    if round(diff % 3.00) == 0 or current == total:
        percentage = (current * 100 / total) if total > 0 else 0
        speed = current / diff if diff > 0 else 0
        
        try:
            eta = int((total - current) / speed) if speed > 0 else 0
        except:
            eta = 0
        
        # Create elegant progress bar
        progress_length = 20
        filled_length = math.floor(percentage / 5)
        progress_bar = ''.join([PROGRESS_BAR['filled'] for _ in range(filled_length)])
        progress_bar += ''.join([PROGRESS_BAR['empty'] for _ in range(progress_length - filled_length)])
        
        # Format time
        elapsed_str = convert_seconds_to_readable(int(diff))
        eta_str = convert_seconds_to_readable(eta) if eta > 0 else "Calculating..."
        
        # Choose a random Dazai quote based on progress
        quote_index = int(percentage / 20) % len(PROGRESS_MESSAGES)
        quote = PROGRESS_MESSAGES[quote_index]
        
        progress_text = f"""🎭 **{ud_type}**

[{progress_bar}] {percentage:.1f}%

📊 **Progress:** {humanbytes(current)} / {humanbytes(total)}
⚡ **Speed:** {humanbytes(speed)}/s
⏱️ **Elapsed:** {elapsed_str}
⏳ **ETA:** {eta_str}

*"{quote}"*"""
        
        try:
            await message.edit_text(
                progress_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
                ])
            )
        except Exception as e:
            logger.debug(f"Progress update failed: {e}")
            pass

def humanbytes(size: int) -> str:
    """Convert bytes to human readable format with improved precision"""
    if not size:
        return "0 B"
    
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB', 5: 'PB'}
    
    while size > power and n < 5:
        size /= power
        n += 1
    
    if n == 0:
        return f"{size} {power_labels[n]}"
    else:
        return f"{size:.2f} {power_labels[n]}"

def convert_seconds_to_readable(seconds: int) -> str:
    """Convert seconds to readable time format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def add_prefix_suffix(filename: str, prefix: str = '', suffix: str = '') -> str:
    """Add prefix and suffix to filename while preserving extension"""
    if not filename:
        return filename
    
    # Split filename and extension
    base, ext = os.path.splitext(filename)
    
    # Add prefix and suffix
    if prefix:
        base = f"{prefix.rstrip()} {base}"
    if suffix:
        base = f"{base} {suffix.lstrip()}"
    
    return f"{base}{ext}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters"""
    # Characters that are generally problematic in filenames
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove multiple consecutive spaces and leading/trailing spaces
    filename = ' '.join(filename.split())
    
    # Ensure filename is not too long (255 chars is typical filesystem limit)
    if len(filename) > 255:
        base, ext = os.path.splitext(filename)
        max_base_length = 255 - len(ext)
        filename = base[:max_base_length] + ext
    
    return filename

async def remove_path(*paths) -> None:
    """Asynchronously remove multiple file paths"""
    for path in paths:
        try:
            if path and os.path.exists(path):
                await asyncio.get_event_loop().run_in_executor(None, os.remove, path)
                logger.debug(f"Removed file: {path}")
        except Exception as e:
            logger.debug(f"Failed to remove {path}: {e}")

async def ensure_directory(directory: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")

def extract_file_info(file) -> Dict[str, Any]:
    """Extract comprehensive file information"""
    if not file:
        return {
            'file_name': None,
            'mime_type': None,
            'file_size': 0,
            'duration': 0,
            'width': 0,
            'height': 0,
            'file_id': None,
            'file_unique_id': None
        }
    
    return {
        'file_name': getattr(file, 'file_name', None) or getattr(file, 'fileName', None),
        'mime_type': getattr(file, 'mime_type', None) or getattr(file, 'mimeType', None),
        'file_size': getattr(file, 'file_size', 0) or getattr(file, 'size', 0),
        'duration': getattr(file, 'duration', 0),
        'width': getattr(file, 'width', 0),
        'height': getattr(file, 'height', 0),
        'file_id': getattr(file, 'file_id', None),
        'file_unique_id': getattr(file, 'file_unique_id', None)
    }

def format_caption(template: str, file_info: Dict[str, Any], custom_vars: Optional[Dict[str, str]] = None) -> str:
    """Format caption template with file information and custom variables"""
    if not template:
        return ""
    
    # Default variables
    variables = {
        'filename': file_info.get('file_name', 'Unknown'),
        'filesize': humanbytes(file_info.get('file_size', 0)),
        'duration': convert_seconds_to_readable(file_info.get('duration', 0)) if file_info.get('duration') else 'N/A',
        'filetype': get_file_type_from_mime(file_info.get('mime_type', '')),
        'width': file_info.get('width', 0),
        'height': file_info.get('height', 0),
        'resolution': f"{file_info.get('width', 0)}x{file_info.get('height', 0)}" if file_info.get('width') else 'N/A'
    }
    
    # Add custom variables if provided
    if custom_vars:
        variables.update(custom_vars)
    
    # Replace variables in template
    try:
        formatted_caption = template.format(**variables)
        return formatted_caption
    except KeyError as e:
        logger.warning(f"Caption template contains unknown variable: {e}")
        return template
    except Exception as e:
        logger.error(f"Caption formatting error: {e}")
        return template

def get_file_type_from_mime(mime_type: str) -> str:
    """Get human-readable file type from MIME type"""
    if not mime_type:
        return "Document"
    
    type_mapping = {
        'video': 'Video',
        'audio': 'Audio', 
        'image': 'Image',
        'application/pdf': 'PDF',
        'application/zip': 'Archive',
        'application/x-zip-compressed': 'Archive',
        'application/x-rar-compressed': 'Archive',
        'text': 'Text'
    }
    
    for key, value in type_mapping.items():
        if key in mime_type.lower():
            return value
    
    return "Document"

async def get_file_duration(file_path: str) -> int:
    """Get duration of video/audio file using ffprobe"""
    try:
        import subprocess
        import json
        
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', file_path
        ]
        
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            data = json.loads(stdout.decode())
            duration = float(data.get('format', {}).get('duration', 0))
            return int(duration)
    except:
        pass
    
    return 0

def create_temp_filename(original_name: str, user_id: int) -> str:
    """Create unique temporary filename"""
    timestamp = int(time.time())
    base, ext = os.path.splitext(original_name)
    return f"{timestamp}_{user_id}_{sanitize_filename(base)}{ext}"

class TempDataManager:
    """Temporary data storage for user sessions"""
    
    def __init__(self):
        self._data = {}
    
    def set(self, user_id: int, key: str, value: Any) -> None:
        """Set temporary data for user"""
        if user_id not in self._data:
            self._data[user_id] = {}
        self._data[user_id][key] = value
    
    def get(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get temporary data for user"""
        return self._data.get(user_id, {}).get(key, default)
    
    def delete(self, user_id: int, key: str = None) -> None:
        """Delete temporary data for user"""
        if user_id in self._data:
            if key:
                self._data[user_id].pop(key, None)
            else:
                self._data.pop(user_id, None)
    
    def clear_expired(self, max_age: int = 3600) -> None:
        """Clear expired temporary data (older than max_age seconds)"""
        current_time = time.time()
        expired_users = []
        
        for user_id, user_data in self._data.items():
            if isinstance(user_data.get('timestamp'), (int, float)):
                if current_time - user_data['timestamp'] > max_age:
                    expired_users.append(user_id)
        
        for user_id in expired_users:
            self._data.pop(user_id, None)

# Global temp data manager instance
temp_data = TempDataManager()

# Dazai quotes for various situations
DAZAI_QUOTES = {
    'start': [
        "Life is precious, that's why it should be beautiful.",
        "The weak crumble, are slaughtered and are erased. That is the law of the world.",
        "I want to see the world burn with my own eyes.",
        "Everything I do is meaningless. But that meaninglessness will help someone.",
    ],
    'success': [
        "Another task completed with artistic precision.",
        "Excellence achieved through careful dedication.",
        "Like poetry in motion, perfectly executed.",
        "Success tastes sweeter when earned through effort.",
    ],
    'error': [
        "Even the best plans sometimes encounter obstacles.",
        "Failure teaches us more than success ever could.",
        "Every setback is merely setup for a comeback.",
        "In chaos, there is opportunity.",
    ],
    'waiting': [
        "Patience is the companion of wisdom.",
        "Good things come to those who wait.",
        "Time reveals all truths eventually.",
        "The art of waiting is often undervalued.",
    ]
}

def get_random_quote(category: str = 'start') -> str:
    """Get a random Dazai quote from specified category"""
    import random
    quotes = DAZAI_QUOTES.get(category, DAZAI_QUOTES['start'])
    return random.choice(quotes)
