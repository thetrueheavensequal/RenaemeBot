from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Bot.config import Config, set_env_var, get_env_var, list_env_keys
from utils.database import db
import time
import psutil


@Client.on_message(filters.command("listenv") & filters.user(Config.ADMIN_ID))
async def listenv_cmd(client, message):
    keys = list_env_keys()
    await message.reply_text("🔑 Allowed environment keys:\n" + "\n".join(f"- `{k}`" for k in keys))


@Client.on_message(filters.command("getenv") & filters.user(Config.ADMIN_ID))
async def getenv_cmd(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply_text("Usage: /getenv KEY")
    key = parts[1].strip()
    val = get_env_var(key)
    if val is None:
        return await message.reply_text("Key not allowed or not set")
    await message.reply_text(f"`{key}` = `{val}`")


@Client.on_message(filters.command("setenv") & filters.user(Config.ADMIN_ID))
async def setenv_cmd(client, message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply_text("Usage: /setenv KEY VALUE")
    key = parts[1].strip()
    value = parts[2].strip()
    ok = set_env_var(key, value)
    if not ok:
        return await message.reply_text("Key not allowed or failed to set")
    await message.reply_text(f"✅ `{key}` updated to `{value}`")


@Client.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def admin_stats(client, message):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    total_users = await db.total_users_count()
    uptime = time.time() - client.start_time if hasattr(client, 'start_time') else 0
    await message.reply_text(f"📊 CPU: {cpu}%\n🧠 RAM: {ram}%\n👥 Users: {total_users}\n⏱ Uptime: {int(uptime)}s")


@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID))
async def broadcast_command(client, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to broadcast it.")
    broadcast_msg = message.reply_to_message
    users = db.get_all_users()
    success = 0
    failed = 0
    status = await message.reply_text("📣 Broadcasting...")
    async for user in users:
        try:
            await broadcast_msg.copy(user["_id"])
            success += 1
        except Exception:
            failed += 1
        if (success + failed) % 20 == 0:
            await status.edit(f"📣 Broadcasting...\n✅ Success: {success}\n❌ Failed: {failed}")
    await status.edit(f"✅ Broadcast complete\nSuccess: `{success}`\nFailed: `{failed}`")


@Client.on_message(filters.command("reload") & filters.user(Config.ADMIN_ID))
async def reload_cmd(client, message):
    await message.reply_text("🔄 Reload requested. Some changes are applied live; a full restart may be required for others.")
