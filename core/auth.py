from telegram import Update
from telegram.ext import ContextTypes
from core.config import MASTER_ID, OWNER_ID, SUDO_USERS

def _is_sudo_or_master(user_id: int, username: str = None) -> bool:
    """Helper to check for core high-level bypasses."""
    if user_id == MASTER_ID: return True
    if user_id in SUDO_USERS: return True
    if username and username.lower() in SUDO_USERS: return True
    return False

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if user has administrative rights in the current context."""
    try:
        user = update.effective_user
        if not user: return False
        
        username = f"@{user.username}" if user.username else None
        if _is_sudo_or_master(user.id, username):
            return True
            
        # Anonymous admin check
        if update.effective_message and update.effective_message.sender_chat:
            sc = update.effective_message.sender_chat
            if sc.type == 'channel' or sc.id == update.effective_chat.id:
                return True
                
        if update.effective_chat.type == 'private':
            return True
            
        member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        return member.status in ['administrator', 'creator']
    except Exception:
        return False

async def is_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Checks if user is the designated bot owner or master."""
    user = update.effective_user
    if not user: return False
    
    username = f"@{user.username}" if user.username else None
    if _is_sudo_or_master(user.id, username):
        return True
        
    return user.id == OWNER_ID
