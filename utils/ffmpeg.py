# utils/ffmpeg.py - Enhanced FFmpeg Operations for Dazai Rename Bot
import subprocess
import json
import shutil
import logging
import asyncio
import os
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None
    logger.warning("imageio-ffmpeg not installed. Falling back to system ffmpeg.")

class FFmpegError(Exception):
    """Custom exception for FFmpeg-related errors"""
    pass

class DazaiFFmpeg:
    """Enhanced FFmpeg handler with Dazai bot integration"""
    
    def __init__(self):
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self._resolve_binaries()
    
    def _resolve_binaries(self) -> None:
        """Resolve FFmpeg and FFprobe binary paths"""
        # Try imageio-ffmpeg first (bundled)
        if imageio_ffmpeg:
            try:
                self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                logger.debug(f"Using imageio-ffmpeg: {self.ffmpeg_path}")
            except Exception as e:
                logger.debug(f"imageio-ffmpeg failed: {e}")
                self.ffmpeg_path = None
        
        # Fallback to system FFmpeg
        if not self.ffmpeg_path:
            self.ffmpeg_path = shutil.which('ffmpeg')
            if self.ffmpeg_path:
                logger.debug(f"Using system ffmpeg: {self.ffmpeg_path}")
        
        # Find FFprobe
        self.ffprobe_path = shutil.which('ffprobe')
        if self.ffprobe_path:
            logger.debug(f"Using ffprobe: {self.ffprobe_path}")
        
        # Log availability
        if not self.ffmpeg_path:
            logger.warning("FFmpeg not found! Video processing will be limited.")
        if not self.ffprobe_path:
            logger.warning("FFprobe not found! Media info extraction will be limited.")
    
    def is_available(self) -> bool:
        """Check if FFmpeg is available"""
        return bool(self.ffmpeg_path)
    
    def is_ffprobe_available(self) -> bool:
        """Check if FFprobe is available"""
        return bool(self.ffprobe_path)
    
    async def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive media information using FFprobe
        
        Args:
            file_path (str): Path to the media file
            
        Returns:
            Dict containing media information
        """
        if not self.ffprobe_path or not os.path.exists(file_path):
            return {}
        
        cmd = [
            self.ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        try:
            logger.debug(f"Running FFprobe: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFprobe failed: {stderr.decode()}")
                return {}
            
            data = json.loads(stdout.decode())
            
            # Extract useful information
            info = {
                'duration': 0,
                'width': 0,
                'height': 0,
                'bitrate': 0,
                'fps': 0,
                'codec': '',
                'format': '',
                'has_video': False,
                'has_audio': False,
                'file_size': 0
            }
            
            # Format information
            format_info = data.get('format', {})
            info['duration'] = float(format_info.get('duration', 0))
            info['bitrate'] = int(format_info.get('bit_rate', 0))
            info['format'] = format_info.get('format_name', '')
            info['file_size'] = int(format_info.get('size', 0))
            
            # Stream information
            streams = data.get('streams', [])
            for stream in streams:
                codec_type = stream.get('codec_type', '')
                
                if codec_type == 'video':
                    info['has_video'] = True
                    info['width'] = int(stream.get('width', 0))
                    info['height'] = int(stream.get('height', 0))
                    info['codec'] = stream.get('codec_name', '')
                    
                    # Calculate FPS
                    r_frame_rate = stream.get('r_frame_rate', '0/1')
                    if '/' in r_frame_rate:
                        num, den = r_frame_rate.split('/')
                        if int(den) > 0:
                            info['fps'] = round(int(num) / int(den), 2)
                
                elif codec_type == 'audio':
                    info['has_audio'] = True
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting media info: {e}")
            return {}
    
    async def change_metadata(self, input_file: str, output_file: str, 
                            metadata: Dict[str, str]) -> bool:
        """
        Change file metadata with enhanced options
        
        Args:
            input_file (str): Input file path
            output_file (str): Output file path
            metadata (dict): Metadata to apply
            
        Returns:
            bool: Success status
        """
        if not self.ffmpeg_path or not os.path.exists(input_file):
            logger.error("FFmpeg not available or input file doesn't exist")
            return False
        
        try:
            # Get stream information for advanced metadata
            streams_info = await self._get_streams_info(input_file)
            
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-map', '0',
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero'
            ]
            
            # Apply global metadata
            for key, value in metadata.items():
                if value and value.strip():
                    cmd.extend(['-metadata', f'{key}={value.strip()}'])
            
            # Apply stream-specific metadata if streams are available
            if streams_info:
                for stream_index, stream_type in streams_info.items():
                    title_key = f'{stream_type}_title'
                    if title_key in metadata and metadata[title_key]:
                        cmd.extend([f'-metadata:s:{stream_index}', f'title={metadata[title_key]}'])
            
            # Add Dazai bot signature
            cmd.extend(['-metadata', 'comment=Processed by Dazai Rename Bot - Where art meets technology'])
            
            # Output format based on extension
            output_ext = Path(output_file).suffix.lower()
            if output_ext in ['.mkv', '.mp4', '.avi']:
                cmd.extend(['-f', 'matroska' if output_ext == '.mkv' else 'mp4'])
            
            cmd.append(output_file)
            
            logger.debug(f"Running FFmpeg: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"FFmpeg metadata change failed: {error_msg}")
                
                # Try to provide helpful error messages
                if "Invalid argument" in error_msg:
                    logger.error("Metadata values may contain invalid characters")
                elif "Permission denied" in error_msg:
                    logger.error("File permission error")
                elif "No such file" in error_msg:
                    logger.error("Input or output file path issue")
                
                return False
            
            # Verify output file was created
            if not os.path.exists(output_file):
                logger.error("Output file was not created")
                return False
            
            logger.info(f"Successfully applied metadata to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Exception during metadata change: {e}")
            return False
    
    async def _get_streams_info(self, file_path: str) -> Dict[int, str]:
        """Get stream types for metadata application"""
        if not self.ffprobe_path:
            return {}
        
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {}
            
            data = json.loads(stdout.decode())
            streams = data.get('streams', [])
            
            stream_info = {}
            for stream in streams:
                index = stream.get('index')
                codec_type = stream.get('codec_type')
                if index is not None and codec_type:
                    stream_info[index] = codec_type
            
            return stream_info
            
        except Exception:
            return {}
    
    async def extract_thumbnail(self, video_path: str, output_path: str, 
                              time_offset: str = "00:00:01") -> bool:
        """
        Extract thumbnail from video file
        
        Args:
            video_path (str): Input video path
            output_path (str): Output thumbnail path
            time_offset (str): Time offset for thumbnail extraction
            
        Returns:
            bool: Success status
        """
        if not self.ffmpeg_path or not os.path.exists(video_path):
            return False
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-ss', time_offset,
                '-vframes', '1',
                '-q:v', '2',
                '-y',  # Overwrite output file
                output_path
            ]
            
            logger.debug(f"Extracting thumbnail: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Thumbnail extracted: {output_path}")
                return True
            else:
                logger.error(f"Thumbnail extraction failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Exception during thumbnail extraction: {e}")
            return False
    
    async def convert_audio(self, input_file: str, output_file: str, 
                          codec: str = "aac", bitrate: str = "128k") -> bool:
        """
        Convert audio with specified codec and bitrate
        
        Args:
            input_file (str): Input file path
            output_file (str): Output file path
            codec (str): Audio codec
            bitrate (str): Audio bitrate
            
        Returns:
            bool: Success status
        """
        if not self.ffmpeg_path:
            return False
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_file,
                '-c:a', codec,
                '-b:a', bitrate,
                '-y',
                output_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return False
    
    def parse_metadata_string(self, metadata_string: str) -> Dict[str, str]:
        """
        Parse metadata string into dictionary
        Compatible with old format while supporting new options
        
        Args:
            metadata_string (str): Metadata string with flags
            
        Returns:
            Dict of metadata key-value pairs
        """
        metadata = {}
        
        # Parse old format flags
        flags = [flag.strip() for flag in metadata_string.split('--') if flag.strip()]
        
        for flag in flags:
            if flag.startswith('change-author'):
                metadata['author'] = flag.replace('change-author', '').strip()
            elif flag.startswith('change-title'):
                metadata['title'] = flag.replace('change-title', '').strip()
            elif flag.startswith('change-video-title'):
                metadata['video_title'] = flag.replace('change-video-title', '').strip()
            elif flag.startswith('change-audio-title'):
                metadata['audio_title'] = flag.replace('change-audio-title', '').strip()
            elif flag.startswith('change-subtitle-title'):
                metadata['subtitle_title'] = flag.replace('change-subtitle-title', '').strip()
        
        return metadata

# Global instance for easy access
ffmpeg_handler = DazaiFFmpeg()

# Compatibility functions for existing code
async def change_metadata(input_file: str, output_file: str, metadata_text: str) -> bool:
    """
    Legacy compatibility function for metadata changes
    
    Args:
        input_file (str): Input file path
        output_file (str): Output file path
        metadata_text (str): Metadata configuration string
        
    Returns:
        bool: Success status
    """
    metadata = ffmpeg_handler.parse_metadata_string(metadata_text)
    return await ffmpeg_handler.change_metadata(input_file, output_file, metadata)

async def get_media_duration(file_path: str) -> int:
    """
    Get media file duration in seconds
    
    Args:
        file_path (str): Path to media file
        
    Returns:
        int: Duration in seconds
    """
    info = await ffmpeg_handler.get_media_info(file_path)
    return int(info.get('duration', 0))

async def get_video_resolution(file_path: str) -> Tuple[int, int]:
    """
    Get video resolution
    
    Args:
        file_path (str): Path to video file
        
    Returns:
        Tuple of (width, height)
    """
    info = await ffmpeg_handler.get_media_info(file_path)
    return (info.get('width', 0), info.get('height', 0))

def get_ffmpeg_version() -> Optional[str]:
    """
    Get FFmpeg version string
    
    Returns:
        str: FFmpeg version or None if not available
    """
    if not ffmpeg_handler.ffmpeg_path:
        return None
    
    try:
        result = subprocess.run(
            [ffmpeg_handler.ffmpeg_path, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split('\n')[0]
            if 'version' in first_line:
                return first_line.strip()
        
        return None
        
    except Exception:
        return None

# Initialize on import
def initialize_ffmpeg() -> bool:
    """
    Initialize FFmpeg handler and check availability
    
    Returns:
        bool: True if FFmpeg is available
    """
    global ffmpeg_handler
    ffmpeg_handler = DazaiFFmpeg()
    
    if ffmpeg_handler.is_available():
        version = get_ffmpeg_version()
        logger.info(f"FFmpeg initialized successfully: {version}")
        return True
    else:
        logger.warning("FFmpeg not available. Some features will be limited.")
        return False

# Auto-initialize
_ffmpeg_available = initialize_ffmpeg()
