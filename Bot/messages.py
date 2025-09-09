# Bot/messages.py - Dazai-themed Message Templates
from typing import Dict

class DazaiMessages:
    """Centralized message templates with Dazai theme from Bungo Stray Dogs"""
    
    # Main welcome message
    START = """🎭 **Welcome to Dazai's File Renaming Atelier** 

Greetings, {user}! I am Osamu Dazai, master of words and files alike. 

**What I can do:**
• Rename any file with artistic precision
• Add custom prefixes and suffixes
• Set personalized captions and thumbnails
• Embed metadata information
• Work in both private chats and groups

**How to use:**
Send me any file and I'll guide you through renaming it beautifully.

*"Words are the dress of thoughts, and I shall tailor yours perfectly."*"""

    # Help message
    HELP = """📚 **Dazai's Complete Guide**

**File Renaming:**
• Send any document, video, or audio file
• Reply with your desired filename
• Choose upload format (document/video/audio)

**Caption Management:**
• `/set_caption` - Create custom caption templates
• `/view_caption` - See current template
• `/del_caption` - Remove caption template
• Use variables: `{filename}`, `{filesize}`, `{duration}`, `{filetype}`

**Prefix & Suffix:**
• `/set_prefix [text]` - Add text before filename
• `/set_suffix [text]` - Add text after filename
• `/view_prefix` & `/view_suffix` - View current settings
• `/del_prefix` & `/del_suffix` - Remove settings

**Thumbnail Settings:**
• Send any photo to set as video thumbnail
• `/view_thumb` - Preview current thumbnail
• `/del_thumb` - Remove thumbnail

**Metadata Configuration:**
• `/metadata` - Configure file metadata
• Add author and title information
• Enable/disable metadata embedding

**General Commands:**
• `/settings` - View all your settings
• `/reset_all` - Reset everything to defaults
• `/stats` - View your usage statistics

**Group Usage:**
Mention me (@{bot_username}) or reply to my messages to use in groups.

*"Every masterpiece requires the right tools and technique."*"""

    # About message
    ABOUT = """🎭 **About Dazai Rename Bot**

I am {bot_name}, inspired by Osamu Dazai from Bungo Stray Dogs - a character known for his complex nature and literary genius. Just as Dazai crafts beautiful yet melancholic prose, I help you craft perfect filenames.

**Technical Details:**
• Built with Pyrogram {pyrogram_version}
• Supports files up to 2GB (4GB with premium sessions)
• Works in private chats and groups
• Fast, reliable, and user-friendly

**Features:**
• Intelligent file renaming
• Custom caption templates
• Prefix/suffix management
• Video thumbnail support
• Metadata embedding
• Group compatibility

**Philosophy:**
Like Dazai's writing, every renamed file tells a story. I believe in the beauty of organization and the art of digital expression.

*"In every filename lies the potential for poetry."*

Made with dedication for file organization enthusiasts."""

    # File rename prompt
    RENAME_PROMPT = """📁 **File Received - Ready to Rename**

**Current Details:**
• **Name:** `{filename}`
• **Size:** `{filesize}`
• **Type:** {filetype}

**Instructions:**
Reply to this message with your desired filename. I'll handle the rest with artistic precision.

**Tips:**
• Include file extension or I'll keep the original
• Use descriptive names for better organization
• Consider your prefix/suffix settings

*"Even I have my limits, unlike my desire for perfect naming."*"""

    # Progress messages
    DOWNLOAD_PROGRESS = "📥 **Downloading File**\n\n*\"Patience is a virtue I'm still learning...\"*"
    UPLOAD_PROGRESS = "📤 **Uploading Masterpiece**\n\n*\"The final touches make all the difference...\"*"
    PROCESSING_PROGRESS = "⚙️ **Processing File**\n\n*\"Perfection takes time, even for someone like me...\"*"

    # Error messages
    ERROR_FILE_TOO_LARGE = """❌ **File Size Exceeded**

Your file is too large for processing:
• **Your file:** `{filesize}`
• **Maximum allowed:** `{maxsize}`

*"Even my abilities have their boundaries."*

**Suggestion:** Try compressing the file or use a premium Telegram account for larger files."""

    ERROR_DOWNLOAD_FAILED = """❌ **Download Failed**

I encountered an issue while downloading your file:
`{error}`

*"Sometimes even the best plans encounter obstacles."*

Please try again or contact support if the issue persists."""

    ERROR_UPLOAD_FAILED = """❌ **Upload Failed**

I couldn't upload your renamed file:
`{error}`

*"Failure teaches us more than success ever could."*

Please try again with a different format or contact support."""

    ERROR_INVALID_FILENAME = """❌ **Invalid Filename**

The filename you provided contains invalid characters or is too long.

**Rules:**
• Avoid: `< > : " / \\ | ? *`
• Maximum length: 255 characters
• Cannot be empty

*"Even creativity needs boundaries."*

Please provide a valid filename."""

    # Success messages
    SUCCESS_SETTINGS_UPDATED = """✅ **Settings Updated Successfully**

Your preferences have been saved and will be applied to future file operations.

*"Another step towards perfection."*"""

    SUCCESS_FILE_RENAMED = """✅ **File Renamed Successfully**

Your file has been processed and renamed with artistic precision.

**Details:**
• **New name:** `{filename}`
• **Size:** `{filesize}`
• **Processing time:** `{duration}`

*"Another masterpiece completed."*"""

    SUCCESS_RESET_COMPLETE = """✅ **Settings Reset Complete**

All your settings have been restored to their default state. You can now configure everything fresh according to your preferences.

*"Sometimes we need a clean slate to write our best stories."*"""

    # Confirmation messages
    CONFIRM_RESET_ALL = """⚠️ **Confirm Settings Reset**

This will permanently delete all your customizations:
• Caption templates
• Prefix and suffix settings
• Thumbnail image
• Metadata configuration

This action cannot be undone.

*"Destruction can be a form of creation."*"""

    CONFIRM_DELETE_CAPTION = """⚠️ **Confirm Caption Deletion**

Are you sure you want to remove your current caption template?

Current template:
`{caption}`

*"Sometimes silence speaks louder than words."*"""

    # Information messages
    INFO_NO_SETTINGS = """ℹ️ **No Settings Configured**

You haven't configured any custom settings yet. Here's what you can set up:

• **Caption Template** - Custom captions for files
• **Prefix/Suffix** - Text added to filenames
• **Thumbnail** - Custom image for videos
• **Metadata** - Author and title information

Use `/settings` to see all options and `/help` for detailed instructions.

*"Every journey begins with a single step."*"""

    INFO_GROUP_USAGE = """ℹ️ **Using in Groups**

To use me in group chats:
• Mention me: @{bot_username}
• Reply to my messages
• Send files with mentions in caption

**Example:**
Send a file with caption: "Rename this @{bot_username}"

*"Even in crowds, I can hear your call."*"""

    # Metadata specific messages
    METADATA_HELP = """📊 **Metadata Configuration**

Metadata adds information directly into your files that can be read by media players and file managers.

**Available Options:**
• **Author** - Your name or identifier
• **Title** - Default title for files
• **Enable/Disable** - Toggle metadata embedding

**Supported Files:**
Video and audio files support metadata embedding.

**Usage:**
Use `/metadata` command to access the configuration menu.

*"Even files deserve proper attribution."*"""

    # Admin messages
    ADMIN_STATS = """📊 **Bot Statistics (Admin)**

**User Statistics:**
• **Total Users:** `{total_users}`
• **Active Users (24h):** `{active_users}`
• **Files Processed Today:** `{files_today}`

**System Information:**
• **CPU Usage:** `{cpu_usage}%`
• **RAM Usage:** `{ram_usage}%`
• **Disk Usage:** `{disk_usage}%`
• **Uptime:** `{uptime}`

*"Numbers tell stories that words sometimes cannot."*"""

    ADMIN_BROADCAST_START = """📢 **Broadcast Started**

Sending message to all users...

*"Spreading words across the digital realm."*"""

    ADMIN_BROADCAST_COMPLETE = """✅ **Broadcast Complete**

**Results:**
• **Successful:** `{success}`
• **Failed:** `{failed}`
• **Total:** `{total}`

*"Message delivered to those who matter."*"""

    # Special occasion messages
    FIRST_FILE_CONGRATULATIONS = """🎉 **Congratulations!**

You've successfully renamed your first file with my assistance. This is the beginning of a beautiful journey toward perfect file organization.

*"Every expert was once a beginner."*"""

    MILESTONE_MESSAGES = {
        10: "You've renamed 10 files! You're getting the hang of this.",
        50: "50 files renamed! You're becoming quite the organization expert.", 
        100: "100 files! You've truly mastered the art of file naming.",
        500: "500 files! Your dedication to organization is inspiring.",
        1000: "1000 files! You've achieved legendary status in file management."
    }

    @staticmethod
    def get_milestone_message(count: int) -> str:
        """Get milestone message for file count"""
        milestones = sorted(DazaiMessages.MILESTONE_MESSAGES.keys())
        for milestone in milestones:
            if count == milestone:
                return f"🎯 **Milestone Achieved!**\n\n{DazaiMessages.MILESTONE_MESSAGES[milestone]}\n\n*\"Progress is the sweetest reward.\"*"
        return ""

    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        """Format message template with provided variables"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Message formatting error: missing variable {e}"
        except Exception as e:
            return f"Message formatting error: {e}"

# Create instance for easy importing
Messages = DazaiMessages()
