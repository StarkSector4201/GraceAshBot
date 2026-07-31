from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.config import MASTER_ID, OWNER_ID
from core.auth import is_owner, is_admin
from core.settings import load_settings, save_settings, get_group_settings
from core.logger import logger

# Note: We will need a way to access get_phrase. 
# For now, we'll assume it will be imported from the main entry point or a new translate module.
from gracebot import get_phrase, get_lock_reason

async def cmd_glock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Globally lock a command across all chats."""
    try:
        if not await is_owner(update, context):
            await update.message.reply_text("❌ Security Breach: Master key authorization required."); return
            
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: `/glock <cmd_name> <reason>`", parse_mode="Markdown"); return
            
        cmd_to_lock = context.args[0].lower().replace("/", "")
        reason = " ".join(context.args[1:])
        
        settings = load_settings()
        if "global_locks" not in settings: settings["global_locks"] = {}
        settings["global_locks"][cmd_to_lock] = reason
        save_settings(settings)
        
        await update.message.reply_text(get_phrase(update.effective_chat.id, "lock_activated", cmd=cmd_to_lock, reason=reason), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in glock: {e}")

async def cmd_gunlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unlock a globally locked command."""
    try:
        if not await is_owner(update, context):
            await update.message.reply_text("❌ Security Breach: Master key authorization required."); return
            
        if not context.args:
            await update.message.reply_text("Usage: `/gunlock <cmd_name>`", parse_mode="Markdown"); return
            
        cmd_to_unlock = context.args[0].lower().replace("/", "")
        settings = load_settings()
        if "global_locks" in settings and cmd_to_unlock in settings["global_locks"]:
            del settings["global_locks"][cmd_to_unlock]
            save_settings(settings)
            await update.message.reply_text(f"🔓 Command `/{cmd_to_unlock}` has been released.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❓ Command `/{cmd_to_unlock}` is not currently locked.")
    except Exception as e:
        logger.error(f"Error in gunlock: {e}")
