# -*- coding: utf-8 -*-
import os
import sys
import logging
import warnings
import shutil
from pathlib import Path

# --- System Paths (Dynamic Resolution) ---
def get_binary_path(name, fallback):
    """Detects binary in system PATH, Environment, or uses fallback."""
    return os.getenv(f"{name.upper().replace('-', '_')}_PATH") or shutil.which(name) or fallback

YT_DLP_PATH = get_binary_path("yt-dlp", r"C:\Users\abyad\AppData\Local\Programs\Python\Python310\Scripts\yt-dlp.exe")
FFMPEG_PATH = get_binary_path("ffmpeg", r"C:\Users\abyad\AppData\Local\Programs\Python\Python310\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")
COOKIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

"""
GraceAshcroftBot - Inspired by Grace Ashcroft from Resident Evil: Requiem
FBI Technical Analyst personality — anxious, analytical, determined.
Same commands and permissions as MaríaBot.
"""

import json
import copy
import asyncio
import random
import tempfile
import glob
import threading
import time as _time
import re as _re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import deque
from dotenv import load_dotenv
import httpx as _httpx
import psutil
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, ConversationHandler, filters
from telegram.error import RetryAfter
from telegram.request import HTTPXRequest
import feedparser
from bs4 import BeautifulSoup as _BS
from grace_phrases import PHRASES
from services.ai import ask_gemini, ask_groq

from collections import OrderedDict

# --- STATE MANAGEMENT (Fixed-Size LRU Caches) ---
class LimitedDict(OrderedDict):
    """A dictionary that limits itself to a maximum number of keys (LRU policy)."""
    def __init__(self, max_limit=500, *args, **kwargs):
        self.max_limit = max_limit
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if len(self) > self.max_limit:
            self.popitem(last=False)  # Evict the oldest entry (LRU)

# --- Global Volatile Buffers ---
_chat_msg_buffer = LimitedDict(max_limit=2000) 

def escape_md(text: str) -> str:
    """Escapes special characters for Telegram's MarkdownV2 format."""
    # List of special characters that need to be escaped in MarkdownV2
    specials = r"[\_\*\[\]\(\)\~\`\#\+\-\=\|\{\}\.\!]"
    return _re.sub(specials, lambda m: "\\" + m.group(0), str(text))

# Paths for Grace's animation files (Mute videos)
MUTE_ANIMATION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Avatar", "mute.gif.mp4")
MILA_MUTE_VIDEO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Avatar", "mute2.gif.mp4")

# Load environment variables
load_dotenv()

# Configuration
TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "n0amtell")
GITHUB_REPO = os.getenv("GITHUB_REPO", "https://github.com/YourUsername/grace-bot")
DEFAULT_DIALECT = os.getenv("DIALECT", "arabic_fousha")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Beirut"))
BOT_START_TIME = datetime.now(TIMEZONE)
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
MASTER_ID = int(os.getenv("MASTER_ID", "0"))
INVITE_PASSWORD = os.getenv("INVITE_PASSWORD", "")
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "")
INTEL_CHANNEL = os.getenv("INTEL_CHANNEL", "")  # Dedicated channel for intelligence reports
GRACE_PROXY   = os.getenv("GRACE_PROXY", "")
PO_TOKEN      = os.getenv("PO_TOKEN", "")      # YouTube Proof of Origin Token
VISITOR_DATA  = os.getenv("VISITOR_DATA", "")  # YouTube Visitor Data
GRACE_COOKIES = os.getenv("GRACE_COOKIES", "") # Browser to pull cookies from (chrome/firefox/edge)
SAUCENAO_KEY  = os.getenv("SAUCENAO_API_KEY", "")  # Free API key from saucenao.com

_sudo_raw = os.getenv("SUDO_USERS", "")
SUDO_USERS = []
if _sudo_raw:
    for item in _sudo_raw.split(","):
        item = item.strip()
        if not item: continue
        if item.startswith("@"):
            SUDO_USERS.append(item.lower())
        elif item.isdigit():
            SUDO_USERS.append(int(item))
        else:
            SUDO_USERS.append(item.lower())

SETTINGS_FILE = "grace_settings.json"
message_history = LimitedDict(max_limit=500)   # Caps AI context memory
group_stats = LimitedDict(max_limit=1000)      # Caps group metrics memory
repeat_history = LimitedDict(max_limit=1000)   # Caps spam filter memory
pending_invites = LimitedDict(max_limit=100)
pending_captcha = LimitedDict(max_limit=200)
pending_apply = LimitedDict(max_limit=100)
_umbrella_game_state = LimitedDict(max_limit=100)
# Removed legacy INTEL constants to consolidate monitoring into NEWS_SOURCES.

# --- BACKGROUND TASK REGISTRY (prevents GC + catches silent failures) ---
_background_tasks: set = set()

def safe_create_task(coro, *, name=None):
    """Create a tracked async task with automatic error logging and GC protection.
    
    Solves two problems with raw asyncio.create_task():
    1. Stores a strong reference so the task can't be garbage-collected mid-flight
    2. Logs any unhandled exceptions instead of silently swallowing them
    """
    task = asyncio.create_task(coro, name=name)
    _background_tasks.add(task)
    
    def _on_done(t):
        _background_tasks.discard(t)
        if t.cancelled():
            return
        exc = t.exception()
        if exc:
            logger.warning(f"Background task '{t.get_name()}' failed: {exc}")
    
    task.add_done_callback(_on_done)
    return task


import random
from _apply_data import APPLY_QUESTIONS, APPLY_INTRO
# --- PHRASES LOADED FROM MODULE ---


DIALECT_NAMES = {
    "english": "English 🇬🇧",
    "arabic_fousha": "Arabic (Fousha) 🇸🇦",
}

# ─────────────────────────────────────────────────────────────────────────────
# Logging — colored console + full file log
# ─────────────────────────────────────────────────────────────────────────────

class _GraceConsoleFormatter(logging.Formatter):
    """ANSI-colored, single-line formatter for the live terminal output."""
    _RESET  = "\033[0m"
    _BOLD   = "\033[1m"
    _DIM    = "\033[2m"
    _COLORS = {
        logging.DEBUG:    "\033[96m",   # bright cyan
        logging.INFO:     "\033[92m",   # bright green
        logging.WARNING:  "\033[93m",   # bright yellow
        logging.ERROR:    "\033[91m",   # bright red
        logging.CRITICAL: "\033[95m",   # bright magenta
    }
    _ICONS = {
        logging.DEBUG:    "🔵",
        logging.INFO:     "✅",
        logging.WARNING:  "⚠️ ",
        logging.ERROR:    "❌",
        logging.CRITICAL: "💥",
    }

    def format(self, record: logging.LogRecord) -> str:
        color  = self._COLORS.get(record.levelno, self._RESET)
        icon   = self._ICONS.get(record.levelno, "  ")
        ts     = datetime.now().strftime("%H:%M:%S")
        level  = record.levelname.ljust(8)
        msg    = record.getMessage()
        # Show traceback only for ERROR+
        exc = ""
        if record.exc_info and record.levelno >= logging.ERROR:
            exc = "\n" + self.formatException(record.exc_info)
        return (
            f"{self._DIM}[{ts}]{self._RESET} "
            f"{color}{self._BOLD}{icon} {level}{self._RESET} "
            f"{msg}{exc}"
        )


class _LibraryNoiseFilter(logging.Filter):
    """Suppress chatty third-party library logs from the console."""
    _SUPPRESS = {
        "urllib3", "charset_normalizer", "asyncio", "apscheduler",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        # ALWAYS allow the bot's own logs (usually __main__ or gracebot)
        if record.name == "__main__" or record.name.startswith("gracebot"):
            return True
        root = record.name.split(".")[0]
        return root not in self._SUPPRESS


# ── File handler — captures EVERYTHING (DEBUG+) ─────────────────────────────
_file_handler = logging.FileHandler("gracebot.log", encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)

# ── Console handler — show only bot-level INFO+ in color ────────────────────
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_GraceConsoleFormatter())
_console_handler.addFilter(_LibraryNoiseFilter())

# ── Root logger ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.DEBUG, handlers=[_file_handler, _console_handler])

# Silence noisy libraries globally (but allow httpx and telegram INFO for user tracking)
for _noisy_lib in ("urllib3", "apscheduler"):
    logging.getLogger(_noisy_lib).setLevel(logging.WARNING)

for _tracked_lib in ("httpx", "httpcore", "telegram"):
    logging.getLogger(_tracked_lib).setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# ── Startup banner ───────────────────────────────────────────────────────────
def _print_banner():
    if hasattr(sys.stdout, "reconfigure"):
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
    B = "\033[94m"; C = "\033[96m"; W = "\033[97m"; R = "\033[0m"; BLD = "\033[1m"
    try:
        print(f"""
{B}{'━'*54}{R}
{BLD}{C}   🔬  GRACE ASHCROFT BOT  —  Live Monitor{R}
{B}{'━'*54}{R}
{W}  Actions, warnings and errors appear here in real time.
  Full debug log → gracebot.log{R}
{B}{'━'*54}{R}
""")
    except Exception:
        pass


# --- SETTINGS MANAGEMENT (DeepScope High-Performance Cache) ---
_SETTINGS_CACHE = None
_SETTINGS_LOCK = threading.Lock()           # Disk I/O serialization only
_SETTINGS_ASYNC_LOCK = asyncio.Lock()       # Async transaction lock
_SAVE_TIMER = None                          # Debounce timer for coalesced writes

def _default_settings():
    """Canonical settings schema — single source of truth for default structure."""
    return {"groups": {}, "warnings": {}, "global_locks": {}, "last_news_ids": [], "last_news_titles": []}

def load_settings():
    """Returns the settings from memory cache (Zero-Latency). Loads from disk only once."""
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is not None:
        return _SETTINGS_CACHE
        
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                _SETTINGS_CACHE = json.load(f)
        else:
            _SETTINGS_CACHE = _default_settings()
    except (FileNotFoundError, json.JSONDecodeError):
        _SETTINGS_CACHE = _default_settings()
    
    return _SETTINGS_CACHE

def save_settings(settings=None):
    """Marks cache dirty and schedules a debounced disk write (2s coalesce window).
    
    All 40+ call sites mutate the shared cache reference directly, so the in-memory
    state is always current. This function only needs to schedule the disk persistence.
    Multiple rapid calls coalesce into a single write, eliminating thread leak.
    """
    global _SETTINGS_CACHE, _SAVE_TIMER
    if settings is not None:
        _SETTINGS_CACHE = settings
    
    # Cancel any pending write — this new save supersedes it
    if _SAVE_TIMER is not None:
        _SAVE_TIMER.cancel()
    
    # Schedule coalesced disk write after 2s debounce window
    _SAVE_TIMER = threading.Timer(2.0, _flush_to_disk)
    _SAVE_TIMER.daemon = True
    _SAVE_TIMER.start()

def _flush_to_disk():
    """Performs the actual disk write. Serialized via _SETTINGS_LOCK."""
    with _SETTINGS_LOCK:
        try:
            # deepcopy runs inside the lock to guarantee a consistent snapshot
            data = copy.deepcopy(_SETTINGS_CACHE)
            temp_file = SETTINGS_FILE + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, SETTINGS_FILE)
        except Exception as e:
            logger.error(f"Failed to save settings to disk: {e}")

def _flush_settings_sync():
    """Synchronous flush for shutdown hooks. Ensures no data loss on exit."""
    global _SAVE_TIMER
    if _SAVE_TIMER is not None:
        _SAVE_TIMER.cancel()
        _SAVE_TIMER = None
    if _SETTINGS_CACHE is not None:
        _flush_to_disk()

import atexit
atexit.register(_flush_settings_sync)

from contextlib import asynccontextmanager

@asynccontextmanager
async def settings_session():
    """
    Forensic transaction manager for settings. 
    Ensures atomic read-modify-write cycles across concurrent async handlers.
    """
    async with _SETTINGS_ASYNC_LOCK:
        settings = load_settings()
        yield settings
        save_settings(settings)

def get_lock_reason(command_name):
    """Returns the lock reason from cache (Zero-Latency)."""
    settings = load_settings()
    locks = settings.get("global_locks", {})
    return locks.get(command_name)

def get_group_settings(chat_id):
    """Fetches group configuration from cache. Non-blocking — no threading locks.
    
    Safe without locks because all async handlers run on the same event loop thread,
    and this function contains no await points, so it executes atomically.
    """
    settings = load_settings()
    chat_id = str(chat_id)
    if chat_id not in settings["groups"]:
        settings["groups"][chat_id] = {
            "welcome": None,
            "rules": None,
            "dialect": DEFAULT_DIALECT,
            "link_filter": False,
            "ai_enabled": False,
            "members": []
        }
        save_settings()
    return settings["groups"][chat_id]

def get_phrase(chat_id, key, **kwargs):
    group_settings = get_group_settings(chat_id)
    dialect = group_settings.get("dialect", DEFAULT_DIALECT)
    phrase = PHRASES.get(dialect, PHRASES["english"]).get(key, "")
    return phrase.format(**kwargs) if kwargs else phrase

# --- ADMIN CHECK ---

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

async def log_event(context, action: str, chat_title: str, admin_name: str, target_name: str, reason: str = ""):
    if not LOG_CHANNEL:
        return
    try:
        now = datetime.now(TIMEZONE)
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        icons = {
            "warn": "⚠️", "mute": "🔇", "unmute": "🔊",
            "kick": "🌂", "ban": "🚫",
            "captcha_pass": "✅", "captcha_fail": "❌"
        }
        icon = icons.get(action, "📝")
        log_msg_channel = (
            f"{icon} **{action.upper()}**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 Group: {chat_title}\n"
            f"👮 Admin: {admin_name}\n"
            f"👤 Target: {target_name}\n"
        )
        if reason:
            log_msg_channel += f"📝 Reason: {reason}\n"
        log_msg_channel += f"🕐 Time: {time_str}"

        # Local console tracking (Action Tracking)
        logger.info(f"Action: {action.upper()} | Group: {chat_title} | Admin: {admin_name} | Target: {target_name}")

        await context.bot.send_message(int(LOG_CHANNEL), log_msg_channel, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Could not send log to channel: {e}")

# --- REMOVED: NSFW / AI LOGIC DECOMMISSIONED ---

# --- YOUTUBE AUDIO HELPER ---


# --- GMusic Service Integrated ---



# =============================================================================
# /gsource — Face Identification & Person Recognition (Yandex)
# =============================================================================

async def _upload_to_telegraph(image_bytes: bytes) -> str:
    """Upload image to Telegraph or fallback hosts for a public URL."""
    # 1. Telegraph
    try:
        async with _httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post("https://telegra.ph/upload", files={"file": ("image.jpg", image_bytes, "image/jpeg")})
            if resp.status_code == 200 and (data := resp.json()) and isinstance(data, list):
                return f"https://telegra.ph{data[0]['src']}"
    except: pass

    # 2. Catbox.moe
    try:
        async with _httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": ("image.jpg", image_bytes, "image/jpeg")})
            if resp.status_code == 200 and resp.text.startswith("http"):
                return resp.text.strip()
    except: pass

    # 3. File.io (Fast and reliable)
    try:
        async with _httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post("https://file.io", data={"expires": "1h"}, files={"file": ("image.jpg", image_bytes, "image/jpeg")})
            if resp.status_code == 200 and (data := resp.json()).get("link"):
                return data["link"]
    except: pass

    return ""

async def _yandex_identify(public_url: str) -> dict:
    """Yandex face recognition — extract person name, tags, and similar images."""
    result = {"name": "", "tags": [], "similar_images": []}
    if not public_url:
        return result
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        from urllib.parse import quote
        url = f"https://yandex.com/images/search?rpt=imageview&url={quote(public_url, safe='')}"
        proxy_cfg = GRACE_PROXY if GRACE_PROXY and GRACE_PROXY.strip() else None
        async with _httpx.AsyncClient(timeout=30.0, proxy=proxy_cfg, headers=headers, follow_redirects=True, trust_env=False) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"Yandex failed: {resp.status_code}")
                return result
            html = resp.text
            logger.info(f"🔍 Yandex HTML: {len(html)} bytes")

            tags = []

            # Method 1: CBIR Tags JSON block — "tags":[{"text":"Name",...}]
            tag_blocks = _re.findall(r'"tags"\s*:\s*\[([^\]]{5,2000})\]', html)
            for block in tag_blocks:
                found = _re.findall(r'"text"\s*:\s*"([^"]{2,80})"', block)
                tags.extend(found)

            # Method 2: CbirTags section in HTML
            cbir_section = _re.findall(r'CbirTags.*?</div>', html, _re.DOTALL)
            for section in cbir_section[:2]:
                found = _re.findall(r'>([^<]{2,60})<', section)
                tags.extend(found)

            # Method 3: Entity/person name patterns
            entities = _re.findall(r'"entity"\s*:\s*\{[^}]*?"name"\s*:\s*"([^"]{2,60})"', html)
            tags.extend(entities)

            # Method 4: Similar faces section
            faces = _re.findall(r'CbirSimilar(?:People|Faces)[^}]*?"name"\s*:\s*"([^"]{2,60})"', html, _re.DOTALL)
            tags.extend(faces)

            # Method 5: Page title often has person name
            title_match = _re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                raw_title = title_match.group(1).strip()
                # Clean "Yandex Images" suffix
                raw_title = _re.sub(r'\s*[-—|]\s*Yandex.*$', '', raw_title, flags=_re.IGNORECASE).strip()
                if raw_title and len(raw_title) > 2 and "search" not in raw_title.lower():
                    tags.insert(0, raw_title)

            # Method 6: description/snippet text that might contain name
            snippets = _re.findall(r'"snippet"\s*:\s*"([^"]{5,100})"', html)
            tags.extend(snippets[:3])

            # Deduplicate and clean
            seen = set()
            clean = []
            noise = {"yandex", "images", "search", "cbir", "undefined", "null", "error", "loading", "button"}
            for t in tags:
                t = t.strip()
                if len(t) < 2 or t.lower() in seen:
                    continue
                if t.lower() in noise or t.startswith(("{", "<", "http", "//", "function")):
                    continue
                seen.add(t.lower())
                clean.append(t)

            result["tags"] = clean[:12]
            
            # Smart name selection: skip generic phrases and category labels
            noise_phrases = [
                "yandex images", "image appears to contain", "search by image", "found on", 
                "photo of", "picture of", "эротика", "порно", "девушка", "красивая", 
                "erotica", "porn", "sexy", "girl", "beautiful", "nsfw", "onlyfans", 
                "leaked", "free", "video", "photos", "images", "model"
            ]
            for candidate in clean:
                if any(p in candidate.lower() for p in noise_phrases):
                    continue
                result["name"] = candidate
                break
            
            if not result["name"] and clean:
                result["name"] = clean[0]

            # Extract similar image URLs
            # Priority 1: Specifically "Similar People / Faces" section
            person_imgs = []
            similar_blocks = _re.findall(r'CbirSimilar(?:People|Faces)":\[(.*?)\]', html, _re.DOTALL)
            for block in similar_blocks:
                # Find direct image URLs or avatar URLs in this block
                found = _re.findall(r'"(?:url|src|thumbUrl|origUrl)"\s*:\s*"(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', block)
                person_imgs.extend(found)
                found_av = _re.findall(r'(https?://avatars\.mds\.yandex\.net/[^"\'>\s]+)', block)
                person_imgs.extend(found_av)

            # Priority 2: Generic similar images
            generic_imgs = _re.findall(r'"(?:url|src|href|thumbUrl|origUrl)"\s*:\s*"(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html)
            generic_thumbs = _re.findall(r'(https?://avatars\.mds\.yandex\.net/[^"\'>\s]+)', html)
            
            # Combine and deduplicate
            all_candidates = person_imgs + generic_imgs + generic_thumbs
            seen_i = set()
            final_imgs = []
            
            # Filter logic: skip original URL and duplicate patterns
            # We want DIFFERENT images, so we skip the first one if it's very similar to the source
            source_parts = set(_re.findall(r'[a-zA-Z0-9]{5,}', public_url.lower()))
            
            for u in all_candidates:
                u_low = u.lower()
                # Skip self-links
                if u_low in seen_i or "yandex.com/images" in u_low or len(u) > 500:
                    continue
                # Simple similarity check: if URL shares too many path components with source, it might be the same photo
                u_parts = set(_re.findall(r'[a-zA-Z0-9]{5,}', u_low))
                intersection = source_parts.intersection(u_parts)
                if len(intersection) > 3: # Likely same file or very similar source
                    continue
                    
                seen_i.add(u_low)
                final_imgs.append(u)
            
            # If we have person-specific images, pick from them first
            # We skip the first one (often the same photo) and take 2 and 3
            if len(final_imgs) >= 3:
                result["similar_images"] = final_imgs[1:3]
            else:
                result["similar_images"] = final_imgs[:2]

            logger.info(f"🔍 Yandex ID: name='{result['name']}' tags={result['tags'][:5]} imgs={len(result['similar_images'])} (candidates={len(final_imgs)})")
    except Exception as e:
        logger.warning(f"Yandex identify error: {e}")
    return result

async def _generate_bio(tags: list, is_ar: bool = False) -> dict:
    """Use AI to identify the person from tags and generate a bio."""
    if not tags or not GROQ_API_KEY:
        return {"name": "", "bio": ""}
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        tag_str = ", ".join(tags)
        lang_instruction = "Respond ONLY in Arabic (Saudi dialect)." if is_ar else "Respond ONLY in English."
        
        system_prompt = (
            "You are a forensic identity analyst. Given search tags, identify the specific person's REAL NAME. "
            "CRITICAL: Ignore generic category words like 'erotica', 'nsfw', 'model', 'girl', etc. "
            "Translate names to English or Arabic. "
            f"Write a 2-3 sentence biography. {lang_instruction} "
            "Format your response as valid JSON: {\"name\": \"...\", \"bio\": \"...\"}. "
            "If no specific person is identified, return empty strings."
        )
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Tags: {tag_str}"}
            ],
            "temperature": 0.1, "response_format": {"type": "json_object"}
        }
        
        async with _httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()["choices"][0]["message"]["content"]
                parsed = json.loads(data)
                return {"name": parsed.get("name", ""), "bio": parsed.get("bio", "")}
    except Exception as e:
        logger.warning(f"Bio generation error: {e}")
    return {"name": "", "bio": ""}

async def _yandex_keyword_search(query: str) -> list:
    """Fallback: Perform a keyword image search to find more photos of the person."""
    if not query:
        return []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
        from urllib.parse import quote
        url = f"https://yandex.com/images/search?text={quote(query)}"
        proxy_cfg = GRACE_PROXY if GRACE_PROXY else None
        async with _httpx.AsyncClient(timeout=15.0, proxy=proxy_cfg, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                html = resp.text
                # Extract image URLs from the search results
                found = _re.findall(r'"(?:url|src|thumbUrl|origUrl)"\s*:\s*"(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html)
                # Clean and deduplicate
                res = []
                seen = set()
                for u in found:
                    if u not in seen and "yandex.com/images" not in u and len(u) < 500:
                        seen.add(u)
                        res.append(u)
                return res[:10]
    except Exception as e:
        logger.warning(f"Keyword search error: {e}")
    return []

async def cmd_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gsource — Face identification and person recognition."""
    chat_id = update.effective_chat.id
    # Global Lock Check
    if reason := get_lock_reason("gsource"):
        await update.message.reply_text(get_phrase(chat_id, "lock_denied_gsource", reason=reason), parse_mode="Markdown")
        return

    if not update.message:
        return
    chat_id = update.effective_chat.id
    gs = get_group_settings(chat_id)
    is_ar = gs.get("dialect", DEFAULT_DIALECT) == "arabic_fousha"

    target = update.message.reply_to_message or update.message
    photo = None
    if target.photo:
        photo = target.photo[-1]
    elif target.document and (target.document.mime_type or "").startswith("image/"):
        photo = target.document
    elif target.sticker and not target.sticker.is_animated and not target.sticker.is_video:
        photo = target.sticker

    if not photo:
        await update.message.reply_text(
            ("🔬 **غريس أشكروفت — التعرف على الهوية**\n━━━━━━━━━━━━━━━━━━━━━\nيرجى الرد على صورة شخص بالأمر `/gsource`\n\n_سأحلل الوجه وأحدد هوية الشخص._ 📋" if is_ar else
             "🔬 **Grace Ashcroft — Face Identification**\n━━━━━━━━━━━━━━━━━━━━━\nReply to a photo of a person with `/gsource`\n\n_I'll analyze the face and identify who they are._ 📋"),
            parse_mode="Markdown")
        return

    status = await update.message.reply_text(
        ("🔬 **تحليل الوجه...**\n_رفع الصورة..._" if is_ar else "🔬 **Analyzing face...**\n_Uploading image..._"), parse_mode="Markdown")

    try:
        tg_file = await context.bot.get_file(photo.file_id)
        image_bytes = bytes(await tg_file.download_as_bytearray())

        public_url = await _upload_to_telegraph(image_bytes)
        if not public_url:
            public_url = tg_file.file_path or ""
        if not public_url:
            await status.edit_text("❌ " + ("فشل رفع الصورة." if is_ar else "Image upload failed."))
            return

        try:
            await status.edit_text(("🔬 **مسح قاعدة بيانات الوجوه...**" if is_ar else "🔬 **Scanning face database...**"), parse_mode="Markdown")
        except: pass
        yd = await _yandex_identify(public_url)

        bio_data = {"name": yd["name"], "bio": ""}
        if yd["tags"]:
            try:
                await status.edit_text(("🔬 **تم رصد شخص... جاري استخراج البيانات...**" if is_ar else "🔬 **Person detected... extracting profile...**"), parse_mode="Markdown")
            except: pass
            bio_data = await _generate_bio(yd["tags"], is_ar=is_ar)

        # Use AI-refined name if available
        final_name = bio_data.get("name") or yd["name"]
        final_bio = bio_data.get("bio")

        # Fallback: If we don't have enough similar images, perform a keyword search for the name
        if len(yd["similar_images"]) < 2 and final_name:
            try:
                await status.edit_text(("🔬 **البحث عن صور إضافية...**" if is_ar else "🔬 **Searching for additional photos...**"), parse_mode="Markdown")
            except: pass
            more_imgs = await _yandex_keyword_search(final_name)
            for img in more_imgs:
                if img not in yd["similar_images"]:
                    yd["similar_images"].append(img)
                if len(yd["similar_images"]) >= 3: # Keep 2-3 candidates
                    break

        # Build clean report
        header = ("🔬 **غريس أشكروفت — التعرف على الهوية**\n━━━━━━━━━━━━━━━━━━━━━\n" if is_ar else "🔬 **Grace Ashcroft — Face Identification**\n━━━━━━━━━━━━━━━━━━━━━\n")

        if final_name:
            report = header
            report += f"\n👤 {'**الاسم:**' if is_ar else '**Name:**'} `{final_name}`\n"
            if final_bio:
                report += f"\n📋 {'**السيرة:**' if is_ar else '**Bio:**'} {final_bio}\n"
            if len(yd["tags"]) > 1:
                report += f"\n🏷️ {'**كلمات مفتاحية:**' if is_ar else '**Keywords:**'} {', '.join(yd['tags'][1:5])}\n"
        else:
            report = header + "\n❌ " + ("**لم أتمكن من التعرف على الشخص.**\n_جرب صورة أوضح للوجه._" if is_ar else "**Could not identify this person.**\n_Try a clearer face photo._")

        from urllib.parse import quote
        enc = quote(public_url, safe="")
        kbd = InlineKeyboardMarkup([[InlineKeyboardButton(("🔍 بحث يدوي Yandex" if is_ar else "🔍 Manual Yandex Search"), url=f"https://yandex.com/images/search?rpt=imageview&url={enc}")]])

        report += "\n━━━━━━━━━━━━━━━━━━━━━\n_" + ("تم إنهاء تحليل الهوية." if is_ar else "Identity analysis complete.") + "_ 📋"
        await status.edit_text(report, parse_mode="Markdown", reply_markup=kbd, disable_web_page_preview=True)

        # Send similar images (Targeting 2 distinct photos)
        if yd["similar_images"]:
            try:
                from telegram import InputMediaPhoto
                media = []
                cap_name = final_name if final_name else ("الشخص" if is_ar else "the person")
                caption = "🔬 " + (f"صور أخرى لـ {cap_name} 📋" if is_ar else f"Other photos of {cap_name} 📋")
                
                for i, img_url in enumerate(yd["similar_images"][:2]):
                    m_cap = caption if i == 0 else ""
                    media.append(InputMediaPhoto(media=img_url, caption=m_cap))
                
                if media:
                    await update.message.reply_media_group(media=media)
            except Exception as e:
                logger.warning(f"Failed to send media group: {e}")
                # Fallback: send individually if group fails
                try:
                    for img_url in yd["similar_images"][:2]:
                        await update.message.reply_photo(photo=img_url)
                except: pass

        logger.info(f"✅ /gsource: name='{yd['name']}' | URL: {public_url}")
    except Exception as e:
        logger.error(f"❌ Source Error: {e}", exc_info=True)
        try:
            await status.edit_text("💥 " + ("**خطأ في تحليل الهوية.** _تم تسجيل الخطأ._ 📋" if is_ar else "**Identity analysis fault.** _Error logged._ 📋"))
        except: pass




# --- AI CONVERSATION ENGINE (Groq) ---

async def ask_groq(prompt: str, user_name: str = "User", chat_history: list = None):
    if not GROQ_API_KEY:
        return None
        
    # Get current time in Beirut/Saudi timezone for context
    now = datetime.now(TIMEZONE)
    current_time_str = now.strftime("%I:%M %p")
    current_date_str = now.strftime("%Y-%m-%d")

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    # System Prompt: Grace Ashcroft (Arabic-Only Persona)
    system_instruction = (
        f"التاريخ: {current_date_str}. الوقت الحالي: {current_time_str}. "
        "أنتِ غريس أشكروفت، محللة فنية في الـ FBI. "
        "تحدثي فقط باللهجة السعودية البيضاء والعفوية. "
        "القواعد الصارمة: "
        "1. ممنوع منعاً باتاً استخدام أي حرف غير عربي (لا إنجليزي ولا صيني ولا غيره). "
        "2. ممنوع استخدام اللغة العربية الفصحى (لا تقولي ماذا، لماذا، تريد). "
        "3. ممنوع تكرار الجمل الترحيبية في كل رسالة. ادخلي في الموضوع فوراً. "
        "4. لا تعطي نصائح لغوية للمستخدم ولا تصححي له كلامه. "
        "5. كوني اجتماعية، عفوية، وقصيرة في ردودك (جملة أو جملتين). "
        f"أنتِ تتحدثين مع {user_name}."
    )
    
    messages = [{"role": "system", "content": system_instruction}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1500,
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Use the configured proxy if available to bypass regional blocks (e.g. 403 Forbidden)
        proxy_url = GRACE_PROXY if GRACE_PROXY and GRACE_PROXY.strip() else None
        async with _httpx.AsyncClient(timeout=30.0, proxy=proxy_url, trust_env=False) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if 'choices' in data and data['choices']:
                return data['choices'][0]['message']['content'].strip()
            return None
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return None


# --- IDENTITY / REPLY HANDLER (Grace Ashcroft Persona) ---

_umbrella_answers = LimitedDict(max_limit=1000) # Prevents memory leaks from interrogations

async def reply_who_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
        
        # Ignore messages from the bot itself
        if update.message.from_user.id == context.bot.id:
            return

        chat_id = update.effective_chat.id
        user = update.effective_user
        name = user.first_name or "User"

        # Umbrella Roulette GAME STATE INTERCEPT
        if user.id in _umbrella_game_state and _umbrella_game_state[user.id].get("chat_id") == chat_id:
            # Active player answering!
            state = _umbrella_game_state[user.id]
            q_idx = state.get("q_idx", -1)
            # Text based questions are anything except 9 and 10
            if q_idx not in [9, 10] and q_idx > 0:
                original_msg_id = state.get("msg_id")
                _umbrella_game_state.pop(user.id, None)
                
                if original_msg_id:
                    async def clean_roulette_msg(c_id, m_id, user_m_id):
                        await asyncio.sleep(9)
                        try:
                            await context.bot.delete_message(chat_id=c_id, message_id=m_id)
                        except Exception:
                            pass
                        try:
                            await context.bot.delete_message(chat_id=c_id, message_id=user_m_id)
                        except Exception:
                            pass
                    safe_create_task(clean_roulette_msg(chat_id, original_msg_id, update.message.message_id), name="clean_roulette_msg")
                group_settings = get_group_settings(chat_id)
                lang = group_settings.get("dialect", DEFAULT_DIALECT)
                
                raw_text = update.message.text
                time_taken = round(_time.time() - state.get("start_time", _time.time()), 1)
                question = get_phrase(chat_id, f"umbrella_fact_q{q_idx}")
                
                custom_reaction = ""
                if q_idx == 5:
                    raw_text_lower = raw_text.lower()
                    arabic_yes = ["نعم", "اي", "ايه", "يس"]
                    if "yes" in raw_text_lower or any(y in raw_text_lower for y in arabic_yes):
                        custom_reaction = f"\n\n**Grace:** _{get_phrase(chat_id, 'umbrella_react_q5_yes')}_"
                    else:
                        custom_reaction = f"\n\n**Grace:** _{get_phrase(chat_id, 'umbrella_react_q5_no')}_"
                
                import uuid
                from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                
                ans_id = uuid.uuid4().hex[:8]
                _umbrella_answers[ans_id] = raw_text
                
                kbd = InlineKeyboardMarkup([[InlineKeyboardButton("👁️ عرض الإجابة" if lang == "arabic_fousha" else "👁️ Reveal Answer", callback_data=f"ub_rev_{ans_id}")]])
                
                if lang == "arabic_fousha":
                     reply_msg = (
                         f"📋 **سجل التحقيق النفسي**\n"
                         f"━━━━━━━━━━━━━━━━━━━━━\n"
                         f"👤 **الهدف:** `{name}`\n"
                         f"⏱️ **زمن الاستجابة:** `{time_taken}s`\n\n"
                         f"**السؤال المطروح:**\n"
                         f"❓ _{question}_\n\n"
                         f"**البيانات المستردة:**\n"
                         f"🔒 `[ السجل محمي بشفرة أمنية ]`\n\n"
                         f"_تم حفظ الإجابة في قاعدة البيانات. صلاحية الوصول تقتصر على الموظفين المصرح لهم._ {custom_reaction}"
                     )
                else:
                     reply_msg = (
                         f"📋 **PSYCHOLOGICAL INTERROGATION LOG**\n"
                         f"━━━━━━━━━━━━━━━━━━━━━\n"
                         f"👤 **Subject:** `{name}`\n"
                         f"⏱️ **Response Time:** `{time_taken}s`\n\n"
                         f"**Interrogation Query:**\n"
                         f"❓ _{question}_\n\n"
                         f"**Recovered Data:**\n"
                         f"🔒 `[ RECORD REDACTED - ENCRYPTED FILE ]`\n\n"
                         f"_Data logged to internal servers. Access restricted to authorized personnel._ {custom_reaction}"
                     )
                
                try:
                    final_post = await update.message.reply_text(reply_msg, reply_markup=kbd, parse_mode="Markdown")
                except Exception:
                    # Fallback if message deleted
                    final_post = await context.bot.send_message(chat_id=chat_id, text=reply_msg, reply_markup=kbd, parse_mode="Markdown")
                     
                # Cleanup the interrogation log and free memory after 30 minutes
                async def clean_interrogation_log(c_id, m_id, a_id):
                    await asyncio.sleep(1800)
                    try:
                        await context.bot.delete_message(chat_id=c_id, message_id=m_id)
                        _umbrella_answers.pop(a_id, None)
                    except Exception:
                        pass
                
                safe_create_task(clean_interrogation_log(chat_id, final_post.message_id, ans_id), name="clean_interrogation_log")
                update_umbrella_stats(chat_id, user.id, "survived", inc_streak=True)
                return # Stop processing text
            return # Even if it's button question, we ignore text


        text = update.message.text.lower()
        bot_usr = context.bot.username.lower() if context.bot.username else ""

        # Identity Triggers
        identity_triggers = [
            "غريس عرفي عن نفسك", "g عرفي عن نفسك",
            "g introduce yourself", "grace introduce yourself",
            "g who are you", "grace who are you", "who are you"
        ]
        mention_triggers  = ["g", "G", "غ", "غريس", "gigi", "جيجي"]

        is_identity = any(t in text for t in identity_triggers)
        is_mention  = any(
            (_re.search(r'(?i)\b' + _re.escape(t) + r'\b', update.message.text) if len(t) <= 2 else t in text)
            for t in mention_triggers
        )
        is_tag      = f"@{bot_usr}" in text
        
        # Reply detection
        is_reply_to_bot = False
        if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

        if is_tag or is_identity or is_mention or is_reply_to_bot:
            # 2. Conversational Logic (Mentions/Replies)
            # Global Lock Check for AI
            if reason_ai := get_lock_reason("ggai"):
                # Only respond to mentions if AI is locked, to explain why she's silent
                is_mention = (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id) or (f"@{context.bot.username}" in update.message.text)
                if is_mention:
                    await update.message.reply_text(get_phrase(chat_id, "lock_denied_ggai_chat", reason=reason_ai), parse_mode="Markdown")
                return

            gs = get_group_settings(chat_id)
            if gs.get("ai_enabled", False):
                # Show "typing..." status while AI thinks
                try: await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                except: pass

                # Get Chat History
                history = message_history.get(chat_id, [])
                
                # Try AI response first (Gemini 2.5 Flash Engine)
                ai_reply = await ask_gemini(update.message.text, name, chat_history=history)
                
                if ai_reply:
                    msg = ai_reply
                    # Update History
                    history.append({"role": "user", "content": update.message.text})
                    history.append({"role": "assistant", "content": ai_reply})
                    # Keep only last 5 exchanges (10 messages)
                    message_history[chat_id] = history[-10:]
                else:
                    # Fallback to standard persona phrases if AI fails or is disabled
                    if is_mention and not is_identity:
                        msg = random.choice([
                            get_phrase(chat_id, "mention_1"),
                            get_phrase(chat_id, "mention_2"),
                            get_phrase(chat_id, "mention_3"),
                        ])
                    else:
                        msg = random.choice([
                            get_phrase(chat_id, "identity_1"),
                            get_phrase(chat_id, "identity_2"),
                        ])
                # Send with identity video if available
                async def safe_reply(text_content):
                    try:
                        if is_mention and not is_identity:
                            await update.message.reply_text(text_content)
                        else:
                            video_path = "identity.gif.mp4"
                            if os.path.exists(video_path):
                                try:
                                    with open(video_path, 'rb') as video_file:
                                        await update.message.reply_video(
                                            video=video_file,
                                            caption=text_content,
                                            supports_streaming=True
                                        )
                                except Exception:
                                    await update.message.reply_text(text_content)
                            else:
                                await update.message.reply_text(text_content)
                    except Exception:
                        await context.bot.send_message(chat_id=chat_id, text=text_content)

                await safe_reply(msg)
                return
            else:
                # If AI is disabled, only respond if specifically mentioned (standard phrases)
                if is_mention and not is_identity:
                    phrase = get_phrase(chat_id, f"mention_{random.randint(1, 3)}")
                    await update.message.reply_text(phrase)
                elif is_identity:
                    phrase = get_phrase(chat_id, f"identity_{random.randint(1, 2)}")
                    await update.message.reply_text(phrase)
                return

        # Greeting / Social Opener Intent
        match_salam = _re.match(r'^(سلام عليكم|سلام|السلام عليكم)[\s\!\؟\.\،]*$', text)
        match_hala = _re.match(r'^(اهلا|هلا ولله|هلا|مرحبا|مرحباً|أهلين|اهلين|هاي)[\s\!\؟\.\،]*$', text)
        match_sabah = _re.match(r'^(صباح الخير|صباح النور|صباحو|يسعدلي صباحك|صباح الورد)[\s\!\؟\.\،]*$', text)
        match_masa = _re.match(r'^(مساء الخير|مساء النور|مسا الخير|مسا النور)[\s\!\؟\.\،]*$', text)
        match_kifak = _re.match(r'^(كيفك|شلونك|وش اخبارك|كيف الحال|كيف حالك)[\s\!\؟\.\،]*$', text)
        
        reply_pool = None
        
        if match_salam:
            reply_pool = [
                "وعليكم السلام... وش عندك؟",
                "وعليكم السلام ورحمة الله.",
                "وعليكم السلام ورحمة الله وبركاته.",
                "وعليكم السلام... الليلة هادية، وهذا غالبًا مو شيء يطمن.",
                "وعليكم السلام... أنا هنا. الأمور مستتبة للحين."
            ]
        elif match_hala:
            reply_pool = [
                "هلا... أسمعك. الوضع مستتب حالياً، بس خلك منتبه.",
                "هلا... من صوتك، فيه شيء شاغلك.",
                "مرحباً... كنت أراجع بعض السجلات. صاير شيء؟",
                "أهلاً... الشاشات عندي ما فيها حركة للحين. وش صاير عندك؟",
                "هلا بك."
            ]
        elif match_sabah:
            reply_pool = [
                "صباح النور.",
                "صباح الخير... صاحي بدري، واضح إن عندك شيء.",
                "صباح النور، وش وراك؟",
                "صباح الخير... السيرفرات هادية هالوقت."
            ]
        elif match_masa:
            reply_pool = [
                "مساء النور.",
                "مساء الخير... للحين صاحي؟ عادة هالوقت ما يجي بخير.",
                "مساء النور، وش عندك؟",
                "مساء الخير... المراقبة مستمرة، مافيه شيء جديد."
            ]
        elif match_kifak:
            reply_pool = [
                "بخير... بس الوضع حولي يخلي الواحد متأهب. وأنت؟",
                "الحمدلله. أراقب التحديثات الأخيرة. وش صاير معك؟",
                "بخير... الشغل ما يوقف. عندك بلاغ؟"
            ]
            
        if reply_pool:
            try: await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            except: pass
            await asyncio.sleep(1.2)
            
            await update.message.reply_text(random.choice(reply_pool))
            return

        # Boredom triggers
        boredom_triggers = ["bored", "boring", "nothing to do", "ملل", "زهق"]
        if any(t in text for t in boredom_triggers):
            msg = random.choice([
                get_phrase(chat_id, "bored_1"),
                get_phrase(chat_id, "bored_2"),
                get_phrase(chat_id, "bored_3"),
            ])
            await update.message.reply_text(msg)
            return

        # Photo triggers
        img_triggers = ["show me your photo", "warine soura", "send photo", "grace photo", "grace pic"]
        if any(t in text for t in img_triggers):
            try:
                jpg_path = "grace.jpg"
                gif_path = "grace.gif"
                if os.path.exists(gif_path):
                    with open(gif_path, 'rb') as f:
                        await update.message.reply_animation(
                            animation=f,
                            caption="...You asked. Here. 📋"
                        )
                elif os.path.exists(jpg_path):
                    with open(jpg_path, 'rb') as f:
                        await update.message.reply_photo(
                            photo=f,
                            caption="...Here. Don't make it weird. 📋"
                        )
                else:
                    await update.message.reply_text("I... don't have an image file set up. (grace.jpg missing)")
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
            return

    except Exception as e:
        logger.error(f"Error in reply_who handler: {e}")

# ─────────────────────────────────────────────
# /gstart — Interactive Guide with Buttons
# ─────────────────────────────────────────────

def _guide_main_keyboard(chat_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_phrase(chat_id, "btn_members"), callback_data="guide_members"),
         InlineKeyboardButton(get_phrase(chat_id, "btn_admins"),  callback_data="guide_admins")],
        [InlineKeyboardButton(get_phrase(chat_id, "btn_about"),   callback_data="guide_about")],
    ])

def _guide_back_keyboard(chat_id):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_phrase(chat_id, "btn_back"), callback_data="guide_main")]])

async def cmd_gcmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hidden command for @n0amtell to list all commands and triggers without emojis."""
    user = update.effective_user
    if not user or user.username != "n0amtell":
        return

    report = (
        "Grace Ashcroft - Full Command List\n"
        "------------------------------------\n"
        "\n"
        "[ General & Status ]\n"
        "  /start | /gstart | /gmenu - Start bot or open menu\n"
        "  /gabout - About information\n"
        "  /gstatus - Bot status\n"
        "  /ghelp - Help menu\n"
        "  /grules - View group rules\n"
        "  /ginfo - Get user or group info\n"
        "  /getid - Get chat or user ID\n"
        "  /gstats - Get group stats\n"
        "\n"
        "[ Group Settings & Moderation ]\n"
        "  /gsetwlc - Set welcome message\n"
        "  /gsetfrw - Set farewell message\n"
        "  /gsetrules - Set group rules\n"
        "  /gsetwarn - Set warning action\n"
        "  /gsetmute - Set mute action\n"
        "  /gsetkick - Set kick action\n"
        "  /gsetban - Set ban action\n"
        "  /glang - Set language or dialect\n"
        "  /gsetlog - Set logging channel\n"
        "\n"
        "[ Filters & Anti-Spam ]\n"
        "  /glinkfilter - Toggle link filter\n"
        "  /gspamfilter - Toggle spam filter\n"
        "  /grepeatfilter - Toggle repeat message filter\n"
        "  /gcaptcha - Toggle CAPTCHA for new members\n"
        "  /gantibot - Toggle anti-bot protection\n"
        "  /gtoggleapply - Toggle group application system\n"
        "  /gcleanservice - Clean service messages\n"
        "\n"
        "[ Admin Actions ]\n"
        "  /gpromote - Promote a user\n"
        "  /gdemote - Demote an admin\n"
        "  /gwarn - Warn a user\n"
        "  /gmute - Mute a user\n"
        "  /gkick - Kick a user\n"
        "  /gban - Ban a user\n"
        "  /glock - Lock a command or feature\n"
        "  /gunlock - Unlock a command or feature\n"
        "  /gcleardata - Clear group data\n"
        "  /gclearchat - Clear chat history\n"
        "  /gnotifyall - Notify all members\n"
        "  /gedit - Edit bot messages\n"
        "\n"
        "[ Features & Mini-Games ]\n"
        "  /ggai - Toggle AI interactions\n"
        "  /gapply - Apply to join the group\n"
        "  /gumbrella | /a - Play the Umbrella (Roulette) game\n"
        "  /gmusic - Music playback controls\n"
        "  /gsource - Face identification or person recognition\n"
        "  /gin - Toggle 'in' state\n"
        "  /gout - Toggle 'out' state\n"
        "  /gsum - Generate chat summary\n"
        "  /gana - Analyze chat or user\n"
        "\n"
        "[ News & Content ]\n"
        "  /gnews - General news\n"
        "  /ggame - Gaming news\n"
        "  /gmcu - MCU (Marvel) news\n"
        "  /gtech - Tech news\n"
        "  /gnewsctl - News control\n"
        "  /gnewssrc - News sources management\n"
        "  /gforcesync - Force sync news data\n"
        "\n"
        "------------------------------------\n"
        "Keyword Triggers (Regex)\n"
        "------------------------------------\n"
        "[ Umbrella / Roulette ]\n"
        "  Play: امبريلا | أمبريلا | روليت | مظله | مظلة | ا | umbrella | roulette | a\n"
        "  Help: شرح الروليت | قوانين الروليت | غريس اشرحي اللعبه | غريس اشرحي اللعبة | how to play roulette | roulette rules\n"
        "\n"
        "[ General News ]\n"
        "  Prefixes: g | G | غريس | جيجي\n"
        "  Suffixes: عطني اخر المستجدات | عطيني اخر المستجدات | عطني | عطيني\n"
        "  Exact: تقرير اليوم يا غريس | تقرير اليوم يا g | تقرير اليوم يا جيجي | تقرير اليوم | زودني\n"
        "\n"
        "[ Gaming News ]\n"
        "  Prefixes +: عطني اخر المستجدات عن الالعاب | عطيني اخر المستجدات عن الالعاب\n"
        "  Exact: تقرير الالعاب يا غريس | تقرير الالعاب يا g | تقرير الالعاب يا جيجي | تقرير الالعاب | تقرير الألعاب\n"
        "\n"
        "[ MCU News ]\n"
        "  Prefixes +: عطني اخر المستجدات عن مارفل | عطيني اخر المستجدات عن مارفل\n"
        "  Exact: تقرير مارفل يا غريس | تقرير مارفل يا g | تقرير مارفل يا جيجي | تقرير مارفل\n"
        "\n"
        "[ Tech News ]\n"
        "  Prefixes +: عطني اخر المستجدات عن التقنية | عطيني اخر المستجدات عن التقنية\n"
        "  Exact: تقرير التقنية يا غريس | تقرير التقنية يا g | تقرير التقنية يا جيجي | تقرير التقنية"
    )
    
    await update.message.reply_text(report, disable_web_page_preview=True)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Interactive Guide entry point (/start, /gstart, /gmenu)."""
    try:
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        text_raw = update.message.text or ""
        command = text_raw.split()[0].lower().replace("@" + context.bot.username.lower(), "")

        # If /start is used in a group, we remain silent to avoid clutter.
        # This ensures /start only acts as the 'gmenu' entry point in private chats.
        if command == "/start" and chat_type != "private":
            return

        await update.message.reply_text(
            get_phrase(chat_id, "guide_main"), 
            parse_mode="Markdown", 
            reply_markup=_guide_main_keyboard(chat_id)
        )
    except Exception as e:
        logger.error(f"Error in start/menu handler: {e}")

async def guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query: return
    await query.answer()
    chat_id = update.effective_chat.id
    try:
        if query.data == "guide_main":
            await query.edit_message_text(
                get_phrase(chat_id, "guide_main"), 
                parse_mode="Markdown", 
                reply_markup=_guide_main_keyboard(chat_id)
            )
        elif query.data in ["guide_members", "guide_admins", "guide_about"]:
            await query.edit_message_text(
                get_phrase(chat_id, query.data), 
                parse_mode="Markdown", 
                reply_markup=_guide_back_keyboard(chat_id)
            )
    except Exception as e:
        logger.error(f"Error in guide_callback: {e}")

# --- SYSTEM METRICS & STATS HELPERS ---

def get_bot_uptime() -> str:
    now = datetime.now(TIMEZONE)
    delta = now - BOT_START_TIME
    days, remainder = divmod(int(delta.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours:02d}h")
    parts.append(f"{minutes:02d}m")
    parts.append(f"{seconds:02d}s")
    return " ".join(parts)

def get_system_metrics():
    try:
        cpu_pct = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        ram_used_gb = vm.used / (1024 ** 3)
        ram_total_gb = vm.total / (1024 ** 3)
        ram_pct = vm.percent
        proc = psutil.Process()
        proc_ram_mb = proc.memory_info().rss / (1024 ** 2)
    except Exception as e:
        logger.warning(f"Error fetching system metrics: {e}")
        cpu_pct = 0.0
        ram_used_gb = 0.0
        ram_total_gb = 0.0
        ram_pct = 0.0
        proc_ram_mb = 0.0

    def make_bar(pct, length=8):
        filled = int(round(length * max(0, min(100, pct)) / 100))
        return '■' * filled + '□' * (length - filled)

    return {
        "cpu_pct": cpu_pct,
        "cpu_bar": make_bar(cpu_pct),
        "ram_used_gb": f"{ram_used_gb:.1f}",
        "ram_total_gb": f"{ram_total_gb:.1f}",
        "ram_pct": f"{ram_pct:.1f}",
        "ram_bar": make_bar(ram_pct),
        "proc_ram_mb": f"{proc_ram_mb:.1f}",
        "python_ver": sys.version.split()[0],
        "os_sys": sys.platform.title()
    }

async def build_status_message(chat_id: int):
    group_settings = get_group_settings(chat_id)
    dialect = group_settings.get("dialect", DEFAULT_DIALECT)
    is_ar = (dialect == "arabic_fousha")

    uptime_str = get_bot_uptime()
    metrics = get_system_metrics()
    current_time = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")

    # Subsystem status check
    music_ok = os.path.exists(FFMPEG_PATH) and (os.path.exists(YT_DLP_PATH) or shutil.which("yt-dlp"))
    ai_ok = bool(GROQ_API_KEY)
    
    if is_ar:
        music_status = "نشط 🟢" if music_ok else "محدود (FFmpeg مفقود) ⚠️"
        news_status = "نشط (٤ مصادر) 📡"
        ai_status = "جاهز ⚡" if ai_ok else "غير مفعل (مفتاح API) ❌"
        
        status_text = (
            "📋 **غريس أشكروفت — تقرير حالة النظام والتشغيل**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🟢 **الحالة التشغيلية:** `أونلاين (DeepScope v1.5)`\n"
            f"⏱️ **مدة التشغيل:** `{uptime_str}`\n"
            f"🖥️ **نظام المضيف:** `{metrics['os_sys']}` · `Python {metrics['python_ver']}`\n\n"
            "📊 **قياسات أداء الجهاز:**\n"
            f"▸ **استهلاك المعالج (CPU):** `[{metrics['cpu_bar']}] {metrics['cpu_pct']:.1f}%`\n"
            f"▸ **الذاكرة العشوائية (RAM):** `[{metrics['ram_bar']}] {metrics['ram_used_gb']}GB / {metrics['ram_total_gb']}GB ({metrics['ram_pct']}%)`\n"
            f"▸ **ذاكرة البوت (RSS):** `{metrics['proc_ram_mb']} MB`\n\n"
            "**تشخيص الأنظمة الفرعية:**\n"
            f"▸ 🎵 **محرك الصوتيات (Music Engine):** {music_status}\n"
            f"▸ 🌐 **تغذية DeepScope:** {news_status}\n"
            f"▸ 🤖 **منطق الذكاء الاصطناعي (Groq):** {ai_status}\n"
            "▸ 💾 **قاعدة البيانات:** متصلة 🟢\n"
            "▸ 🛡️ **مصفوفة الحماية:** نشطة 🟢\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "_جميع الأنظمة تعمل ضمن الحدود المعيارية والطبيعية._\n"
            f"🕐 `{current_time}`"
        )
        refresh_btn = "🔄 تحديث الحالة"
        intel_btn = "🔍 معلومات النظام"
    else:
        music_status = "ONLINE 🟢" if music_ok else "LIMITED (FFmpeg Missing) ⚠️"
        news_status = "ACTIVE (4 Feeds) 🌐"
        ai_status = "ONLINE ⚡" if ai_ok else "DISABLED (API Key) ❌"

        status_text = (
            "📋 **Grace Ashcroft — System Status & Health Report**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🟢 **Operational State:** `ONLINE (DeepScope v1.5)`\n"
            f"⏱️ **System Uptime:** `{uptime_str}`\n"
            f"🖥️ **Host Architecture:** `{metrics['os_sys']}` · `Python {metrics['python_ver']}`\n\n"
            "📊 **Hardware Telemetry:**\n"
            f"▸ **CPU Load:** `[{metrics['cpu_bar']}] {metrics['cpu_pct']:.1f}%`\n"
            f"▸ **Host Memory:** `[{metrics['ram_bar']}] {metrics['ram_used_gb']}GB / {metrics['ram_total_gb']}GB ({metrics['ram_pct']}%)`\n"
            f"▸ **Process RSS:** `{metrics['proc_ram_mb']} MB`\n\n"
            "**Subsystem Diagnostics:**\n"
            f"▸ 🎵 **Music Node Engine:** {music_status}\n"
            f"▸ 🌐 **DeepScope Intelligence:** {news_status}\n"
            f"▸ 🤖 **Groq AI Logic:** {ai_status}\n"
            "▸ 💾 **Database Connectivity:** ONLINE 🟢\n"
            "▸ 🛡️ **Security Matrix:** ACTIVE 🟢\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "_All subsystems operating within defined parameters._\n"
            f"🕐 `{current_time}`"
        )
        refresh_btn = "🔄 Refresh Status"
        intel_btn = "🔍 System Intel"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(refresh_btn, callback_data="gstatus_refresh"),
            InlineKeyboardButton(intel_btn, callback_data="guide_about")
        ]
    ])
    return status_text, keyboard

async def build_stats_message(chat, chat_id: int, member_count: int, admins: list, group_settings: dict):
    dialect = group_settings.get("dialect", DEFAULT_DIALECT)
    is_ar = (dialect == "arabic_fousha")

    tracked_members = len(group_settings.get("members", []))
    track_ratio = (tracked_members / max(1, member_count)) * 100
    
    def make_bar(pct, length=8):
        filled = int(round(length * max(0, min(100, pct)) / 100))
        return '■' * filled + '□' * (length - filled)

    track_bar = make_bar(track_ratio)

    # Feature Toggles
    link_filter = group_settings.get("link_filter", False)
    spam_filter = group_settings.get("spam_filter", False)
    repeat_filter = group_settings.get("repeat_filter", False)
    captcha = group_settings.get("captcha", False)
    clean_service = group_settings.get("clean_service", False)
    ai_enabled = group_settings.get("ai_enabled", False)
    apply_enabled = group_settings.get("apply_enabled", True)
    has_rules = bool(group_settings.get("rules"))

    # Global Bot Telemetry
    all_settings = load_settings()
    all_groups = all_settings.get("groups", {})
    total_groups = len(all_groups)
    total_tracked_users = sum(len(g.get("members", [])) for g in all_groups.values() if isinstance(g, dict))

    current_time = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    chat_title = chat.title if (chat and chat.title) else ("Private User" if (chat and chat.type == "private") else f"Chat {chat_id}")
    dialect_display = DIALECT_NAMES.get(dialect, dialect)

    if is_ar:
        def format_status_ar(val):
            return "مفعّل 🟢" if val else "معطّل 🔴"

        stats_text = (
            "📊 **غريس أشكروفت — إحصائيات وبينات المجموعة**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 **المجموعة المستهدفة:** `{chat_title}`\n"
            f"🆔 **معرف الدردشة:** `{chat_id}`\n"
            f"💬 **اللهجة النشطة:** `{dialect_display}`\n\n"
            "👥 **الديموغرافيا والتتبع:**\n"
            f"▸ **إجمالي الأعضاء:** `{member_count}`\n"
            f"▸ **عدد المشرفين:** `{len(admins)}`\n"
            f"▸ **الأعضاء المتتبعين في DB:** `{tracked_members}`\n"
            f"▸ **نسبة التتبع النشط:** `[{track_bar}] {track_ratio:.1f}%`\n\n"
            "🛡️ **مصفوفة الحماية والخدمات:**\n"
            f"▸ 🔗 **فلتر الروابط:** {format_status_ar(link_filter)}\n"
            f"▸ 📝 **فلتر السبام:** {format_status_ar(spam_filter)}\n"
            f"▸ 🔄 **فلتر التكرار:** {format_status_ar(repeat_filter)}\n"
            f"▸ 🤖 **اختبار الكابوتشا:** {format_status_ar(captcha)}\n"
            f"▸ 🧹 **تنظيف رسائل الخدمة:** {format_status_ar(clean_service)}\n"
            f"▸ 🧠 **محادثة الذكاء الاصطناعي:** {format_status_ar(ai_enabled)}\n"
            f"▸ 📥 **نظام الانضمام (/gapply):** {format_status_ar(apply_enabled)}\n"
            f"▸ 📜 **قوانين المجموعة:** {'مسجلة 📋' if has_rules else 'غير محددة ⚠️'}\n\n"
            "🌐 **البيانات الإجمالية للبوت:**\n"
            f"▸ **إجمالي المجموعات المسجلة:** `{total_groups}`\n"
            f"▸ **إجمالي الأعضاء المسجلين:** `{total_tracked_users}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "_تم إجراء التحليل الجنائي المتقدم للبيانات._\n"
            f"🕐 `{current_time}`"
        )
        refresh_btn = "🔄 تحديث الإحصائيات"
        admins_btn = "👮 المشرفين"
    else:
        def format_status_en(val):
            return "Active 🟢" if val else "Disabled 🔴"

        stats_text = (
            "📊 **Grace Ashcroft — Group Intelligence & Data Metrics**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 **Target Group:** `{chat_title}`\n"
            f"🆔 **Chat ID:** `{chat_id}`\n"
            f"💬 **Active Dialect:** `{dialect_display}`\n\n"
            "👥 **Demographics & Activity:**\n"
            f"▸ **Total Members:** `{member_count}`\n"
            f"▸ **Administrators:** `{len(admins)}`\n"
            f"▸ **Tracked Active Users:** `{tracked_members}`\n"
            f"▸ **Tracking Coverage:** `[{track_bar}] {track_ratio:.1f}%`\n\n"
            "🛡️ **Protection & Feature Matrix:**\n"
            f"▸ 🔗 **Link Filter:** {format_status_en(link_filter)}\n"
            f"▸ 📝 **Spam Filter:** {format_status_en(spam_filter)}\n"
            f"▸ 🔄 **Repeat Filter:** {format_status_en(repeat_filter)}\n"
            f"▸ 🤖 **Captcha Verification:** {format_status_en(captcha)}\n"
            f"▸ 🧹 **Service Message Cleaner:** {format_status_en(clean_service)}\n"
            f"▸ 🧠 **AI Conversational Logic:** {format_status_en(ai_enabled)}\n"
            f"▸ 📥 **Membership Applications:** {format_status_en(apply_enabled)}\n"
            f"▸ 📜 **Group Rules:** {'Configured 📋' if has_rules else 'Not Set ⚠️'}\n\n"
            "🌐 **Global Telemetry:**\n"
            f"▸ **Total Managed Groups:** `{total_groups}`\n"
            f"▸ **Global Tracked Database Users:** `{total_tracked_users}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "_Forensic data analysis completed._\n"
            f"🕐 `{current_time}`"
        )
        refresh_btn = "🔄 Refresh Stats"
        admins_btn = "👮 View Admins"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(refresh_btn, callback_data="gstats_refresh"),
            InlineKeyboardButton(admins_btn, callback_data="guide_admins")
        ]
    ])
    return stats_text, keyboard

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        status_text, keyboard = await build_status_message(chat_id)
        await update.message.reply_text(status_text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in status: {e}")

async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(get_phrase(update.effective_chat.id, "about_msg"), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in about: {e}")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(get_phrase(update.effective_chat.id, "help_msg"), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in help: {e}")

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        rules = get_group_settings(chat_id).get("rules")
        if rules:
            await update.message.reply_text(f"{get_phrase(chat_id, 'rules_header')}\n\n{rules}")
        else:
            await update.message.reply_text(get_phrase(chat_id, "no_rules"))
    except Exception as e:
        logger.error(f"Error in rules: {e}")

async def cmd_setwlc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not context.args:
            await update.message.reply_text("Usage: /gsetwlc [message]\nExample: /gsetwlc Welcome {name} to {group}!"); return
        welcome_msg = update.message.text.split(maxsplit=1)[1]
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT}
        settings["groups"][chat_id]["welcome"] = welcome_msg
        save_settings(settings)
        await update.message.reply_text(get_phrase(update.effective_chat.id, "welcome_set"))
    except Exception as e:
        logger.error(f"Error in setwlc: {e}")

async def cmd_setfrw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not context.args:
            await update.message.reply_text("Usage: /gsetfrw [message]\nExample: /gsetfrw Goodbye {name}!"); return
        farewell_msg = update.message.text.split(maxsplit=1)[1]
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT}
        settings["groups"][chat_id]["farewell"] = farewell_msg
        save_settings(settings)
        await update.message.reply_text(get_phrase(update.effective_chat.id, "farewell_set"))
    except Exception as e:
        logger.error(f"Error in setfrw: {e}")

async def cmd_setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not context.args:
            await update.message.reply_text("Usage: /gsetrules [rules text]"); return
        rules_text = update.message.text.split(maxsplit=1)[1]
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT}
        settings["groups"][chat_id]["rules"] = rules_text
        save_settings(settings)
        await update.message.reply_text(get_phrase(update.effective_chat.id, "rules_set"))
    except Exception as e:
        logger.error(f"Error in setrules: {e}")

async def cmd_setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mission Intelligence Language Selector (/glang)."""
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        
        if not context.args:
            await update.message.reply_text(
                "🌐 **Language Configuration Protocol**\n━━━━━━━━━━━━━━━━━━━━━\n"
                "Usage: `/glang eng` (English) or `/glang ara` (Arabic)\n"
                "Current Mission Dialect: `" + settings.get("groups", {}).get(chat_id, {}).get("dialect", DEFAULT_DIALECT) + "`",
                parse_mode="Markdown"
            ); return
            
        lang = context.args[0].lower()
        if lang in ["eng", "english"]:
            target_dialect = "english"
        elif lang in ["ara", "arabic", "fousha"]:
            target_dialect = "arabic_fousha"
        else:
            await update.message.reply_text("❌ Protocol Error: Invalid language identifier. Use `eng` or `ara`."); return

        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": target_dialect}
        else:
            settings["groups"][chat_id]["dialect"] = target_dialect
        
        save_settings(settings)
        display_name = DIALECT_NAMES.get(target_dialect, target_dialect)
        await update.message.reply_text(get_phrase(update.effective_chat.id, "dialect_set", dialect=display_name))
    except Exception as e:
        logger.error(f"Error in setlang: {e}")

async def build_ai_control_message(chat_id: int):
    settings = load_settings()
    cid_str = str(chat_id)
    gs = get_group_settings(chat_id)
    ai_state = gs.get("ai_enabled", False)
    is_ar = gs.get("dialect", DEFAULT_DIALECT) == "arabic_fousha"
    
    history = message_history.get(chat_id, [])
    mem_count = len(history) // 2
    
    status_text = ("مـفـعـل ✅ (ONLINE)" if ai_state else "مـعـطـل ❌ (PAUSED)") if is_ar else ("ACTIVE ✅ (ONLINE)" if ai_state else "PAUSED ❌ (OFFLINE)")
    
    if is_ar:
        text = (
            "🤖 **لوحة تحكم الذكاء الاصطناعي — Grace AI Core**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 **الحالة التشغيلية:** `{status_text}`\n"
            f"🧠 **ذاكرة المحادثة النشطة:** `{mem_count} / 5 محادثات`\n"
            "⚡ **محرك المعالجة:** `DeepScope Neural Engine`\n"
            "🛡️ **تصفية النصوص:** `مفعلة تلقائياً (Arabic Whitelist)`\n\n"
            "_استخدم الأزرار أدناه للتحكم الفوري ببروتوكولات المحادثة._ 📋"
        )
        btn_toggle = "❌ تعطيل الذكاء" if ai_state else "✅ تفعيل الذكاء"
        btn_clear = "🧹 مسح الذاكرة"
        btn_status = "📊 قياسات المحرك"
        btn_refresh = "🔄 تحديث"
    else:
        text = (
            "🤖 **GRACE AI NEURAL CONTROL PANEL**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 **Operational Status:** `{status_text}`\n"
            f"🧠 **Active Context Memory:** `{mem_count} / 5 Exchanges`\n"
            "⚡ **Processing Neural Engine:** `DeepScope Neural Engine`\n"
            "🛡️ **Security Sanitation:** `Active (Sanitized Output)`\n\n"
            "_Use the controls below to configure real-time persona logic._ 📋"
        )
        btn_toggle = "❌ Disable AI" if ai_state else "✅ Enable AI"
        btn_clear = "🧹 Clear Memory"
        btn_status = "📊 Telemetry"
        btn_refresh = "🔄 Refresh"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(btn_toggle, callback_data="ggai_toggle"),
            InlineKeyboardButton(btn_clear, callback_data="ggai_clear")
        ],
        [
            InlineKeyboardButton(btn_status, callback_data="ggai_status"),
            InlineKeyboardButton(btn_refresh, callback_data="ggai_refresh")
        ]
    ])
    return text, keyboard

async def cmd_toggle_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if reason := get_lock_reason("ggai"):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "lock_denied_ggai", reason=reason), parse_mode="Markdown")
            return

        if not await is_admin(update, context):
            await update.message.reply_text("❌ Admin-only command."); return
            
        chat_id = update.effective_chat.id
        
        if context.args:
            sub = context.args[0].lower()
            if sub in ["clear", "reset", "مسح", "تصفير"]:
                message_history[chat_id] = []
                await update.message.reply_text("🧹 **تم مسح ذاكرة محادثات غريس للدردشة الحالية.**", parse_mode="Markdown")
                return
            elif sub in ["status", "info", "حالة", "تقرير"]:
                text, keyboard = await build_ai_control_message(chat_id)
                await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
                return

        settings = load_settings()
        chat_id_str = str(chat_id)
        if chat_id_str not in settings["groups"]:
            get_group_settings(chat_id)
            settings = load_settings()
            
        current = settings["groups"][chat_id_str].get("ai_enabled", False)
        settings["groups"][chat_id_str]["ai_enabled"] = not current
        save_settings(settings)
        
        text, keyboard = await build_ai_control_message(chat_id)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in toggle_ai: {e}")

async def ggai_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data.startswith("ggai_"): return
    
    chat_id = query.message.chat_id
    if not await is_admin(update, context):
        await query.answer("❌ This action requires admin permissions.", show_alert=True)
        return
        
    action = query.data.split("_")[1]
    
    if action == "toggle":
        settings = load_settings()
        cid_str = str(chat_id)
        current = settings.get("groups", {}).get(cid_str, {}).get("ai_enabled", False)
        if cid_str not in settings.get("groups", {}):
            settings["groups"][cid_str] = {}
        settings["groups"][cid_str]["ai_enabled"] = not current
        save_settings(settings)
        
        text, kbd = await build_ai_control_message(chat_id)
        try: await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kbd)
        except Exception: pass
        await query.answer("🤖 Grace AI Mode Toggled!")
        
    elif action == "clear":
        message_history[chat_id] = []
        text, kbd = await build_ai_control_message(chat_id)
        try: await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kbd)
        except Exception: pass
        await query.answer("🧹 AI Conversational Memory Cleared!", show_alert=True)
        
    elif action == "status":
        await query.answer("⚡ Engine: DeepScope Multi-Key Neural Pipeline 🟢", show_alert=True)
        
    elif action == "refresh":
        text, kbd = await build_ai_control_message(chat_id)
        try: await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kbd)
        except Exception: pass
        await query.answer("🔄 Control Panel Refreshed!")

async def cmd_linkfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "link_filter": False}
        current = settings["groups"][chat_id].get("link_filter", False)
        settings["groups"][chat_id]["link_filter"] = not current
        save_settings(settings)
        status = "✅ Active — links will be auto-removed." if not current else "❌ Inactive — links are permitted."
        await update.message.reply_text(f"🔗 Link filter: {status}")
    except Exception as e:
        logger.error(f"Error in linkfilter: {e}")

async def cmd_spamfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "spam_filter": False, "max_chars": 500}
        if context.args:
            try:
                max_chars = int(context.args[0])
                settings["groups"][chat_id]["max_chars"] = max_chars
                save_settings(settings)
                await update.message.reply_text(f"📏 Character limit updated: {max_chars} chars."); return
            except ValueError: pass
        current = settings["groups"][chat_id].get("spam_filter", False)
        settings["groups"][chat_id]["spam_filter"] = not current
        max_chars = settings["groups"][chat_id].get("max_chars", 500)
        save_settings(settings)
        if not current:
            await update.message.reply_text(f"📰 Long message filter: ✅ Active\nMax: {max_chars} chars\nUse /gspamfilter [number] to change.")
        else:
            await update.message.reply_text("📰 Long message filter: ❌ Inactive")
    except Exception as e:
        logger.error(f"Error in spamfilter: {e}")

async def cmd_repeatfilter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "repeat_filter": False}
        current = settings["groups"][chat_id].get("repeat_filter", False)
        settings["groups"][chat_id]["repeat_filter"] = not current
        save_settings(settings)
        status = "✅ Active — duplicate messages (3+) will be removed." if not current else "❌ Inactive"
        await update.message.reply_text(f"🔄 Repeat filter: {status}")
    except Exception as e:
        logger.error(f"Error in repeatfilter: {e}")

async def cmd_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "captcha": False}
        current = settings["groups"][chat_id].get("captcha", False)
        settings["groups"][chat_id]["captcha"] = not current
        save_settings(settings)
        if not current:
            await update.message.reply_text("🤖 Math captcha: ✅ Active\n60 seconds to answer, or members are removed automatically.")
        else:
            await update.message.reply_text("🤖 Math captcha: ❌ Inactive")
    except Exception as e:
        logger.error(f"Error in captcha: {e}")

async def cmd_toggle_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "welcome_enabled": True}
        current = settings["groups"][chat_id].get("welcome_enabled", True)
        new_state = not current
        settings["groups"][chat_id]["welcome_enabled"] = new_state
        save_settings(settings)
        if new_state:
            await update.message.reply_text("✅ تم تفعيل بروتوكول الترحيب.. بنهلي باللي يجينا!")
        else:
            await update.message.reply_text("❌ تم إيقاف الترحيب.. بنخلي الوضع صامت.")
    except Exception as e:
        logger.error(f"Error in toggle_in: {e}")

async def cmd_toggle_out(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "farewell_enabled": True}
        current = settings["groups"][chat_id].get("farewell_enabled", True)
        new_state = not current
        settings["groups"][chat_id]["farewell_enabled"] = new_state
        save_settings(settings)
        if new_state:
            await update.message.reply_text("✅ تم تفعيل بروتوكول التوديع.. الله يحفظ اللي يغادرنا.")
        else:
            await update.message.reply_text("❌ تم إيقاف التوديع.. ما نبي نودع أحد.")
    except Exception as e:
        logger.error(f"Error in toggle_out: {e}")

async def cmd_toggleapply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "apply_required": False}
        current = settings["groups"][chat_id].get("apply_required", False)
        settings["groups"][chat_id]["apply_required"] = not current
        save_settings(settings)
        if not current:
            await update.message.reply_text("📝 Application form (/gapply): ✅ Active\nNew members must complete a form. Results sent to ownership.")
        else:
            await update.message.reply_text("📝 Application form: ❌ Inactive\nMembers can join freely.")
    except Exception as e:
        logger.error(f"Error in toggleapply: {e}")

# --- GLOBAL LOCKS (Master Only) ---

async def cmd_glock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Globally lock a command across all chats."""
    try:
        if update.effective_user.id != MASTER_ID and update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ Security Breach: Master key authorization required."); return
            
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: `/glock <cmd_name> <reason>`\nExample: `/glock gmusic Maintenance in progress`", parse_mode="Markdown"); return
            
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
        if update.effective_user.id != MASTER_ID and update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ Security Breach: Master key authorization required."); return
            
        if not context.args:
            await update.message.reply_text("Usage: `/gunlock <cmd_name>`", parse_mode="Markdown"); return
            
        cmd_to_unlock = context.args[0].lower().replace("/", "")
        
        settings = load_settings()
        if "global_locks" in settings and cmd_to_unlock in settings["global_locks"]:
            del settings["global_locks"][cmd_to_unlock]
            save_settings(settings)
            await update.message.reply_text(get_phrase(update.effective_chat.id, "lock_released", cmd=cmd_to_unlock), parse_mode="Markdown")
        else:
            await update.message.reply_text(f"ℹ️ Command `/{cmd_to_unlock}` is not currently locked.")
    except Exception as e:
        logger.error(f"Error in gunlock: {e}")

async def cmd_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_list = []
        for admin in admins:
            name = admin.user.first_name
            if admin.user.username:
                name = f"[{name}](https://t.me/{admin.user.username})"
            admin_list.append(f"{'👑' if admin.status == 'creator' else '⭐'} {name}")
        await update.message.reply_text(
            f"👥 **Group Administrators** ({len(admins)})\n━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(admin_list),
            parse_mode="Markdown", disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error in admins: {e}")

async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        # Global Lock Check
        if reason := get_lock_reason("ginfo"):
            await update.message.reply_text(get_phrase(chat_id, "lock_denied_ginfo", reason=reason), parse_mode="Markdown")
            return

        target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
        chat_id = str(update.effective_chat.id)
        user_id = str(target.id)
        settings = load_settings()
        warn_count = settings.get("warnings", {}).get(chat_id, {}).get(user_id, 0)
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, target.id)
            status_map = {"creator": "👑 Owner", "administrator": "⭐ Admin", "member": "👤 Member", "restricted": "🔇 Restricted", "left": "❌ Left", "kicked": "🚫 Banned"}
            status = status_map.get(member.status, "Unknown")
        except:
            status = "👤 Member"
        info_msg = (
            f"📋 **Member Report**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: {target.first_name}\n🆔 ID: `{target.id}`\n"
            f"📱 Username: {'@' + target.username if target.username else 'None'}\n"
            f"📊 Status: {status}\n⚠️ Warnings: {warn_count}/3\n"
        )
        if warn_count >= 2: info_msg += "\n⚡ **Note:** Approaching maximum warnings threshold."
        await update.message.reply_text(info_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in info: {e}")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        # Global Lock Check
        if reason := get_lock_reason("gstats"):
            await update.message.reply_text(get_phrase(chat_id, "lock_denied_gstats", reason=reason), parse_mode="Markdown")
            return

        chat = await context.bot.get_chat(chat_id)
        if chat.type == "private":
            member_count = 1
            admins = []
        else:
            try:
                member_count = await context.bot.get_chat_member_count(chat_id)
            except Exception:
                member_count = 1
            try:
                admins = await context.bot.get_chat_administrators(chat_id)
            except Exception:
                admins = []

        group_settings = get_group_settings(chat_id)
        stats_text, keyboard = await build_stats_message(chat, chat_id, member_count, admins, group_settings)
        await update.message.reply_text(stats_text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in stats: {e}")

async def cmd_setlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if LOG_CHANNEL:
            await update.message.reply_text(f"📢 **Log channel active**\n━━━━━━━━━━━━━━━━━━━━━\n🆔 ID: `{LOG_CHANNEL}`\n\nEdit .env to change.", parse_mode="Markdown")
        else:
            await update.message.reply_text("📢 **Log channel not configured**\n━━━━━━━━━━━━━━━━━━━━━\nAdd `LOG_CHANNEL=-100xxx` to .env and restart.", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in setlog: {e}")

async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to the target member's message."); return
        user = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        custom_title = " ".join(context.args) if context.args else ""
        await context.bot.promote_chat_member(chat_id=chat_id, user_id=user.id,
            can_delete_messages=True, can_restrict_members=True, can_pin_messages=True,
            can_promote_members=False, can_change_info=False, can_invite_users=True)
        if custom_title:
            try: await context.bot.set_chat_administrator_custom_title(chat_id=chat_id, user_id=user.id, custom_title=custom_title[:16])
            except Exception: pass
        await update.message.reply_text(
            f"⭐ **Member Promoted**\n━━━━━━━━━━━━━━━\n👤 {user.first_name}\n🎖️ Permissions: ✅ Delete, Restrict, Pin, Invite"
            + (f"\n📛 Title: {custom_title[:16]}" if custom_title else ""), parse_mode="Markdown")
        await log_event(context, "promote", update.effective_chat.title, update.effective_user.first_name, user.first_name)
    except Exception as e:
        logger.error(f"Error in promote: {e}")
        await update.message.reply_text(f"❌ Failed: {e}")

async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to the admin's message."); return
        user = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        member = await context.bot.get_chat_member(chat_id, user.id)
        if member.status == "creator":
            await update.message.reply_text("❌ Cannot demote the group owner."); return
        await context.bot.promote_chat_member(chat_id=chat_id, user_id=user.id, is_anonymous=False,
            can_manage_chat=False, can_delete_messages=False, can_manage_video_chats=False,
            can_restrict_members=False, can_promote_members=False, can_change_info=False,
            can_invite_users=False, can_pin_messages=False, can_post_messages=False,
            can_edit_messages=False, can_manage_topics=False)
        await update.message.reply_text(f"👤 **Admin Permissions Revoked**\n━━━━━━━━━━━━━━━\n👤 {user.first_name}\n📝 Returned to regular member.", parse_mode="Markdown")
        await log_event(context, "demote", update.effective_chat.title, update.effective_user.first_name, user.first_name)
    except Exception as e:
        logger.error(f"Error in demote: {e}")
        await update.message.reply_text(f"❌ Failed: {e}")

# --- CUSTOM MOD MESSAGES ---

async def cmd_setwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not context.args:
            await update.message.reply_text("Usage: /gsetwarn [message]\nVariables: {name}, {count}"); return
        custom_msg = update.message.text.split(maxsplit=1)[1]
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]: settings["groups"][chat_id] = {"dialect": DEFAULT_DIALECT}
        settings["groups"][chat_id]["warn_msg"] = custom_msg
        save_settings(settings)
        await update.message.reply_text("✅ Custom warn message updated.")
    except Exception as e: logger.error(f"Error in setwarn: {e}")

async def cmd_setmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not context.args:
            await update.message.reply_text("Usage: /gsetmute [message]\nVariables: {name}, {time}"); return
        custom_msg = update.message.text.split(maxsplit=1)[1]
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]: settings["groups"][chat_id] = {"dialect": DEFAULT_DIALECT}
        settings["groups"][chat_id]["mute_msg"] = custom_msg
        save_settings(settings)
        await update.message.reply_text("✅ Custom mute message updated.")
    except Exception as e: logger.error(f"Error in setmute: {e}")

async def cmd_setkick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not context.args:
            await update.message.reply_text("Usage: /gsetkick [message]\nVariables: {name}"); return
        custom_msg = update.message.text.split(maxsplit=1)[1]
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]: settings["groups"][chat_id] = {"dialect": DEFAULT_DIALECT}
        settings["groups"][chat_id]["kick_msg"] = custom_msg
        save_settings(settings)
        await update.message.reply_text("✅ Custom kick message updated.")
    except Exception as e: logger.error(f"Error in setkick: {e}")

async def cmd_setban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        if not context.args:
            await update.message.reply_text("Usage: /gsetban [message]\nVariables: {name}"); return
        custom_msg = update.message.text.split(maxsplit=1)[1]
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]: settings["groups"][chat_id] = {"dialect": DEFAULT_DIALECT}
        settings["groups"][chat_id]["ban_msg"] = custom_msg
        save_settings(settings)
        await update.message.reply_text("✅ Custom ban message updated.")
    except Exception as e: logger.error(f"Error in setban: {e}")

# --- WARN ---

async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text("❌ Admin-only command."); return
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to the target member's message to warn them."); return
        target = update.message.reply_to_message.from_user
        chat_id = str(update.effective_chat.id)
        user_id = str(target.id)
        reason = " ".join(context.args) if context.args else ""
        settings = load_settings()
        if "warnings" not in settings: settings["warnings"] = {}
        if chat_id not in settings["warnings"]: settings["warnings"][chat_id] = {}
        current = settings["warnings"][chat_id].get(user_id, 0) + 1
        settings["warnings"][chat_id][user_id] = current
        save_settings(settings)
        name = target.first_name or target.username or "User"
        if current >= 3:
            until = datetime.now(TIMEZONE) + timedelta(hours=8)
            try:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id, target.id,
                    permissions=ChatPermissions(can_send_messages=False), until_date=until
                )
            except Exception: pass
            settings["warnings"][chat_id][user_id] = 0
            save_settings(settings)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Lift Restriction (Lasso)", callback_data=f"unmute_{chat_id}_{target.id}")]])
            msg = (
                f"🔇 **Auto-Mute Triggered**\n━━━━━━━━━━━━━━━\n"
                f"👤 {name}\n⚠️ 3 warnings reached.\n"
                f"🔇 Restricted for 8 hours.\n"
                f"⏰ Ends: {until.strftime('%I:%M %p')}\n\n"
                f"_I... really didn't want it to come to this._"
            )
            if os.path.exists(MUTE_ANIMATION_PATH):
                with open(MUTE_ANIMATION_PATH, "rb") as f:
                    await update.message.reply_animation(animation=f, caption=msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            remaining = 3 - current
            custom_warn = settings.get("groups", {}).get(chat_id, {}).get("warn_msg")
            if custom_warn:
                msg = custom_warn.replace("{name}", name).replace("{count}", str(current))
            else:
                msg = get_phrase(update.effective_chat.id, "warn", name=name, count=current)
            if reason: msg += f"\n📝 Reason: {reason}"
            msg += f"\n⚠️ {remaining} warning(s) remaining before restriction."
            await update.message.reply_text(msg)
        await log_event(context, "warn", update.effective_chat.title, update.effective_user.first_name, name, reason)
    except Exception as e:
        logger.error(f"Error in warn: {e}")

# --- MUTE ---

async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text("❌ Admin-only command."); return
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to a message to mute that member."); return
        target = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        name = target.first_name or target.username or "User"
        reason = ""
        mute_minutes = 30
        for arg in (context.args or []):
            if arg.isdigit(): mute_minutes = int(arg)
            else: reason = arg
        until = datetime.now(TIMEZONE) + timedelta(minutes=mute_minutes)
        await context.bot.restrict_chat_member(chat_id, target.id, permissions=ChatPermissions(can_send_messages=False), until_date=until)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Lift Restriction (Lasso)", callback_data=f"unmute_{chat_id}_{target.id}")]])
        
        settings = load_settings()
        custom_mute = settings.get("groups", {}).get(str(chat_id), {}).get("mute_msg")
        if custom_mute:
            msg = custom_mute.replace("{name}", name).replace("{time}", str(mute_minutes))
        else:
            msg = get_phrase(chat_id, "muted", name=name, time=mute_minutes)

        if reason: msg += f"\n📝 Reason: {reason}"
        if os.path.exists(MUTE_ANIMATION_PATH):
            with open(MUTE_ANIMATION_PATH, "rb") as f:
                await update.message.reply_animation(animation=f, caption=msg, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        await log_event(context, "mute", update.effective_chat.title, update.effective_user.first_name, name, reason)
    except Exception as e:
        logger.error(f"Error in mute: {e}")
        await update.message.reply_text(f"❌ Failed: {e}")

# --- KICK ---

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_admin(update, context):
            await update.message.reply_text("❌ Admin-only command."); return
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to a message to kick that member."); return
        target = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        name = target.first_name or target.username or "User"
        reason = " ".join(context.args) if context.args else ""
        await context.bot.ban_chat_member(chat_id, target.id)
        await context.bot.unban_chat_member(chat_id, target.id)
        
        settings = load_settings()
        custom_kick = settings.get("groups", {}).get(str(chat_id), {}).get("kick_msg")
        if custom_kick:
            msg = custom_kick.replace("{name}", name)
        else:
            msg = get_phrase(chat_id, "kicked", name=name)

        if reason: msg += f"\n📝 Reason: {reason}"
        await update.message.reply_text(msg)
        await log_event(context, "kick", update.effective_chat.title, update.effective_user.first_name, name, reason)
    except Exception as e:
        logger.error(f"Error in kick: {e}")
        await update.message.reply_text(f"❌ Failed: {e}")

# --- BAN ---

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text("❌ Owner-only command."); return
        if not update.message.reply_to_message:
            await update.message.reply_text("Reply to a message to ban that member."); return
        target = update.message.reply_to_message.from_user
        chat_id = update.effective_chat.id
        name = target.first_name or target.username or "User"
        reason = " ".join(context.args) if context.args else ""
        await context.bot.ban_chat_member(chat_id, target.id)
        
        settings = load_settings()
        custom_ban = settings.get("groups", {}).get(str(chat_id), {}).get("ban_msg")
        if custom_ban:
            msg = custom_ban.replace("{name}", name)
        else:
            msg = get_phrase(chat_id, "banned", name=name)

        if reason: msg += f"\n📝 Reason: {reason}"
        await update.message.reply_text(msg)
        await log_event(context, "ban", update.effective_chat.title, update.effective_user.first_name, name, reason)
    except Exception as e:
        logger.error(f"Error in ban: {e}")
        await update.message.reply_text(f"❌ Failed: {e}")

# --- ANTIBOT ---

async def cmd_antibot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text("❌ Owner-only command."); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "antibot": False}
        current = settings["groups"][chat_id].get("antibot", False)
        settings["groups"][chat_id]["antibot"] = not current
        save_settings(settings)
        if not current:
            await update.message.reply_text("🤖 Anti-bot mode: ✅ Active\nBots added to the group will be automatically removed.")
        else:
            await update.message.reply_text("🤖 Anti-bot mode: ❌ Inactive")
    except Exception as e:
        logger.error(f"Error in antibot: {e}")

# --- CLEANSERVICE ---

async def cmd_cleanservice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text("❌ Owner-only command."); return
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        if chat_id not in settings["groups"]:
            settings["groups"][chat_id] = {"welcome": None, "rules": None, "dialect": DEFAULT_DIALECT, "clean_service": False}
        current = settings["groups"][chat_id].get("clean_service", False)
        settings["groups"][chat_id]["clean_service"] = not current
        save_settings(settings)
        if not current:
            await update.message.reply_text("🧹 Clean service messages: ✅ Active\nJoin/leave notifications will be auto-deleted.")
        else:
            await update.message.reply_text("🧹 Clean service messages: ❌ Inactive")
    except Exception as e:
        logger.error(f"Error in cleanservice: {e}")

# --- ROULETTE ---

async def cmd_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_chat.type == "private":
            await update.message.reply_text("I... don't think doing that in private is a good use of our time. Group chats only, please. 📋")
            return
        
        user = update.effective_user
        name = user.first_name or "User"
        chat_id = update.effective_chat.id
        
        # Risk Selection Keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(get_phrase(chat_id, "rl_btn_1"), callback_data=f"rl_1_{user.id}"),
                InlineKeyboardButton(get_phrase(chat_id, "rl_btn_2"), callback_data=f"rl_2_{user.id}")
            ],
            [
                InlineKeyboardButton(get_phrase(chat_id, "rl_btn_3"), callback_data=f"rl_3_{user.id}"),
                InlineKeyboardButton(get_phrase(chat_id, "rl_btn_4"), callback_data=f"rl_4_{user.id}")
            ],
            [
                InlineKeyboardButton(get_phrase(chat_id, "rl_btn_5"), callback_data=f"rl_5_{user.id}")
            ]
        ])
        
        await update.message.reply_text(
            get_phrase(chat_id, "rl_menu_body", name=name),
            reply_markup=keyboard, parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in init_roulette: {e}")

async def roulette_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query: return
    
    data = query.data
    if not data.startswith("rl_"): return
    
    parts = data.split("_")
    bullets = int(parts[1])
    target_uid = int(parts[2])
    
    if query.from_user.id != target_uid:
        await query.answer("This logical assessment isn't yours to decide.", show_alert=True)
        return

    await query.answer()
    chat_id = query.message.chat_id
    user = query.from_user
    name = user.first_name or "User"
    
    # Suspense Phase
    suspense_frames = [
        get_phrase(chat_id, "rl_frame_1"),
        get_phrase(chat_id, "rl_frame_2"),
        get_phrase(chat_id, "rl_frame_3"),
        get_phrase(chat_id, "rl_frame_4"),
    ]
    
    for frame in suspense_frames:
        try:
            await query.edit_message_text(
                f"🧤 **{get_phrase(chat_id, 'rl_progress_title' if 'rl_progress_title' in PHRASES['english'] else 'rl_menu_title' if 'rl_menu_title' in PHRASES['english'] else 'Roulette')}...**\n━━━━━━━━━━━━━━━\n{frame}",
                parse_mode="Markdown"
            )
            await asyncio.sleep(0.7)
        except Exception:
            pass # Handle if message deleted

    # Calculation
    chambers = 6
    is_dead = random.randint(1, chambers) <= bullets
    
    # Penalties (bullets: minutes)
    penalties = {1: 10, 2: 30, 3: 60, 4: 240, 5: 720}
    mute_time = penalties.get(bullets, 5)
    
    # Stats Tracking
    settings = load_settings()
    cid_str = str(chat_id)
    uid_str = str(user.id)
    
    if "roulette_stats" not in settings: settings["roulette_stats"] = {}
    if cid_str not in settings["roulette_stats"]: settings["roulette_stats"][cid_str] = {}
    if uid_str not in settings["roulette_stats"][cid_str]:
        settings["roulette_stats"][cid_str][uid_str] = {"streak": 0, "max_streak": 0, "deaths": 0, "total": 0}
    
    stats = settings["roulette_stats"][cid_str][uid_str]
    stats["total"] += 1
    
    if is_dead:
        stats["deaths"] += 1
        stats["streak"] = 0
        save_settings(settings)
        
        try:
            until = datetime.now(TIMEZONE) + timedelta(minutes=mute_time)
            await context.bot.restrict_chat_member(
                chat_id, user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until
            )
            result = get_phrase(chat_id, "rl_result_dead", name=name, bullets=bullets, time=mute_time)
        except Exception:
            result = f"💥 **BANG.**\n\n{name} took the hit. (Restriction failed — no admin permissions.)\n📈 Streak reset to 0."
    else:
        stats["streak"] += 1
        if stats["streak"] > stats["max_streak"]:
            stats["max_streak"] = stats["streak"]
        save_settings(settings)
        
        prob = f"{chambers - bullets}/{chambers}"
        result = get_phrase(chat_id, "rl_result_survive", name=name, prob=prob, streak=stats['streak'], max_streak=stats['max_streak'])

    await query.edit_message_text(
        f"🧤 **{get_phrase(chat_id, 'rl_result_title' if 'rl_result_title' in PHRASES['english'] else 'Roulette Result')}**\n━━━━━━━━━━━━━━━\n{result}",
        parse_mode="Markdown"
    )

# --- UMBRELLA ROULETTE RESTRUCTURED ---

def update_umbrella_stats(chat_id: int, user_id: int, result_type: str, inc_streak: bool = True, reset_streak: bool = False):
    settings = load_settings()
    cid_str = str(chat_id)
    uid_str = str(user_id)
    if "umbrella_stats" not in settings:
        settings["umbrella_stats"] = {}
    if cid_str not in settings["umbrella_stats"]:
        settings["umbrella_stats"][cid_str] = {}
    if uid_str not in settings["umbrella_stats"][cid_str]:
        settings["umbrella_stats"][cid_str][uid_str] = {
            "spins": 0, "streak": 0, "max_streak": 0, "survived": 0, "infected": 0, "immunity_passes": 0
        }
    stats = settings["umbrella_stats"][cid_str][uid_str]
    stats["spins"] = stats.get("spins", 0) + 1

    if result_type == "survived":
        stats["survived"] = stats.get("survived", 0) + 1
        if inc_streak:
            stats["streak"] = stats.get("streak", 0) + 1
            if stats["streak"] > stats.get("max_streak", 0):
                stats["max_streak"] = stats["streak"]
    elif result_type == "infected":
        stats["infected"] = stats.get("infected", 0) + 1
        if reset_streak:
            stats["streak"] = 0
    elif result_type == "immunity_reward":
        stats["immunity_passes"] = stats.get("immunity_passes", 0) + 1
        stats["survived"] = stats.get("survived", 0) + 1
        stats["streak"] = stats.get("streak", 0) + 2
        if stats["streak"] > stats.get("max_streak", 0):
            stats["max_streak"] = stats["streak"]

    save_settings(settings)
    return stats

def consume_immunity_pass(chat_id: int, user_id: int) -> bool:
    settings = load_settings()
    cid_str = str(chat_id)
    uid_str = str(user_id)
    user_stats = settings.get("umbrella_stats", {}).get(cid_str, {}).get(uid_str, {})
    passes = user_stats.get("immunity_passes", 0)
    if passes > 0:
        user_stats["immunity_passes"] = passes - 1
        save_settings(settings)
        return True
    return False

async def show_umbrella_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    settings = load_settings()
    cid_str = str(chat_id)
    uid_str = str(user.id)
    stats = settings.get("umbrella_stats", {}).get(cid_str, {}).get(uid_str, {
        "spins": 0, "streak": 0, "max_streak": 0, "survived": 0, "infected": 0, "immunity_passes": 0
    })
    lang = get_group_settings(chat_id).get("dialect", DEFAULT_DIALECT)
    name = user.first_name or "Subject"

    survived = stats.get("survived", 0)
    if survived >= 25:
        rank = "Level 4 Umbrella Director 👑" if lang != "arabic_fousha" else "المستوى الرابع: مدير أمبريلا 👑"
    elif survived >= 12:
        rank = "Level 3 Biohazard Specialist ☣️" if lang != "arabic_fousha" else "المستوى الثالث: أخصائي الخطر البيولوجي ☣️"
    elif survived >= 5:
        rank = "Level 2 Technical Analyst 📋" if lang != "arabic_fousha" else "المستوى الثاني: محلل بيانات 📋"
    else:
        rank = "Level 1 Trainee Subject 🧪" if lang != "arabic_fousha" else "المستوى الأول: متدرب جديد 🧪"

    if lang == "arabic_fousha":
        text = (
            "📊 **سجل السيرة الذاتية ورتبة أمبريلا**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **الهدف:** `{name}`\n"
            f"🎖️ **الرتبة الحالية:** `{rank}`\n\n"
            f"🎲 **إجمالي المحاولات (Spins):** `{stats.get('spins', 0)}`\n"
            f"✅ **التحقيقات والمهام الناجحة:** `{stats.get('survived', 0)}`\n"
            f"☣️ **مرات التحور والعدوى (Mutes):** `{stats.get('infected', 0)}`\n"
            f"🔥 **سلسلة النجاة الحالية:** `{stats.get('streak', 0)}`\n"
            f"🏆 **أعلى سلسلة نجاة:** `{stats.get('max_streak', 0)}`\n"
            f"🛡️ **بطاقات الحصانة المتاحة:** `{stats.get('immunity_passes', 0)}`\n\n"
            "_تواصل مؤسسة أمبريلا مراقبة مؤشراتك الحيوية._ 📋"
        )
    else:
        text = (
            "📊 **UMBRELLA DOSSIER & SURVIVAL METRICS**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Subject:** `{name}`\n"
            f"🎖️ **Current Clearance:** `{rank}`\n\n"
            f"🎲 **Total Spins:** `{stats.get('spins', 0)}`\n"
            f"✅ **Successful Assessments:** `{stats.get('survived', 0)}`\n"
            f"☣️ **T-Virus Mutations (Mutes):** `{stats.get('infected', 0)}`\n"
            f"🔥 **Current Survival Streak:** `{stats.get('streak', 0)}`\n"
            f"🏆 **Best Survival Streak:** `{stats.get('max_streak', 0)}`\n"
            f"🛡️ **Active Immunity Passes:** `{stats.get('immunity_passes', 0)}`\n\n"
            "_Umbrella Executive Board tracks all biometric trends._ 📋"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def umbrella_timeout_task(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, name: str, msg_id: int, caption: str, timeout_seconds: int = 60, mute_duration: int = 40, reply_markup: InlineKeyboardMarkup = None):
    try:
        group_settings = get_group_settings(chat_id)
        lang = group_settings.get("dialect", DEFAULT_DIALECT)
        
        frames_count = 6
        step = timeout_seconds / frames_count
        
        for i in range(frames_count):
            if user_id not in _umbrella_game_state or _umbrella_game_state[user_id].get("msg_id") != msg_id:
                return
            
            remaining = int(timeout_seconds - (i * step))
            bar_len = 10
            filled = max(1, int(round(bar_len * (remaining / timeout_seconds))))
            bar = "🟩" * filled + "⬛" * (bar_len - filled)
            
            ind = "🟢" if remaining >= (timeout_seconds * 0.6) else ("🟡" if remaining >= (timeout_seconds * 0.3) else "🔴")
            time_text = f"{ind} الوقت المتبقي: {remaining} ثانية" if lang == "arabic_fousha" else f"{ind} Time Remaining: {remaining}s"
            
            try:
                await context.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=msg_id,
                    caption=f"{caption}\n━━━━━━━━━━━━━━━━━━━━━\n**{time_text}**\n\n`[{bar}]`",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            except Exception:
                pass
            await asyncio.sleep(step)
            
        if user_id in _umbrella_game_state and _umbrella_game_state[user_id].get("msg_id") == msg_id:
            _umbrella_game_state.pop(user_id, None)
            
            if consume_immunity_pass(chat_id, user_id):
                saved_msg = "🛡️ **تم تفعيل بطاقة الحصانة!**\nتم تجنيبك الحظر بفضل تصريحك الأمني." if lang == "arabic_fousha" else "🛡️ **IMMUNITY PASS ACTIVATED!**\nYou avoided mutual restriction due to your security clearance."
                new_caption = f"{caption}\n\n{saved_msg}"
            else:
                until = datetime.now(TIMEZONE) + timedelta(seconds=mute_duration)
                muted = True
                try:
                    await context.bot.restrict_chat_member(
                        chat_id, user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=until
                    )
                except Exception as e:
                    logger.warning(f"Failed to mute user on timeout: {e}")
                    muted = False
                
                update_umbrella_stats(chat_id, user_id, "infected", reset_streak=True)
                
                if lang == "arabic_fousha":
                    punish_text = f"⏱️ **انتهى الوقت المحدد.**\nتم تطبيق حظر مؤقت {mute_duration} ثانية لعدم الاستجابة.\n" + (f"🔇 **تم الحظر.**" if muted else f"⚠️ (فشل الحظر - صلاحيات غير كافية).")
                else:
                    punish_text = f"⏱️ **TIME EXCEEDED.**\n_Subject {name} failed to provide data. Containment applied ({mute_duration}s)._\n" + (f"🔇 **Muted.**" if muted else f"⚠️ (Restriction failed).")
                new_caption = f"{caption}\n\n{punish_text}"
            
            try:
                await context.bot.edit_message_caption(chat_id=chat_id, message_id=msg_id, caption=new_caption, parse_mode="Markdown")
            except Exception:
                try:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=new_caption, parse_mode="Markdown")
                except Exception: pass
                
            await asyncio.sleep(300)
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception: pass
                
    except Exception as e:
        logger.error(f"Error in umbrella_timeout_task: {e}")

async def cmd_umbrella(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Launch the Resident Evil themed Umbrella Roulette."""
    if not update.effective_chat or not update.message: return
    chat_id = update.effective_chat.id
    
    if context.args and context.args[0].lower() in ["stats", "rank", "احصائيات", "رتبتي"]:
        await show_umbrella_stats(update, context)
        return

    if reason := get_lock_reason("gumbrella"):
        await update.message.reply_text(get_phrase(chat_id, "lock_denied_gumbrella", reason=reason), parse_mode="Markdown")
        return

    try:
        user = update.effective_user
        name = user.first_name or "Subject"
        group_settings = get_group_settings(chat_id)
        lang = group_settings.get("dialect", DEFAULT_DIALECT)
        is_ar = (lang == "arabic_fousha")

        if user.id in _umbrella_game_state:
            msg = "⚠️ **أنت تخضع حالياً لاختبار نفسي!**\nأكمل التقييم الحالي أو انتظر انتهاء الوقت." if is_ar else "⚠️ **INTERROGATION IN PROGRESS!**\nResolve your current active assessment before spinning again."
            await update.message.reply_text(msg, parse_mode="Markdown")
            return

        roll = random.random()
        if roll < 0.60:
            category = "fact"
        elif roll < 0.75:
            category = "tvirus"
        elif roll < 0.85:
            category = "command"
        elif roll < 0.95:
            category = "escape"
        else:
            category = "reward"

        photo_map = {
            "fact": "Avatar/umbrella_spin_fact.jpeg",
            "command": "Avatar/umbrella_spin_command.jpeg",
            "tvirus": "Avatar/umbrella_spin_tvirus.jpeg",
            "escape": "Avatar/umbrella_spin_run.jpeg",
            "reward": "Avatar/umbrella_spin_reward.jpeg"
        }
        photo_path = photo_map.get(category)

        if is_ar:
            init_frame = "🧪 `[▓▓░░░░░░░░] 20%`\n_تأمين المحيط الخارجي..._"
            frames = [
                "🧪 `[▓▓▓▓▓░░░░░] 45%`\n_تحليل المقاييس الحيوية للهدف..._",
                "🧪 `[▓▓▓▓▓▓▓▓░░] 78%`\n_حساب احتمالات النجاة..._",
                "🧪 `[▓▓▓▓▓▓▓▓▓▓] 99%`\n_إقفال مسار عجلة أمبريلا..._"
            ]
        else:
            init_frame = "🧪 `[▓▓░░░░░░░░] 20%`\n_Securing perimeter..._"
            frames = [
                "🧪 `[▓▓▓▓▓░░░░░] 45%`\n_Analyzing subject biometrics..._",
                "🧪 `[▓▓▓▓▓▓▓▓░░] 78%`\n_Computing survival odds..._",
                "🧪 `[▓▓▓▓▓▓▓▓▓▓] 99%`\n_Locking roulette trajectory..._"
            ]

        status = await update.message.reply_text(
            f"🧤 **{get_phrase(chat_id, 'umbrella_spinning')}**\n━━━━━━━━━━━━━━━━━━━━━\n{init_frame}",
            parse_mode="Markdown"
        )

        for frame in frames:
            await asyncio.sleep(0.6)
            try:
                await status.edit_text(f"🧤 **{get_phrase(chat_id, 'umbrella_spinning')}**\n━━━━━━━━━━━━━━━━━━━━━\n{frame}", parse_mode="Markdown")
            except Exception: pass

        await asyncio.sleep(0.6)
        try: await status.delete()
        except Exception: pass

        kbd = None
        timeout_dur = 60
        mute_dur = 40

        if category == "fact":
            q_idx = random.randint(1, 49)
            q_key = f"umbrella_fact_q{q_idx}"
            question = get_phrase(chat_id, q_key).replace("_", "\\_")
            header = get_phrase(chat_id, "umbrella_fact_header", name=name)
            full_msg = f"{header}**{question}**"

            if q_idx == 9:
                kbd = InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q9_1"), callback_data=f"ub_q9_1_{user.id}")],
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q9_2"), callback_data=f"ub_q9_2_{user.id}")],
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q9_3"), callback_data=f"ub_q9_3_{user.id}")],
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q9_4"), callback_data=f"ub_q9_4_{user.id}")]
                ])
            elif q_idx == 10:
                kbd = InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q10_1"), callback_data=f"ub_q10_1_{user.id}")],
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q10_2"), callback_data=f"ub_q10_2_{user.id}")],
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q10_3"), callback_data=f"ub_q10_3_{user.id}")],
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q10_4"), callback_data=f"ub_q10_4_{user.id}")],
                    [InlineKeyboardButton(get_phrase(chat_id, "umbrella_btn_q10_5"), callback_data=f"ub_q10_5_{user.id}")]
                ])
            else:
                rank_btn = "📊 رتبتي في أمبريلا" if is_ar else "📊 My Umbrella Rank"
                kbd = InlineKeyboardMarkup([[InlineKeyboardButton(rank_btn, callback_data=f"ub_st_{user.id}")]])

        elif category == "tvirus":
            full_msg = get_phrase(chat_id, "umbrella_cat_tvirus", name=name)
            btn1 = "💉 حقن المصل (75%)" if is_ar else "💉 Inject Antidote (75%)"
            btn2 = "🧪 عزل العينة (65%)" if is_ar else "🧪 Contain Sample (65%)"
            btn3 = "🛡️ حجر ذاتي (85%)" if is_ar else "🛡️ Self Quarantine (85%)"
            kbd = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn1, callback_data=f"ub_tv_1_{user.id}")],
                [InlineKeyboardButton(btn2, callback_data=f"ub_tv_2_{user.id}")],
                [InlineKeyboardButton(btn3, callback_data=f"ub_tv_3_{user.id}")]
            ])
            timeout_dur = 35
            mute_dur = 45

        elif category == "command":
            mandate_options = [
                "صرح بالولاء لمؤسسة أمبريلا في رسالة نصية أو صوتية الآن." if is_ar else "Declare loyalty to Umbrella Corporation in text or voice.",
                "أرسل ٣ إيموجيات للخطر البيولوجي (☣️ 🧪 🔬)." if is_ar else "Send 3 biohazard emojis (☣️ 🧪 🔬).",
                "منشن أحد مشرفي المجموعه واطلب منه تصريح حجر أمني." if is_ar else "Tag an admin and request Level 2 clearance.",
                "اذكر اسم شخصيتك المفضلة من Resident Evil." if is_ar else "State your favorite Resident Evil character in chat."
            ]
            mandate = random.choice(mandate_options)
            full_msg = get_phrase(chat_id, "umbrella_cat_command", name=name, mandate=mandate)
            btn_done = "✅ تم تنفيذ التكليف" if is_ar else "✅ Executive Directive Completed"
            kbd = InlineKeyboardMarkup([[InlineKeyboardButton(btn_done, callback_data=f"ub_cm_1_{user.id}")]])
            timeout_dur = 45
            mute_dur = 30

        elif category == "escape":
            full_msg = get_phrase(chat_id, "umbrella_cat_escape", name=name)
            btn_esc = "🚪 🏃 هروب سرييييع!" if is_ar else "🚪 🏃 EVACUATE NOW!"
            kbd = InlineKeyboardMarkup([[InlineKeyboardButton(btn_esc, callback_data=f"ub_es_1_{user.id}_{int(_time.time())}")]])
            timeout_dur = 15
            mute_dur = 35

        else: # reward
            full_msg = get_phrase(chat_id, "umbrella_cat_reward", name=name)
            btn_rw = "🎖️ استلام التصريح البلاتيني" if is_ar else "🎖️ Claim Level 4 Security Clearance"
            kbd = InlineKeyboardMarkup([[InlineKeyboardButton(btn_rw, callback_data=f"ub_rw_1_{user.id}")]])
            update_umbrella_stats(chat_id, user.id, "immunity_reward")
            timeout_dur = 0 # No timeout mute for reward

        if photo_path and os.path.exists(photo_path):
            with open(photo_path, "rb") as photo_file:
                final_msg = await update.message.reply_photo(photo=photo_file, caption=full_msg, reply_markup=kbd, parse_mode="Markdown")
        else:
            final_msg = await update.message.reply_text(full_msg, reply_markup=kbd, parse_mode="Markdown")

        if timeout_dur > 0:
            _umbrella_game_state[user.id] = {
                "chat_id": chat_id,
                "q_idx": q_idx if category == "fact" else -1,
                "msg_id": final_msg.message_id,
                "start_time": _time.time()
            }
            safe_create_task(
                umbrella_timeout_task(context, chat_id, user.id, name, final_msg.message_id, full_msg, timeout_seconds=timeout_dur, mute_duration=mute_dur, reply_markup=kbd),
                name=f"umbrella_timeout_{user.id}"
            )

    except Exception as e:
        logger.error(f"Error in cmd_umbrella: {e}")

async def cmd_explain_umbrella(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    settings = load_settings()
    lang = settings.get("groups", {}).get(str(chat_id), {}).get("dialect", DEFAULT_DIALECT)
    
    if lang == "arabic_fousha":
        text = (
            "📋 **دليل شـامل — بروتوكولات روليت أمبريلا (Umbrella Roulette Protocols)**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "**المضيف:** `غريس أشكروفت` (محللة البيانات الجنائية) 📋\n\n"
            "🎮 **طرق تشغيل اللعبة:**\n"
            "▸ الأوامر: `/gumbrella` أو `/a`\n"
            "▸ الكلمات المفتاحية: `مظلة` · `مظله` · `ا` · `a` · `A` · `امبريلا` · `روليت` · `umbrella` · `roulette`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🧪 **الفئات الـ ٥ ونظام المواجهة:**\n\n"
            "🟣 **١. التحقيق النفسي (Psychological Interrogation):**\n"
            "   - تطرح غريس سؤالاً شخصياً أو نفسياً مع مهلة **60 ثانية**.\n"
            "   - **كيف تجيب؟** يمكنك الرد مباشرة برسالة نصية في الدردشة أو الضغط على أزرار الخيارات.\n"
            "   - يتم تشفير إجابتك وتوثيقها في ملفك الجنائي.\n"
            "   - التأخر عن الرد يسبب حظراً مؤقتاً لـ **40 ثانية**!\n\n"
            "☣️ **٢. تفشي T-Virus (Biological Hazard):**\n"
            "   - تسرب بيولوجي كيميائي في القطاع! اختر بروتوكول المواجهة:\n"
            "     `[ 💉 حقن المصل (75%) ]` · `[ 🧪 عزل العينة (65%) ]` · `[ 🛡️ حجر ذاتي (85%) ]`\n"
            "   - النجاح يمنحك **بطاقة حصانة أمنية**.\n"
            "   - الفشل يسبب تحوراً وراثياً وحظراً لـ **45 ثانية**.\n\n"
            "🔵 **٣. تكليف أمبريلا التنفيذي (Executive Mandate):**\n"
            "   - تكليف مباشر من إدارة أمبريلا (إعلان الولاء، إرسال إيموجيات بيولوجية، منشن لـ Admin).\n"
            "   - عند الإتمام اضغط `[ ✅ تم تنفيذ التكليف ]` لتوثيق الالتزام (+1 ستريك).\n\n"
            "🔴 **٤. الإخلاء العاجل (Containment Evacuation):**\n"
            "   - إنذار خرق الحجر! أبواب الفولاذ تقتلق خلال **15 ثانية**!\n"
            "   - اضغط `[ 🚪 🏃 هروب سرييييع! ]` فوراً قبل إغلاق القطاع بالكامل.\n"
            "   - الفشل يسبب الحجز في قطاع العزل لـ **35 ثانية**.\n\n"
            "🟡 **٥. مكافأة التصريح الرئاسي (Level 4 Clearance):**\n"
            "   - تصريح بلاتيني نادر! يمنحك **بطاقة حصانة** + **تعزيز +2 لـ ستريك النجاة**.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🛡️ **نظام الحصانة التلقائي:**\n"
            "إذا كانت لديك **بطاقة حصانة (Immunity Pass)**، فسيتم تفعيلها تلقائياً لإلغاء أي حظر مؤقت عند انتهاء الوقت!\n\n"
            "📊 **الملف الشخصي والرتبة:**\n"
            "اكتب `/gumbrella stats` لمعاينة ملفك الجنائي وسلسلة النجاة (Streak) ورتبتك من *متدرب* حتى *مدير أمبريلا*.\n\n"
            "_تذكر دائماً: التزم بالقوانين ولا تتحدى البيانات 📋_"
        )
    else:
        text = (
            "📋 **COMPREHENSIVE GUIDE — UMBRELLA ROULETTE PROTOCOLS**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "**Host:** `Grace Ashcroft` (FBI Technical Analyst) 📋\n\n"
            "🎮 **How to Trigger the Game:**\n"
            "▸ Commands: `/gumbrella` or `/a`\n"
            "▸ Trigger Keywords: `a` · `A` · `umbrella` · `roulette` · `مظلة` · `امبريلا`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🧪 **The 5 Biohazard Assessment Modes:**\n\n"
            "🟣 **1. Psychological Interrogation (Fact Probe):**\n"
            "   - Grace poses a personal or psychological query with a **60-second timer**.\n"
            "   - **How to Answer:** Reply directly with a chat text message or tap the option buttons.\n"
            "   - Your response is encrypted and logged to your FBI case file.\n"
            "   - Timeout results in a **40-second mutual restriction** for non-compliance!\n\n"
            "☣️ **2. T-Virus Biohazard Hazard:**\n"
            "   - Biological leak detected! Select your counter-protocol:\n"
            "     `[ 💉 Inject Antidote (75%) ]` · `[ 🧪 Contain Sample (65%) ]` · `[ 🛡️ Self Quarantine (85%) ]`\n"
            "   - Success neutralizes the strain & awards an **Immunity Pass**.\n"
            "   - Failure mutates the strain, resulting in a **45-second quarantine mute**.\n\n"
            "🔵 **3. Executive Mandate (Directive):**\n"
            "   - Direct task from Umbrella Executive Board (declare loyalty, send biohazard emojis, tag an admin).\n"
            "   - Tap `[ ✅ Executive Directive Completed ]` to confirm (+1 Streak).\n\n"
            "🔴 **4. Containment Breach Evacuation (Reflex Challenge):**\n"
            "   - Emergency warning! Blast doors sealing in **15 seconds**!\n"
            "   - Tap `[ 🚪 🏃 EVACUATE NOW! ]` immediately to escape.\n"
            "   - Failure seals the sector, trapping you in quarantine (**35s mute**).\n\n"
            "🟡 **5. Level 4 Clearance Award (Bonus):**\n"
            "   - Rare drop! Grants a **Purge Immunity Shield** + **+2 Survival Streak Boost**.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🛡️ **Automated Immunity Shield:**\n"
            "If you possess an **Immunity Pass**, the system automatically consumes it to cancel any upcoming restriction penalty if your timer ever expires!\n\n"
            "📊 **Personal Dossier & Clearance Ranks:**\n"
            "Type `/gumbrella stats` to review your survival streak, clearance rank (*Trainee* ➔ *Umbrella Director*), and immunity inventory.\n\n"
            "_Remember: Comply with system protocols. The data is absolute. 📋_"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def umbrella_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data.startswith("ub_"): return
    
    parts = query.data.split("_")
    q_type = parts[1] # q9, q10, rev, tv, cm, es, rw, st
    
    if q_type == "st":
        target_uid = int(parts[2])
        if query.from_user.id != target_uid:
            await query.answer("هذا الملف يخص الضحية فقط.", show_alert=True); return
        settings = load_settings()
        stats = settings.get("umbrella_stats", {}).get(str(query.message.chat_id), {}).get(str(target_uid), {})
        survived = stats.get("survived", 0)
        streak = stats.get("streak", 0)
        passes = stats.get("immunity_passes", 0)
        await query.answer(f"📊 رتبة أمبريلا: {survived} نجاحات | 🔥 ستريك: {streak} | 🛡️ حصانة: {passes}", show_alert=True)
        return

    if q_type == "rev":
        ans_id = parts[2]
        if ans_id in _umbrella_answers:
            ans_text = _umbrella_answers[ans_id][:150]
            is_arabic = get_phrase(query.message.chat_id, "welcome").startswith("أوه")
            alert_text = f"[ تصريح أمني ] تم الوصول للملف 📂\n\nالاعتراف المسترد:\n\"{ans_text}\"" if is_arabic else f"[ SECURITY CLEARANCE ACCEPTED ] 📂\n\nRecovered Confession:\n\"{ans_text}\""
            await query.answer(alert_text, show_alert=True)
        else:
            await query.answer("لقد انتهت صلاحية هذه الإجابة (تم مسح البيانات).", show_alert=True)
        return
        
    target_uid = int(parts[3])
    if query.from_user.id != target_uid:
        await query.answer("This logical assessment isn't yours to decide.", show_alert=True); return

    await query.answer()
    chat_id = query.message.chat_id
    is_ar = get_group_settings(chat_id).get("dialect", DEFAULT_DIALECT) == "arabic_fousha"
    raw_text = query.message.caption if query.message.photo else query.message.text
    safe_original = (raw_text or "").replace("_", "\\_")

    if q_type == "tv": # T-Virus counter-measure
        opt = int(parts[2])
        probs = {1: 0.75, 2: 0.65, 3: 0.85}
        success = random.random() < probs.get(opt, 0.70)
        
        if success:
            st = update_umbrella_stats(chat_id, target_uid, "immunity_reward")
            res_text = (
                f"✅ **تقرير المعاينة: نجاح التطهير البيولوجي**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧪 **النتيجة:** تم تحييد الفيروس واستقرار مؤشرات البقاء.\n"
                f"🛡️ **المكافأة:** +1 بطاقة حصانة أمنية\n"
                f"🔥 **سلسلة النجاة:** `{st.get('streak', 1)}`"
            ) if is_ar else (
                f"✅ **ASSESSMENT REPORT: DECONTAMINATION SUCCESSFUL**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🧪 **Result:** Pathogen neutralized & biometrics stabilized.\n"
                f"🛡️ **Reward:** +1 Immunity Pass\n"
                f"🔥 **Current Streak:** `{st.get('streak', 1)}`"
            )
        else:
            if consume_immunity_pass(chat_id, target_uid):
                st = update_umbrella_stats(chat_id, target_uid, "survived", inc_streak=False)
                res_text = (
                    f"🛡️ **تقرير المعاينة: تفعيل بطاقة الحصانة**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ **النتيجة:** حدث تحور بيولوجي لكن تم حمايتك بفضل تصريحك الأمني!\n"
                    f"❌ **العقوبة:** تم إلغاؤها ومنع الحظر المؤقت.\n"
                    f"🔥 **سلسلة النجاة:** `{st.get('streak', 0)}`"
                ) if is_ar else (
                    f"🛡️ **ASSESSMENT REPORT: IMMUNITY SHIELD ACTIVATED**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ **Result:** Mutation detected, but your clearance prevented quarantine!\n"
                    f"❌ **Penalty:** Mute restriction averted.\n"
                    f"🔥 **Current Streak:** `{st.get('streak', 0)}`"
                )
            else:
                st = update_umbrella_stats(chat_id, target_uid, "infected", reset_streak=True)
                until = datetime.now(TIMEZONE) + timedelta(seconds=45)
                try:
                    await context.bot.restrict_chat_member(chat_id, target_uid, permissions=ChatPermissions(can_send_messages=False), until_date=until)
                except Exception: pass
                res_text = (
                    f"☣️ **تقرير المعاينة: فشل التطهير وتحور الفيروس**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ **النتيجة:** فشل بروتوكول المواجهة وحدث تحور وراثي.\n"
                    f"🔇 **العقوبة:** تم فرض حظر مؤقت (45 ثانية) في قطاع العزل.\n"
                    f"📉 **سلسلة النجاة:** إعادة تعيين إلى 0."
                ) if is_ar else (
                    f"☣️ **ASSESSMENT REPORT: MUTATION FAILED**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ **Result:** Counter-protocol failed. Genetic mutation detected.\n"
                    f"🔇 **Penalty:** 45-second mutual restriction applied.\n"
                    f"📉 **Streak:** Reset to 0."
                )

        final_response = f"{safe_original}\n\n{res_text}"

    elif q_type == "cm": # Command directive done
        st = update_umbrella_stats(chat_id, target_uid, "survived")
        res_text = (
            f"✅ **تقرير المعاينة: توثيق التكليف التنفيذي**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 **النتيجة:** تم إثبات الالتزام لبروتوكول مؤسسة أمبريلا.\n"
            f"🔥 **سلسلة النجاة:** `{st.get('streak', 1)}`"
        ) if is_ar else (
            f"✅ **ASSESSMENT REPORT: DIRECTIVE VERIFIED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 **Result:** Executive compliance logged to ledger.\n"
            f"🔥 **Current Streak:** `{st.get('streak', 1)}`"
        )
        final_response = f"{safe_original}\n\n{res_text}"

    elif q_type == "es": # Evacuation button
        start_t = int(parts[4]) if len(parts) > 4 else int(_time.time())
        elapsed = round(_time.time() - start_t, 1)
        if elapsed <= 15:
            st = update_umbrella_stats(chat_id, target_uid, "survived")
            res_text = (
                f"🏃💨 **تقرير المعاينة: نجاح الإخلاء السريع**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ **الزمن المستغرق:** {elapsed} ثانية (قبل إغلاق القطاع).\n"
                f"🔥 **سلسلة النجاة:** `{st.get('streak', 1)}`"
            ) if is_ar else (
                f"🏃💨 **ASSESSMENT REPORT: EVACUATION SUCCESSFUL**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ **Elapsed Time:** {elapsed}s (escaped before sector lockdown).\n"
                f"🔥 **Current Streak:** `{st.get('streak', 1)}`"
            )
        else:
            st = update_umbrella_stats(chat_id, target_uid, "infected", reset_streak=True)
            until = datetime.now(TIMEZONE) + timedelta(seconds=35)
            try: await context.bot.restrict_chat_member(chat_id, target_uid, permissions=ChatPermissions(can_send_messages=False), until_date=until)
            except Exception: pass
            res_text = (
                f"🚪💥 **تقرير المعاينة: إغلاق أبواب العزل**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ **الزمن المستغرق:** {elapsed} ثانية (تأخير عن المهلة).\n"
                f"🔇 **العقوبة:** احتجاز في قطاع العزل لـ 35 ثانية.\n"
                f"📉 **سلسلة النجاة:** إعادة تعيين إلى 0."
            ) if is_ar else (
                f"🚪💥 **ASSESSMENT REPORT: EVACUATION TIMED OUT**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ **Elapsed Time:** {elapsed}s (evacuation window expired).\n"
                f"🔇 **Penalty:** 35-second quarantine restriction applied.\n"
                f"📉 **Streak:** Reset to 0."
            )

        final_response = f"{safe_original}\n\n{res_text}"

    elif q_type == "rw": # Reward claim
        st = update_umbrella_stats(chat_id, target_uid, "immunity_reward")
        res_text = (
            f"🎖️ **تقرير المعاينة: اعتماد التصريح الرئاسي (Level 4)**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 **المكافأة:** +1 بطاقة حصانة + تعزيز ستريك النجاة (+2).\n"
            f"🔥 **سلسلة النجاة الجديدة:** `{st.get('streak', 1)}`"
        ) if is_ar else (
            f"🎖️ **ASSESSMENT REPORT: LEVEL 4 CLEARANCE GRANTED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 **Reward:** +1 Immunity Pass & +2 Streak Boost applied!\n"
            f"🔥 **New Streak:** `{st.get('streak', 1)}`"
        )
        final_response = f"{safe_original}\n\n{res_text}"

    elif q_type == "q10":
        opt = int(parts[2])
        st = update_umbrella_stats(chat_id, target_uid, "survived")
        reactions_q10_ar = {
            1: "قرار عقلاني. تحييد التهديد بسرعة هو الخيار الأمثل.",
            2: "غريزة البقاء. حذر ومبرر.",
            3: "تفاؤل، لكنه مخاطرة كبيرة.",
            4: "...جنون إحصائي.",
            5: "عقدة البطل؟ حظاً موفقاً."
        }
        react = reactions_q10_ar.get(opt, "تم تسجيل البيانات.") if is_ar else "Data recorded."
        res_text = (
            f"📋 **تقرير المعاينة: توثيق الاستجواب النفسي**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 **تحليل غريس:** {react}\n"
            f"🔥 **سلسلة النجاة:** `{st.get('streak', 1)}`"
        ) if is_ar else (
            f"📋 **ASSESSMENT REPORT: INTERROGATION LOGGED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 **Analyst Note:** {react}\n"
            f"🔥 **Current Streak:** `{st.get('streak', 1)}`"
        )
        final_response = f"{safe_original}\n\n{res_text}"

    else: # q9 or generic
        opt = int(parts[2])
        st = update_umbrella_stats(chat_id, target_uid, "survived")
        res_text = (
            f"📋 **تقرير المعاينة: توثيق الاستجواب النفسي**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 **تحليل غريس:** تمت إضافة إجابتك إلى السجل الجنائي بنجاح.\n"
            f"🔥 **سلسلة النجاة:** `{st.get('streak', 1)}`"
        ) if is_ar else (
            f"📋 **ASSESSMENT REPORT: INTERROGATION LOGGED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 **Analyst Note:** Data saved to your criminal dossier.\n"
            f"🔥 **Current Streak:** `{st.get('streak', 1)}`"
        )
        final_response = f"{safe_original}\n\n{res_text}"

    if query.message.photo:
        await query.edit_message_caption(caption=final_response, parse_mode="Markdown")
    else:
        await query.edit_message_text(text=final_response, parse_mode="Markdown")

    _umbrella_game_state.pop(target_uid, None)


async def captcha_timeout_task(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, msg_id: int):
    """Enforces captcha time limit. Kicks user if not solved in 60s."""
    await asyncio.sleep(60)
    if user_id in pending_captcha and pending_captcha[user_id].get("msg_id") == msg_id:
        try:
            # Cleanup
            pending_captcha.pop(user_id, None)
            # Delete captcha message
            try: await context.bot.delete_message(chat_id, msg_id)
            except: pass
            
            # Kick user
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id) # Unban so they can try again later
            
            logger.info(f"🛡️ Captcha: User {user_id} kicked from {chat_id} (Timeout)")
        except Exception as e:
            logger.error(f"Error in captcha timeout: {e}")


# --- WELCOME / FAREWELL ---

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message: return
        chat_id = message.chat_id
        group_settings = get_group_settings(chat_id)
        if not group_settings.get("welcome_enabled", True):
            return
        for new_member in (message.new_chat_members or []):
            if new_member.is_bot:
                if group_settings.get("antibot", False):
                    try:
                        await context.bot.ban_chat_member(chat_id, new_member.id)
                        await context.bot.unban_chat_member(chat_id, new_member.id)
                        await message.reply_text(f"🤖 Bot @{new_member.username or new_member.first_name} removed. Anti-bot mode is active.")
                    except Exception: pass
                continue
                # Captcha logic (H-02: Added actual timeout enforcement)
                if group_settings.get("captcha", False):
                    a, b = random.randint(1, 20), random.randint(1, 20)
                    op = random.choice(["+", "-", "*"])
                    answer = a + b if op == "+" else (a - b if op == "-" else a * b)
                    
                    question_text = (
                        f"📋 **Verification Required**\n━━━━━━━━━━━━━━━\n👤 {new_member.first_name}\n\n"
                        f"Hello. Before you can participate, I need to verify you're human.\n\n"
                        f"__Solve:__ `{a} {op} {b} = ?`\n\n"
                        f"_You have 60 seconds. Failure = automatic removal._"
                    )
                    
                    options = list({answer, answer + random.randint(1,5), answer - random.randint(1,5), answer + random.randint(6,15)})
                    random.shuffle(options)
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(str(opt), callback_data=f"captcha_{new_member.id}_{opt}_{answer}")] for opt in options])
                    
                    try:
                        # Mute user first
                        await context.bot.restrict_chat_member(chat_id, new_member.id, permissions=ChatPermissions(can_send_messages=False))
                        sent_msg = await message.reply_text(question_text, reply_markup=keyboard)
                        
                        # Register in tracked state
                        pending_captcha[new_member.id] = {
                            "chat_id": chat_id,
                            "msg_id": sent_msg.message_id,
                            "answer": answer,
                            "start_time": _time.time()
                        }
                        
                        # H-02: Start REAL timeout enforcement
                        safe_create_task(captcha_timeout_task(context, chat_id, new_member.id, sent_msg.message_id), name=f"captcha_timeout_{new_member.id}")
                    except Exception as e:
                        logger.error(f"Captcha initiation error: {e}")
                    continue
                
            # Normal Welcome
            if group_settings.get("welcome"):
                welcome_text = group_settings.get("welcome")
                welcome_text = welcome_text.replace("{name}", new_member.first_name)
                welcome_text = welcome_text.replace("{group}", message.chat.title or "this group")
                try:
                    await message.reply_text(welcome_text)
                except Exception as e:
                    logger.error(f"Welcome message error: {e}")
                    
    except Exception as e:
        logger.error(f"Error in welcome_new_member: {e}")

async def farewell_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message: return
        chat_id = message.chat_id
        group_settings = get_group_settings(chat_id)
        if not group_settings.get("farewell_enabled", True):
            return
        if group_settings.get("clean_service", False):
            try: await message.delete()
            except Exception: pass
            return
        left_member = message.left_chat_member
        if not left_member: return
        
        custom_farewell = group_settings.get("farewell")
        if custom_farewell:
            final_msg = custom_farewell.replace("{name}", left_member.first_name or "Unknown")
            final_msg = final_msg.replace("{group}", message.chat.title or "this group")
        else:
            final_msg = get_phrase(chat_id, "bye")

        try:
            await message.reply_text(final_msg)
        except Exception as e:
            if "Forbidden" in str(e): return
            raise e
    except Exception as e:
        logger.error(f"Error in farewell: {e}")

# --- FILTERS ---

async def link_filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message or not message.text: return
        chat_id = update.effective_chat.id
        group_settings = get_group_settings(chat_id)
        if not group_settings.get("link_filter", False): return
        if await is_admin(update, context): return
        import re
        url_pattern = re.compile(r'(https?://|www\.|t\.me/|@\w+\.\w+)', re.IGNORECASE)
        if url_pattern.search(message.text):
            username = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name
            try:
                await message.delete()
                await context.bot.send_message(chat_id, get_phrase(chat_id, "link_blocked", name=username))
            except Exception as e:
                logger.error(f"Link filter error: {e}")
    except Exception as e:
        logger.error(f"Error in link_filter: {e}")

async def track_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        if not message or not update.effective_user: return
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if chat_id not in group_stats: group_stats[chat_id] = {"messages": 0, "users": {}}
        group_stats[chat_id]["messages"] = group_stats[chat_id].get("messages", 0) + 1
        if str(user_id) not in group_stats[chat_id]["users"]:
            group_stats[chat_id]["users"][str(user_id)] = 0
        group_stats[chat_id]["users"][str(user_id)] += 1
        # Spam filter
        group_settings = get_group_settings(chat_id)
        if group_settings.get("spam_filter") and message.text:
            max_chars = group_settings.get("max_chars", 500)
            if len(message.text) > max_chars and not await is_admin(update, context):
                username = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name
                try:
                    await message.delete()
                    await context.bot.send_message(chat_id, f"📰 {username}, that message was too long ({len(message.text)} chars > {max_chars} limit).")
                except Exception: pass
        # Repeat filter
        if group_settings.get("repeat_filter") and message.text:
            if chat_id not in repeat_history: repeat_history[chat_id] = {}
            uid = str(user_id)
            prev_msgs = repeat_history[chat_id].get(uid, [])
            same_count = sum(1 for m in prev_msgs if m == message.text)
            if same_count >= 2 and not await is_admin(update, context):
                try:
                    await message.delete()
                    await context.bot.send_message(chat_id, f"🔄 @{update.effective_user.username or update.effective_user.first_name} — repeated messages removed.")
                except Exception: pass
            prev_msgs.append(message.text)
            if len(prev_msgs) > 10: prev_msgs = prev_msgs[-10:]
            repeat_history[chat_id][uid] = prev_msgs
        # Track member
        async with settings_session() as settings:
            chat_id_str = str(chat_id)
            if chat_id_str not in settings.get("groups", {}): 
                settings["groups"][chat_id_str] = {
                    "welcome": None, "rules": None, "dialect": DEFAULT_DIALECT,
                    "link_filter": False, "ai_enabled": False, "members": []
                }
            if "members" not in settings["groups"][chat_id_str]: 
                settings["groups"][chat_id_str]["members"] = []
            if user_id not in settings["groups"][chat_id_str]["members"]:
                settings["groups"][chat_id_str]["members"].append(user_id)
    except Exception as e:
        logger.error(f"Error in track_activity: {e}")

async def message_buffer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message or update.channel_post
        if not message: return
        chat_id = message.chat_id
        if chat_id not in _chat_msg_buffer:
            _chat_msg_buffer[chat_id] = deque(maxlen=5000)
        _chat_msg_buffer[chat_id].append(message.message_id)
    except Exception: pass

# --- APPLY SYSTEM ---

async def cmd_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        # Global Lock Check
        if reason := get_lock_reason("gapply"):
            await update.message.reply_text(get_phrase(chat_id, "lock_denied_gapply", reason=reason), parse_mode="Markdown")
            return

        user = update.effective_user
        chat_id = update.effective_chat.id
        if update.effective_chat.type != "private":
            group_settings = get_group_settings(chat_id)
            if not group_settings.get("apply_required", False):
                await update.message.reply_text("ℹ️ The application form is not required in this group.")
                return
            await update.message.reply_text(
                f"📋 **Application Process**\n━━━━━━━━━━━━━━━\nHello {user.first_name}.\nPlease message me privately to complete your application.\n\n_— Grace_",
                parse_mode="Markdown"
            )
            try:
                await context.bot.send_message(user.id, APPLY_INTRO)
            except Exception:
                await update.message.reply_text("⚠️ I couldn't message you privately. Please start a private chat with me first.")
            return
        pending_apply[user.id] = {"current_q": 0, "answers": [], "chat_id": None}
        await update.message.reply_text(APPLY_INTRO)
        await update.message.reply_text(APPLY_QUESTIONS[0]["question"])
    except Exception as e:
        logger.error(f"Error in apply: {e}")

async def apply_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query: return
    await query.answer()
    try:
        data = query.data
        if not data.startswith("ap_"): return
        parts = data.split("_", 3)
        user_id = int(parts[1])
        q_idx = int(parts[2])
        answer_text = parts[3] if len(parts) > 3 else "?"
        if user_id not in pending_apply: return
        state = pending_apply[user_id]
        q = APPLY_QUESTIONS[q_idx]
        state["answers"].append({"question": q["question"], "answer": answer_text})
        next_q_idx = q_idx + 1
        state["current_q"] = next_q_idx
        if next_q_idx < len(APPLY_QUESTIONS):
            next_q = APPLY_QUESTIONS[next_q_idx]
            if "options" in next_q:
                keyboard = [[InlineKeyboardButton(opt, callback_data=f"ap_{user_id}_{next_q_idx}_{opt}")] for opt in next_q["options"]]
                await query.edit_message_text(next_q["question"], reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.edit_message_text(next_q["question"])
        else:
            answers_text = "\n".join([f"**Q:** {a['question']}\n**A:** {a['answer']}" for a in state["answers"]])
            report = (
                f"📋 **New Application — {query.from_user.first_name}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 User ID: `{user_id}`\n"
                f"📱 Username: @{query.from_user.username or 'N/A'}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{answers_text}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"_Application logged. — Grace_"
            )
            if OWNER_ID:
                try: await context.bot.send_message(OWNER_ID, report, parse_mode="Markdown")
                except Exception: pass
            if MASTER_ID:
                try: await context.bot.send_message(MASTER_ID, report, parse_mode="Markdown")
                except Exception: pass
            await query.edit_message_text("✅ Application submitted. It's been logged and forwarded to the team.\n_— Grace Ashcroft 📋_")
            pending_apply.pop(user_id, None)
    except Exception as e:
        logger.error(f"Error in apply_answer_callback: {e}")

# --- CLEARCHAT ---

async def cmd_cleardata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_owner(update, context):
            await update.message.reply_text(get_phrase(update.effective_chat.id, "not_admin")); return
        
        chat_id = str(update.effective_chat.id)
        settings = load_settings()
        
        # Clear warnings
        if "warnings" in settings and chat_id in settings["warnings"]:
            del settings["warnings"][chat_id]
        
        # Clear tracked members
        if "groups" in settings and chat_id in settings["groups"]:
            settings["groups"][chat_id]["members"] = []
            
        # Clear roulette stats
        if "roulette_stats" in settings and chat_id in settings["roulette_stats"]:
            del settings["roulette_stats"][chat_id]
            
        save_settings(settings)
        await update.message.reply_text("✅ **Group database cleared.**\nWarnings, tracked members, and game statistics have been reset.")
    except Exception as e:
        logger.error(f"Error in cleardata: {e}")

# --- GNEWS INTELLIGENCE FEED ---

_DEFAULT_NEWS_SOURCES = {
    "MCU / Cinema": [
        "https://news.google.com/rss/search?q=MCU+Marvel&hl=en-US&gl=US&ceid=US:en",
        "https://www.ign.com/rss/articles/movies",
        "https://thedirect.com/MCU/rss",
        "https://thedirect.com/movie/rss"
    ],
    "Gaming": [
        "https://www.ign.com/rss/articles/games",
        "https://www.saudigamer.com/category/%d8%a3%d8%ae%d8%a8%d8%a7%d8%b1/feed/",
        "https://www.saudigamer.com/category/%d9%85%d9%82%d8%a7%d9%84%d8%a7%d8%aa/feed/",
        "https://www.true-gaming.net/home/feed/"
    ],
    "Tech": [
        "https://www.theverge.com/rss/index.xml"
    ]
}

def _get_news_sources() -> dict:
    """Returns the active news sources — dynamic from settings, with hardcoded fallback."""
    settings = load_settings()
    custom = settings.get("news_sources")
    if custom and isinstance(custom, dict) and any(custom.values()):
        return custom
    return _DEFAULT_NEWS_SOURCES

# Keep NEWS_SOURCES as a module-level alias for backward compatibility with fetch_news references
NEWS_SOURCES = _DEFAULT_NEWS_SOURCES

def _get_news_targets() -> set:
    """Returns the set of chat IDs that should receive live news broadcasts."""
    settings = load_settings()
    custom_targets = settings.get("news_targets", [])
    if custom_targets:
        return set(int(t) for t in custom_targets)
    # Fallback to .env channels
    targets = set()
    if INTEL_CHANNEL:
        targets.add(int(INTEL_CHANNEL))
    elif LOG_CHANNEL:
        targets.add(int(LOG_CHANNEL))
    return targets

def _is_news_enabled() -> bool:
    """Check if live news posting is globally enabled."""
    settings = load_settings()
    return settings.get("news_enabled", True)

# --- NEWS CONTROL COMMANDS (Owner Only) ---

async def cmd_newsctl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Control live news posting: targets, enable/disable. Owner only."""
    if not await is_owner(update, context):
        await update.message.reply_text("❌ هذا الأمر خاص بالصانع فقط."); return
    
    args = context.args or []
    
    if not args:
        enabled = _is_news_enabled()
        targets = _get_news_targets()
        status_icon = "✅" if enabled else "❌"
        target_lines = []
        for t in sorted(targets):
            try:
                chat = await context.bot.get_chat(t)
                target_lines.append(f"  `{t}` — {chat.title or 'Private'}")
            except Exception:
                target_lines.append(f"  `{t}` — (غير متاح)")
        
        targets_str = "\n".join(target_lines) if target_lines else "  _لا يوجد_"
        
        await update.message.reply_text(
            f"**DeepScope — نظام البث المباشر**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 **الحالة:** {status_icon} {'مفعل' if enabled else 'معطل'}\n\n"
            f"🎯 **الأهداف (قنوات/مجموعات):**\n{targets_str}\n\n"
            f"**الأوامر:**\n"
            f"▸ `/gnewsctl on` — تفعيل البث\n"
            f"▸ `/gnewsctl off` — إيقاف البث\n"
            f"▸ `/gnewsctl add` — إضافة هذه الدردشة كهدف\n"
            f"▸ `/gnewsctl add [ID]` — إضافة دردشة بالمعرف\n"
            f"▸ `/gnewsctl remove` — إزالة هذه الدردشة\n"
            f"▸ `/gnewsctl remove [ID]` — إزالة دردشة بالمعرف",
            parse_mode="Markdown"
        ); return
    
    action = args[0].lower()
    settings = load_settings()
    
    if action == "on":
        settings["news_enabled"] = True
        save_settings(settings)
        await update.message.reply_text("✅ **البث المباشر مفعل.** غريس ستبث الأخبار تلقائياً.", parse_mode="Markdown")
    
    elif action == "off":
        settings["news_enabled"] = False
        save_settings(settings)
        await update.message.reply_text("❌ **البث المباشر معطل.** لن يتم نشر أي أخبار تلقائية.", parse_mode="Markdown")
    
    elif action == "add":
        target_id = int(args[1]) if len(args) > 1 and args[1].lstrip('-').isdigit() else update.effective_chat.id
        current = settings.get("news_targets", [])
        if target_id not in current:
            current.append(target_id)
            settings["news_targets"] = current
            save_settings(settings)
            try:
                chat = await context.bot.get_chat(target_id)
                name = chat.title or str(target_id)
            except Exception:
                name = str(target_id)
            await update.message.reply_text(f"✅ **تمت إضافة الهدف:**\n🎯 `{target_id}` — {name}", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ هذا الهدف موجود بالفعل.")
    
    elif action == "remove":
        target_id = int(args[1]) if len(args) > 1 and args[1].lstrip('-').isdigit() else update.effective_chat.id
        current = settings.get("news_targets", [])
        if target_id in current:
            current.remove(target_id)
            settings["news_targets"] = current
            save_settings(settings)
            await update.message.reply_text(f"✅ **تمت إزالة الهدف:** `{target_id}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ هذا الهدف غير موجود في القائمة.")
    
    else:
        await update.message.reply_text("⚠️ أمر غير معروف. استخدم `/gnewsctl` بدون معاملات للمساعدة.", parse_mode="Markdown")

async def cmd_newssrc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage RSS feed sources per sector. Owner only."""
    if not await is_owner(update, context):
        await update.message.reply_text("❌ هذا الأمر خاص بالصانع فقط."); return
    
    args = context.args or []
    sources = _get_news_sources()
    
    if not args:
        report = "**DeepScope — مصادر الأخبار**\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for sector, urls in sources.items():
            report += f"📁 **{sector}** ({len(urls)} مصدر)\n"
            for i, u in enumerate(urls, 1):
                clean_url = u.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
                if len(clean_url) > 40: clean_url = clean_url[:37] + "..."
                report += f"  {i}. `{clean_url}`\n"
            report += "\n"
        report += (
            "**الأوامر:**\n"
            "▸ `/gnewssrc add [sector] [rss_url]`\n"
            "▸ `/gnewssrc remove [sector] [rss_url]`\n"
            "▸ `/gnewssrc addsector [name]`\n"
            "▸ `/gnewssrc removesector [name]`\n"
            "▸ `/gnewssrc reset` — إعادة المصادر الافتراضية"
        )
        await update.message.reply_text(report, parse_mode="Markdown", disable_web_page_preview=True)
        return
    
    action = args[0].lower()
    settings = load_settings()
    
    if "news_sources" not in settings or not isinstance(settings.get("news_sources"), dict):
        settings["news_sources"] = copy.deepcopy(_DEFAULT_NEWS_SOURCES)
    
    if action == "add":
        if len(args) < 3:
            await update.message.reply_text("⚠️ **الاستخدام:** `/gnewssrc add [sector] [rss_url]`\nمثال: `/gnewssrc add Gaming https://example.com/feed/`", parse_mode="Markdown")
            return
        sector = args[1]
        url = args[2]
        matched = next((k for k in settings["news_sources"] if k.lower() == sector.lower()), None)
        if not matched:
            await update.message.reply_text(f"⚠️ القطاع `{sector}` غير موجود. استخدم `/gnewssrc addsector {sector}` أولاً.", parse_mode="Markdown")
            return
        if url not in settings["news_sources"][matched]:
            settings["news_sources"][matched].append(url)
            save_settings(settings)
            domain = url.split('/')[2] if len(url.split('/')) > 2 else url
            await update.message.reply_text(f"✅ **تمت إضافة المصدر:**\n📁 {matched} → `{domain}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ هذا المصدر موجود بالفعل.")
    
    elif action == "remove":
        if len(args) < 3:
            await update.message.reply_text("⚠️ **الاستخدام:** `/gnewssrc remove [sector] [rss_url]`", parse_mode="Markdown")
            return
        sector = args[1]
        url = args[2]
        matched = next((k for k in settings["news_sources"] if k.lower() == sector.lower()), None)
        if matched and url in settings["news_sources"][matched]:
            settings["news_sources"][matched].remove(url)
            save_settings(settings)
            await update.message.reply_text(f"✅ **تمت إزالة المصدر** من {matched}", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ المصدر غير موجود في هذا القطاع.")
    
    elif action == "addsector":
        if len(args) < 2:
            await update.message.reply_text("⚠️ **الاستخدام:** `/gnewssrc addsector [name]`", parse_mode="Markdown")
            return
        name = " ".join(args[1:])
        if name not in settings["news_sources"]:
            settings["news_sources"][name] = []
            save_settings(settings)
            await update.message.reply_text(f"✅ **تم إنشاء قطاع جديد:** 📁 {name}", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ هذا القطاع موجود بالفعل.")
    
    elif action == "removesector":
        if len(args) < 2:
            await update.message.reply_text("⚠️ **الاستخدام:** `/gnewssrc removesector [name]`", parse_mode="Markdown")
            return
        name = " ".join(args[1:])
        matched = next((k for k in settings["news_sources"] if k.lower() == name.lower()), None)
        if matched:
            del settings["news_sources"][matched]
            save_settings(settings)
            await update.message.reply_text(f"✅ **تم حذف القطاع:** {matched}", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ القطاع غير موجود.")
    
    elif action == "reset":
        settings["news_sources"] = copy.deepcopy(_DEFAULT_NEWS_SOURCES)
        save_settings(settings)
        await update.message.reply_text("✅ **تمت إعادة المصادر إلى الإعدادات الافتراضية.**", parse_mode="Markdown")
    
    else:
        await update.message.reply_text("⚠️ أمر غير معروف. استخدم `/gnewssrc` بدون معاملات للمساعدة.", parse_mode="Markdown")


def normalize_url(url: str) -> str:
    """Normalize a URL to prevent duplicates while preserving essential query parameters (like ?p= for True Gaming)."""
    if not url: return ""
    try:
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
        url = url.strip().rstrip('/')
        parsed = urlparse(url)
        
        if parsed.query:
            # Common tracking parameters to strip
            tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'fbclid', 'gclid', 'ref'}
            
            # Keep only non-tracking parameters
            query_params = parse_qsl(parsed.query, keep_blank_values=True)
            filtered_params = [(k, v) for k, v in query_params if k.lower() not in tracking_params]
            
            # Reconstruct the URL
            new_query = urlencode(filtered_params)
            parsed = parsed._replace(query=new_query)
            url = urlunparse(parsed)
            
    except Exception:
        pass
    return url.lower()


async def fetch_article_content(url: str) -> str:
    try:
        # H-04: Timeout handled by AsyncClient configuration
        
        # Use a real user agent to bypass basic anti-bot protections
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        async with _httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return ""
            
            soup = _BS(resp.text, 'html.parser')
            
            # Remove scripts, styles, and navigational elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
                element.decompose()
            
            # Target common article containers, fallback to body
            article = soup.find('article') or soup.find(class_='post-content') or soup.find(class_='entry-content') or soup.body
            
            if not article:
                return ""
            
            # Extract only paragraph text to get clean reading material
            paragraphs = article.find_all('p')
            text = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Limit payload to 8000 characters to protect Groq API token limits
            return text[:8000]
    except Exception as e:
        logger.warning(f"Error scraping article {url}: {e}")
        return ""


async def fetch_news(sector=None, limit_per_source=1):
    """Fetch news from all sources or a specific sector with cross-source deduplication."""
    grouped_news = {}
    sectors_to_fetch = [sector] if sector else _get_news_sources().keys()
    seen_in_fetch = set()
    
    for s in sectors_to_fetch:
        urls = _get_news_sources().get(s, [])
        sector_news = []
        for url in urls:
            try:
                # Detect source name from URL
                if "saudigamer" in url:
                    src = "Saudi Gamer 🎮"
                elif "ign.com" in url:
                    src = "IGN"
                elif "theverge.com" in url:
                    src = "The Verge"
                elif "true-gaming" in url:
                    src = "True Gaming"
                elif "thedirect.com" in url:
                    src = "The Direct"
                elif "news.google" in url:
                    src = "Google News"
                else:
                    src = "Global Intel"

                # H-01: Offload blocking RSS parsing to a thread to keep event loop alive
                feed = await asyncio.to_thread(feedparser.parse, url)
                for entry in feed.entries[:limit_per_source]:
                    norm_link = normalize_url(entry.link)
                    if norm_link in seen_in_fetch:
                        continue
                    seen_in_fetch.add(norm_link)

                    # Extract rich metadata
                    author = entry.get("author") or entry.get("dc_creator") or "—"
                    
                    # Parse date into clean format
                    raw_date = entry.get("published") or entry.get("pubDate") or ""
                    try:
                        if entry.get("published_parsed"):
                            import time as _t
                            clean_date = _t.strftime("%Y-%m-%d", entry.published_parsed)
                        else:
                            clean_date = raw_date[:16] if raw_date else "—"
                    except Exception:
                        clean_date = raw_date[:16] if raw_date else "—"
                    
                    content = entry.get("content", [{"value": ""}])[0].get("value") or entry.get("summary", "")
                    
                    # --- DEEPSCOPE ENHANCEMENT: Full Article Scraping ---
                    if "saudigamer" in url or "true-gaming" in url:
                        scraped_content = await fetch_article_content(entry.link)
                        if scraped_content:
                            content = scraped_content

                    sector_news.append({
                        "title": entry.title,
                        "link": entry.link,
                        "norm_link": norm_link,
                        "id": entry.get("id") or norm_link,
                        "author": author,
                        "date": clean_date,
                        "content": content,
                        "source_name": src
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch news from {url}: {e}")
        if sector_news:
            grouped_news[s] = sector_news
    return grouped_news

def clean_ai_arabic_text(text: str) -> str:
    """Aggressively purge any characters that are NOT standard Arabic, English, Numbers, or Emojis."""
    if not text: return text
    
    # 1. Strict Whitelist: ONLY Arabic letters, English letters, Numbers, and basic punctuation.
    # We REMOVED \w and \d because they can include international characters in Unicode mode.
    whitelist_pattern = _re.compile(r'[^a-zA-Z0-9\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s\.\!\?\:\(\)\[\]\-\_\,\/\@\#\$\%\^\&\*\+\=\>\<\"\'\u2600-\u27BF\U0001f300-\U0001faff]', _re.UNICODE)
    text = whitelist_pattern.sub('', text)
    
    # 2. Standardize character variants
    replacements = {'چ': 'ج', 'پ': 'ب', 'ژ': 'ز', 'ڤ': 'ف', 'گ': 'ك', 'ڨ': 'ق'}
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    return text.strip()

def clean_markdown(text: str) -> str:
    """Escapes or removes stray markdown characters to prevent parsing errors."""
    if not text: return ""
    # Characters that break Markdown in Telegram: * _ ` [ > <
    # We replace them with their standard look-alikes or escape them
    return text.replace("*", "").replace("_", " ").replace("`", "'").replace("[", "(").replace("]", ")").replace(">", "").replace("<", "")


async def summarize_intel_report(title: str, content: str, is_ar: bool = True, author: str = "—", date: str = "—", source: str = "—") -> str:
    """Grace Ashcroft professional AI summary of a news report."""
    if not GROQ_API_KEY or not content:
        return "Analysis pending: Source content too brief for forensic summary."
    
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        system_prompt = (
            "أنت غريس أشكروفت، محللة تقنية متخصصة في تغطية أخبار الألعاب والتقنية (DeepScope Analyst). "
            "مهمتك هي تقديم ملخص استخباراتي مهني للمقال المذكور. "
            "الأسلوب المتبع: تقرير جنائي (Case Brief)، دقيق، موضوعي، مع لمسة بسيطة من القلق والتركيز المفرط على البيانات. "
            "STRICT CHARACTER RULE: استخدم فقط الحروف العربية الأساسية. لا تستخدم 'چ' أو 'پ' أو 'گ'. "
            "مهم جداً: ابدأ فوراً بتلخيص المحتوى مباشرة وبدون أي مقدمة أو تمهيد (ممنوع كتابة 'هذا ملخص استخباراتي للمقال:' أو أي عبارة مشابهة). "
            "اذكر النقاط الرئيسية في 3 إلى 5 جمل مهنية."
        )
        
        user_context = f"Source: {source}\nTitle: {title}\nAuthor: {author}\nDate: {date}\n\nContent: {content[:4000]}"
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context}
            ],
            "temperature": 0.5,
            "max_tokens": 800
        }
        
        async with _httpx.AsyncClient(timeout=40.0, trust_env=False) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                summary = resp.json()["choices"][0]["message"]["content"]
                return clean_ai_arabic_text(summary)
            elif resp.status_code == 429:
                logger.warning("Primary Groq model rate limited. Attempting 8b fallback...")
                payload["model"] = "llama-3.1-8b-instant"
                resp_fb = await client.post(url, headers=headers, json=payload)
                if resp_fb.status_code == 200:
                    summary = resp_fb.json()["choices"][0]["message"]["content"]
                    return clean_ai_arabic_text(summary) + "\n\n_(تنبيه: تم استخدام المحرك الاحتياطي بسبب ضغط العمليات)_"
            
            logger.error(f"Groq API Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        err_str = str(e)
        if "getaddrinfo failed" not in err_str and "ConnectError" not in err_str:
            logger.error(f"Summarization error: {e}")
    return "Error during intelligence processing. Please refer to the source link."

async def cmd_news_sector(update: Update, context: ContextTypes.DEFAULT_TYPE, sector: str, banner_file: str):
    """Unified handler for visual-rich sector news."""
    chat_id = update.effective_chat.id
    # Global Lock Check
    if reason := get_lock_reason("gnews"):
        await update.message.reply_text(get_phrase(chat_id, "lock_denied_generic", reason=reason), parse_mode="Markdown")
        return

    is_ar = get_group_settings(chat_id).get("dialect", DEFAULT_DIALECT) == "arabic_fousha"
    status = await update.message.reply_text("📡 " + ("جاري تحضير التقرير المرئي..." if is_ar else "Preparing visual report..."))
    
    grouped_news = await fetch_news(sector=sector, limit_per_source=3)
    if not grouped_news or sector not in grouped_news:
        await status.edit_text("❌ " + ("لا توجد بيانات متاحة حالياً." if is_ar else "No data available at this time."))
        return

    # Mapping for Sector Headers in Arabic
    sector_ar = {
        "MCU / Cinema": "السينما ومارفل",
        "Gaming": "الألعاب والجيمنج",
        "Tech": "التقنية والتكنولوجيا"
    }
    
    header = sector_ar.get(sector, sector) if is_ar else sector
    report = f"📰 <b>REPORT: {header.upper()}</b>\n━━━━━━━━━━━━━━━\n\n"
    
    import html as _html
    for item in grouped_news[sector]:
        safe_t = _html.escape(item['title'])
        safe_l = _html.escape(item['link'])
        report += f"▸ <b><a href=\"{safe_l}\">{safe_t}</a></b>\n\n"
    
    report += "━━━━━━━━━━━━━━━\n<i>" + ("تم إنهاء التحليل. — غريس" if is_ar else "Analysis complete. — Grace") + "</i> 📋"

    try:
        # Check for deepscope_frame.png in avatar first, then the master banner, then sector specific
        banners = ["avatar/deepscope_frame.png", "avatar/news_default.jpg", f"avatar/{banner_file}"]
        final_banner = next((b for b in banners if os.path.exists(b)), None)
        
        if final_banner:
            with open(final_banner, 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=report,
                    parse_mode="HTML"
                )
            await status.delete()
        else:
            # Fallback if no images are found
            await status.edit_text(report, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error sending visual news: {e}")
        await status.edit_text(report, parse_mode="HTML", disable_web_page_preview=True)

async def cmd_news_gaming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_news_sector(update, context, "Gaming", "news_gaming.png")

async def cmd_news_mcu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_news_sector(update, context, "MCU / Cinema", "news_mcu.png")

async def cmd_news_tech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_news_sector(update, context, "Tech", "news_tech.png")

async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual trigger to see the latest intelligence brief by sector (Visual)."""
    chat_id = update.effective_chat.id
    # Global Lock Check
    if reason := get_lock_reason("gnews"):
        await update.message.reply_text(get_phrase(chat_id, "lock_denied_generic", reason=reason), parse_mode="Markdown")
        return

    is_ar = get_group_settings(chat_id).get("dialect", DEFAULT_DIALECT) == "arabic_fousha"
    status = await update.message.reply_text("📡 " + ("جاري سحب آخر التقارير الاستخباراتية..." if is_ar else "Fetching latest intelligence reports..."))
    
    grouped_news = await fetch_news(limit_per_source=1)
    if not grouped_news:
        await status.edit_text("❌ " + ("لا توجد تقارير جديدة حالياً." if is_ar else "No new reports found at this time."))
        return

    report = ("📡 **موجز الاستخبارات — القطاعات النشطة**\n━━━━━━━━━━━━━━━\n\n" if is_ar else "📡 **INTELLIGENCE BRIEF — ACTIVE SECTORS**\n━━━━━━━━━━━━━━━\n\n")
    
    # Mapping for Sector Headers in Arabic
    sector_ar = {
        "MCU / Cinema": "السينما ومارفل",
        "Gaming": "الألعاب والجيمنج",
        "Tech": "التقنية والتكنولوجيا"
    }

    for sector, items in grouped_news.items():
        header = sector_ar.get(sector, sector) if is_ar else sector
        report += f"📁 **{header.upper()}**\n"
        for item in items:
            report += f"▸ [{item['title']}]({item['link']})\n"
        report += "\n"
    
    footer = "تم إنهاء الموجز. — غريس" if is_ar else "Brief complete. — Grace"
    report += "━━━━━━━━━━━━━━━\n_" + footer + "_ 📋"
    
    try:
        # Priority: avatar/deepscope_frame.png > avatar/news_default.jpg
        banners = ["avatar/deepscope_frame.png", "avatar/news_default.jpg"]
        final_banner = next((b for b in banners if os.path.exists(b)), None)
        
        if final_banner:
            with open(final_banner, 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=report,
                    parse_mode="Markdown"
                )
            await status.delete()
        else:
            await status.edit_text(report, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in visual gnews: {e}")
        await status.edit_text(report, parse_mode="Markdown", disable_web_page_preview=True)

async def news_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check for new posts and deliver to configured targets."""
    # Check if live posting is enabled
    if not _is_news_enabled():
        return
    
    # Get targets from dynamic config
    targets = _get_news_targets()
    if not targets:
        return
    
    settings = load_settings()
    # H-03: Use sets for O(1) deduplication instead of O(n) list searches
    last_ids_set = set(settings.get("last_news_ids", []))
    last_titles_set = set(settings.get("last_news_titles", []))
    
    grouped_news = await fetch_news(limit_per_source=2)
    
    # Processed in this run to avoid duplicates if same news appears across different sectors/feeds
    processed_now = set()
    
    for sector, items in grouped_news.items():
        for item in items:
            item_id = str(item["id"])
            norm_link = item.get("norm_link", normalize_url(item["link"]))
            item_title = item["title"].strip()
            
            # Stricter Deduplication: Check ID, Normalized Link, AND Title
            if (item_id not in last_ids_set and 
                norm_link not in last_ids_set and 
                item_title not in last_titles_set and
                norm_link not in processed_now):
                
                logger.info(f"📡 DeepScope: New broadcast detected: {item_title}")
                processed_now.add(norm_link)
                
                # Perform AI Summarization for Saudi Gamer or high-priority items
                summary = ""
                if "saudigamer" in item["link"].lower() or "true-gaming" in item["link"].lower() or "thedirect.com" in item["link"].lower():
                    summary = await summarize_intel_report(
                        item["title"], item["content"], is_ar=True, 
                        author=item['author'], date=item['date'], source=item['source_name']
                    )
                
                # Build clean report
                import html as _html
                title_line = item['title']
                source_name = item.get('source_name', 'News')
                
                safe_title = _html.escape(title_line)
                safe_summary = _html.escape(summary) if summary else ""
                safe_source = _html.escape(source_name)
                safe_link = _html.escape(item['link'])
                
                alert = f"<b>{safe_title}</b>\n\n"
                
                if safe_summary:
                    alert += f"{safe_summary}\n\n"
                    
                alert += f"🌐 <b>{safe_source}</b> • 📋 <a href=\"{safe_link}\">اقرأ التفاصيل</a>"
                # Broadcast to all unique targets
                for target_id in targets:
                    try:
                        await context.bot.send_message(target_id, alert, parse_mode="HTML", disable_web_page_preview=False)
                    except Exception as e:
                        err_str = str(e)
                        if "getaddrinfo failed" not in err_str and "ConnectError" not in err_str:
                            logger.error(f"Failed to post news alert to {target_id}: {e}")
                
                # Update sets and lists
                last_ids_set.add(item_id)
                last_ids_set.add(norm_link)
                last_titles_set.add(item_title)
                
                # Convert back to lists and Prune history to keep JSON manageable (H-03)
                settings["last_news_ids"] = list(last_ids_set)[-600:]
                settings["last_news_titles"] = list(last_titles_set)[-300:]
                save_settings(settings)
                
                await asyncio.sleep(5) # Throttle to prevent flooding

async def cmd_getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple command to get the current chat ID."""
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Private Chat"
    await update.message.reply_text(f"📍 **DeepScope Location Data**\n━━━━━━━━━━━━━━━\n🏷️ **Title:** `{chat_title}`\n🆔 **Chat ID:** `{chat_id}`\n\n_Use this ID with /gsetlog to route intelligence reports here._", parse_mode="Markdown")

async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch any article URL, extract metadata, and generate an Arabic AI summary."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Permission Check
    if user_id != MASTER_ID and user_id != OWNER_ID:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["administrator", "creator"]:
            return # Silent ignore
    
    # Check for URL argument
    if not context.args:
        await update.message.reply_text(
            "📝 **طريقة الاستخدام:**\n"
            "`/gsum [رابط المقال]`\n\n"
            "**مثال:**\n"
            "`/gsum https://www.saudigamer.com/example-post/`\n\n"
            "_غريس ستقوم بتحليل المقال وتلخيصه بالعربية._ 📋",
            parse_mode="Markdown"
        ); return
    
    url = context.args[0]
    if not url.startswith("http"):
        await update.message.reply_text("❌ الرابط غير صالح. يرجى إرسال رابط يبدأ بـ http أو https."); return
    
    status = await update.message.reply_text("🔄 **جاري تحليل المقال...**\n_يتم الآن جمع البيانات من المصدر._", parse_mode="Markdown")
    
    try:
        # Fetch the page
        async with _httpx.AsyncClient(timeout=20.0, follow_redirects=True, trust_env=False) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            if resp.status_code != 200:
                await status.edit_text(f"❌ فشل الاتصال بالمصدر. (HTTP {resp.status_code})"); return
            html = resp.text
        
        soup = _BS(html, "html.parser")
        
        # Extract title
        og_title = soup.find("meta", property="og:title")
        title = og_title["content"] if og_title else (soup.title.string if soup.title else "بدون عنوان")
        
        # Extract author
        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        author_el = soup.find("a", rel="author") or soup.find(class_=_re.compile(r'author', _re.IGNORECASE))
        if author_meta:
            author = author_meta.get("content", "—")
        elif author_el:
            author = author_el.get_text(strip=True)
        else:
            author = "—"
        
        # Extract date
        date_meta = soup.find("meta", property="article:published_time") or soup.find("time")
        if date_meta:
            raw_date = date_meta.get("content") or date_meta.get("datetime") or date_meta.get_text(strip=True)
            pub_date = raw_date[:10] if raw_date else "—"
        else:
            pub_date = "—"
        
        # Extract source name
        og_site = soup.find("meta", property="og:site_name")
        source_name = og_site["content"] if og_site else url.split("/")[2]
        
        # Extract article content for summarization (Improved Filtering)
        article_el = soup.find("article") or soup.find(class_=_re.compile(r'post-content|entry-content|article-body|main-content', _re.IGNORECASE))
        if article_el:
            # Only remove the most obvious noise to avoid deleting content
            for tag in article_el.find_all(["script", "style", "nav", "footer", "form"]):
                tag.decompose()
            content = article_el.get_text(separator="\n", strip=True)
        else:
            # Fallback: grab paragraphs but filter out short "menu-like" text
            paragraphs = []
            for p in soup.find_all("p"):
                p_text = p.get_text(strip=True)
                if len(p_text) > 40: # Only keep substantial paragraphs
                    paragraphs.append(p_text)
            content = "\n".join(paragraphs[:15])
        
        if not content or len(content) < 50:
            await status.edit_text("❌ لم يتم العثور على محتوى كافٍ للتحليل في هذا الرابط."); return
        
        # AI Summary
        summary = await summarize_intel_report(title, content, is_ar=True)
        summary = clean_ai_arabic_text(summary)
        
        import html as _html
        safe_title = _html.escape(title)
        safe_author = _html.escape(author)
        safe_source = _html.escape(source_name)
        safe_summary = _html.escape(summary)

        meta_info = f"👤 <code>{safe_author}</code>\n📅 <code>{pub_date}</code>  |  🏢 <code>{safe_source}</code>"
        
        report = (
            f"<b>{safe_title}</b>\n\n"
            f"{meta_info}\n\n"
            f"🌐 <a href=\"{url}\">اضغط هنا لفتح المقال الكامل</a>\n\n"
            f"📝 <b>ملخص غريس أشكروفت:</b>\n"
            f"{safe_summary}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"غريس أشكروفت — DeepScope 📋"
        )
        
        try:
            await status.edit_text(report, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            logger.warning(f"HTML parsing failed: {e}")
            await status.edit_text(report.replace("<b>", "").replace("</b>", ""), disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Error in cmd_summary: {e}")
        await status.edit_text(f"❌ حدث خطأ أثناء تحليل المقال.\n`{str(e)[:100]}`", parse_mode="Markdown")

async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deep Forensic Analysis protocol (/gana). Much more detailed than /gsum."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Permission Check
    if user_id != MASTER_ID and user_id != OWNER_ID:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["administrator", "creator"]:
            return # Silent ignore
    
    # 1. Input Validation
    input_content = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        input_content = update.message.reply_to_message.text
    elif context.args:
        input_content = " ".join(context.args)
    else:
        await update.message.reply_text(
            "🧪 **بروتوكول التحليل العميق — /gana**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "يرجى توفير رابط أو نص للتحليل الشامل.\n\n"
            "**طرق الاستخدام:**\n"
            "▸ `/gana [النص هنا]`\n"
            "▸ `/gana [رابط المقال]`\n"
            "▸ الرد على أي رسالة بـ `/gana`\n\n"
            "_سأقوم بإجراء فحص استخباراتي دقيق وشامل._ 📋",
            parse_mode="Markdown"
        ); return

    status = await update.message.reply_text("🔬 **جاري تفعيل بروتوكول DeepScope...**\n_بدء عملية التحليل الجنائي الشامل._", parse_mode="Markdown")

    try:
        source_info = "بيانات مباشرة"
        # Check if input is a URL
        if input_content.startswith("http"):
            url = input_content.split()[0]
            async with _httpx.AsyncClient(timeout=20.0, follow_redirects=True, trust_env=False) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                if resp.status_code == 200:
                    soup = _BS(resp.text, "html.parser")
                    # Meta Data
                    og_site = soup.find("meta", property="og:site_name")
                    source_info = og_site["content"] if og_site else url.split("/")[2]
                    # Content
                    article_el = soup.find("article") or soup.find(class_=_re.compile(r'post-content|entry-content|article-body', _re.IGNORECASE))
                    if article_el:
                        input_content = article_el.get_text(separator="\n", strip=True)
                    else:
                        input_content = "\n".join(p.get_text(strip=True) for p in soup.find_all("p")[:20])
        
        # 2. Deep Analysis AI Logic
        system_prompt = (
            "You are Grace Ashcroft, a Senior Technical Intelligence Analyst for DeepScope. "
            "Your task is to provide a 'Deep Forensic Analysis' (تحليل تقني جنائي) in professional Arabic Fousha. "
            "STRICT CHARACTER RULE: Use ONLY the standard 28 Arabic letters. NEVER use 'چ', 'پ', 'گ'. "
            "STRICT TONE: Clinical, expert, highly critical. Use words like 'تقييم الأثر', 'مستوى الاختراق', 'البيانات الخام'. "
            "DO NOT USE Markdown headers like '###'. Use the following format precisely:\n\n"
            "📋 **الملخص التنفيذي:** [Brief, high-level overview]\n\n"
            "🔬 **التحليل الفني الجنائي:** [Deep forensic dive into the content]\n\n"
            "🎯 **التداعيات الاستراتيجية:** [Future market/industry impact]\n\n"
            "Ensure the output is clean and highly professional."
        )
        
        user_prompt = f"Target Data for Analysis:\nSource: {source_info}\n\nContent:\n{input_content[:5000]}"
        
        analysis = await ask_groq(user_prompt, chat_history=[{"role": "system", "content": system_prompt}])
        analysis = clean_ai_arabic_text(analysis)
        
        if not analysis:
            await status.edit_text("❌ فشل النظام في توليد التقرير. يرجى المحاولة لاحقاً."); return

        # 3. Format Final Report
        import random, string, html as _html
        case_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        timestamp = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        safe_source = _html.escape(source_info)
        
        # Format bold tags into HTML <b>
        html_analysis = _html.escape(analysis)
        html_analysis = _re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_analysis)
        
        header = (
            f"🔐 <b>DEEPSCOPE CLASSIFIED — ملف استخباراتي</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>Case ID:</b> <code>{case_id}</code>\n"
            f"🕒 <b>Timestamp:</b> <code>{timestamp}</code>\n"
            f"🎚️ <b>Clearance:</b> <code>Level 4 (Analyst Only)</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        report = (
            f"{header}"
            f"{html_analysis}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>مصدر البيانات:</b> <code>{safe_source}</code>\n"
            f"✅ <b>الحالة:</b> <code>ملف مكتمل ومؤرشف</code>\n"
            f"<i>غريس أشكروفت — المحللة التقنية المركزية</i> 📋"
        )
        
        try:
            await status.edit_text(report, parse_mode="HTML")
        except Exception:
            await status.edit_text(report.replace("<b>", "").replace("</b>", ""))

    except Exception as e:
        logger.error(f"Error in cmd_analyze: {e}")
        await status.edit_text(f"💥 **فشل في بروتوكول التحليل.**\n`{str(e)[:100]}`", parse_mode="Markdown")

async def cmd_edit_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows admins to edit Grace's messages by replying to them with /gedit [text]."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 1. Permission Check
    if user_id != MASTER_ID and user_id != OWNER_ID:
        # Check if user is an admin in the group
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["administrator", "creator"]:
            return # Silent ignore for non-admins

    # 2. Reply Check
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ يرجى الرد على الرسالة التي ترغب في تعديلها بـ `/gedit [النص الجديد]`.", parse_mode="Markdown")
        return

    target_msg = update.message.reply_to_message
    if target_msg.from_user.id != context.bot.id:
        await update.message.reply_text("❌ لا يمكنني تعديل سوى الرسائل التي قمتُ بإرسالها بنفسي.", parse_mode="Markdown")
        return

    # 3. Content Check
    if not context.args:
        await update.message.reply_text("❌ يرجى توفير النص الجديد بعد الأمر.", parse_mode="Markdown")
        return

    new_text = " ".join(context.args)
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=target_msg.message_id,
            text=new_text,
            parse_mode="Markdown"
        )
        # Delete the trigger command to keep chat clean
        await update.message.delete()
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        await update.message.reply_text(f"⚠️ فشل التعديل: `{e}`", parse_mode="Markdown")

async def cmd_forcesync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger the news job and AI summarization (Owner only)."""
    if update.effective_user.id != MASTER_ID and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ صلاحية مرفوضة."); return
    
    await update.message.reply_text("🔄 **جاري بدء المسح الاستخباراتي...**\n_يتم الآن فحص المصادر وتحليل البيانات._", parse_mode="Markdown")
    await news_job(context)
    await update.message.reply_text("✅ **اكتمل المسح.**\n_يرجى مراجعة قناة التقارير للحصول على المستجدات._", parse_mode="Markdown")


async def cmd_clearchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        # Global Lock Check
        if reason := get_lock_reason("gclearchat"):
            await update.message.reply_text(get_phrase(chat_id, "lock_denied_gclearchat", reason=reason), parse_mode="Markdown")
            return

        if not await is_admin(update, context):
            await update.message.reply_text("❌ Admin-only command."); return
            
        current_msg_id = update.message.message_id
        progress = await update.message.reply_text(f"🗑️ **Initiating total message wipe...**\n_Scanning all {current_msg_id} historical messages..._", parse_mode="Markdown")
        
        # Generator for all historical message IDs to save memory
        ids_to_delete = range(current_msg_id, 0, -1)
        
        BATCH = 100
        for i in range(0, len(ids_to_delete), BATCH):
            batch = list(ids_to_delete[i: i + BATCH])
            try:
                await context.bot.delete_messages(chat_id=chat_id, message_ids=batch)
            except Exception:
                pass
            # Avoid Telegram rate limits
            await asyncio.sleep(1.0)
            
        _chat_msg_buffer[chat_id] = deque(maxlen=5000)
        
        try:
            await progress.edit_text(
                f"🗑️ **Chat Cleared**\n━━━━━━━━━━━━━━━\n✅ Scanned and deleted all {current_msg_id} historical messages.\n⏱️ This message deletes in 10 seconds.",
                parse_mode="Markdown"
            )
            await asyncio.sleep(10)
            await progress.delete()
        except Exception: pass
    except Exception as e:
        logger.error(f"Error in clearchat: {e}")

# --- NOTIFYALL ---

async def cmd_notifyall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        # Global Lock Check
        if reason := get_lock_reason("gnotifyall"):
            await update.message.reply_text(get_phrase(chat_id, "lock_denied_gnotifyall", reason=reason), parse_mode="Markdown")
            return

        if not await is_admin(update, context):
            await update.message.reply_text("❌ Admin-only command."); return
        chat_id = update.effective_chat.id
        settings = load_settings()
        member_ids = settings.get("groups", {}).get(str(chat_id), {}).get("members", [])
        if not member_ids:
            await update.message.reply_text("⚠️ No tracked members yet. Members must send at least one message first."); return
        caption = " ".join(context.args) if context.args else random.choice([
            "📢 Attention required. Please check the group. _— Grace_",
            "⚡ Group announcement. _— Grace Ashcroft_",
            "👀 Grace needs everyone's attention. Now.",
        ])
        BATCH = 30
        total = len(member_ids)
        await update.message.reply_text(f"📢 Notifying {total} members...")
        for batch_start in range(0, total, BATCH):
            batch_ids = member_ids[batch_start: batch_start + BATCH]
            parts = []
            for uid in batch_ids:
                try:
                    member = await context.bot.get_chat_member(chat_id, uid)
                    name = member.user.first_name or str(uid)
                except Exception:
                    name = str(uid)
                parts.append(f'<a href="tg://user?id={uid}">{name}</a>')
            mention_block = "  ".join(parts)
            if batch_start == 0:
                msg_text = f"<b>{caption}</b>\n\n{mention_block}"
            else:
                msg_text = mention_block
            await update.message.reply_text(msg_text, parse_mode="HTML")
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"Error in notifyall: {e}")

# --- CAPTCHA CALLBACK ---

async def captcha_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query: return
    await query.answer()
    try:
        data = query.data
        if not data.startswith("captcha_"): return
        parts = data.split("_")
        target_uid = int(parts[1])
        chosen = int(parts[2])
        correct = int(parts[3])
        clicker_id = query.from_user.id
        if clicker_id != target_uid:
            await query.answer("This captcha isn't for you.", show_alert=True); return
        chat_id = pending_captcha.get(target_uid, {}).get("chat_id", query.message.chat_id)
        if chosen == correct:
            await context.bot.restrict_chat_member(chat_id, target_uid, permissions=ChatPermissions(
                can_send_messages=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False, can_invite_users=False
            ))
            await query.edit_message_text(f"✅ {query.from_user.first_name} — verified. Welcome. 📋")
            await log_event(context, "captcha_pass", query.message.chat.title, "Grace", query.from_user.first_name)
        else:
            await context.bot.ban_chat_member(chat_id, target_uid)
            await context.bot.unban_chat_member(chat_id, target_uid)
            await query.edit_message_text(f"❌ {query.from_user.first_name} — wrong answer. Removed automatically.\n_Correct was: {correct}_")
            await log_event(context, "captcha_fail", query.message.chat.title, "Grace", query.from_user.first_name)
        pending_captcha.pop(target_uid, None)
    except Exception as e:
        logger.error(f"Error in captcha_callback: {e}")

# --- GENERAL CALLBACK HANDLER (unmute) ---

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query: return
    try:
        data = query.data
        if data == "gstatus_refresh":
            chat_id = query.message.chat.id
            status_text, keyboard = await build_status_message(chat_id)
            try:
                await query.edit_message_text(status_text, parse_mode="Markdown", reply_markup=keyboard)
                await query.answer("✅ Status refreshed!")
            except Exception as ex:
                if "Message is not modified" in str(ex):
                    await query.answer("✅ Status is up to date!")
                else:
                    await query.answer()
                    logger.error(f"Error refreshing status callback: {ex}")
            return

        if data == "gstats_refresh":
            chat_id = query.message.chat.id
            chat = query.message.chat
            if chat.type == "private":
                member_count = 1
                admins = []
            else:
                try:
                    member_count = await context.bot.get_chat_member_count(chat_id)
                except Exception:
                    member_count = 1
                try:
                    admins = await context.bot.get_chat_administrators(chat_id)
                except Exception:
                    admins = []

            group_settings = get_group_settings(chat_id)
            stats_text, keyboard = await build_stats_message(chat, chat_id, member_count, admins, group_settings)
            try:
                await query.edit_message_text(stats_text, parse_mode="Markdown", reply_markup=keyboard)
                await query.answer("✅ Stats refreshed!")
            except Exception as ex:
                if "Message is not modified" in str(ex):
                    await query.answer("✅ Stats are up to date!")
                else:
                    await query.answer()
                    logger.error(f"Error refreshing stats callback: {ex}")
            return

        await query.answer()
        if data.startswith("unmute_"):
            parts = data.split("_")
            chat_id = int(parts[1])
            user_id = int(parts[2])
            if not await is_admin(update, context):
                await query.answer("❌ Only admins can lift restrictions.", show_alert=True); return
            await context.bot.restrict_chat_member(chat_id, user_id, permissions=ChatPermissions(
                can_send_messages=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True, can_change_info=False, can_invite_users=False
            ))
            try:
                member = await context.bot.get_chat_member(chat_id, user_id)
                name = member.user.first_name or str(user_id)
            except Exception:
                name = str(user_id)
            try:
                await query.edit_message_caption(
                    caption=(query.message.caption or "") + f"\n\n✅ Restriction lifted by {query.from_user.first_name}.",
                    parse_mode="Markdown"
                )
            except Exception:
                await query.edit_message_text(
                    text=(query.message.text or "") + f"\n\n✅ Restriction lifted by {query.from_user.first_name}.",
                    parse_mode="Markdown"
                )
            logger.info(f"User {user_id} in {chat_id} unmuted by {query.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_handler: {e}")

# --- ERROR HANDLER ---

async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore common intermittent network errors that Telegram automatically recovers from
    err_str = str(context.error)
    if any(e in err_str for e in ["httpx.ReadError", "httpx.RemoteProtocolError", "httpx.ConnectError", "getaddrinfo failed"]):
        return
    logger.error(f"Update {update} caused error: {context.error}", exc_info=True)

# --- CORE SYSTEM INITIALIZATION ---

# --- MAIN ---

def main():
    _print_banner()
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Bot token not set. Edit .env file.")
        return

    logger.info("📋 Starting Grace Ashcroft Bot...")

    try:


        proxy_url = GRACE_PROXY if GRACE_PROXY and GRACE_PROXY.strip() else None
        
        # Isolation Protocol: Ensure we don't pick up conflicting system proxies if GRACE_PROXY is empty
        request = HTTPXRequest(
            connect_timeout=300, 
            read_timeout=300, 
            write_timeout=300,
            pool_timeout=120, 
            connection_pool_size=100, 
            proxy=proxy_url
        )
        app = ApplicationBuilder().token(TOKEN).request(request).build()

        # Commands

        # Commands
        app.add_handler(CommandHandler("gcmd",          cmd_gcmd))
        app.add_handler(CommandHandler("gstart",        cmd_start))
        app.add_handler(CommandHandler("gabout",        cmd_about))
        app.add_handler(CommandHandler("gstatus",       cmd_status))
        app.add_handler(CommandHandler("ghelp",         cmd_help))
        app.add_handler(CommandHandler("grules",        cmd_rules))
        app.add_handler(CommandHandler("gsetwlc",       cmd_setwlc))
        app.add_handler(CommandHandler("gsetfrw",       cmd_setfrw))
        app.add_handler(CommandHandler("gsetwarn",      cmd_setwarn))
        app.add_handler(CommandHandler("gsetmute",      cmd_setmute))
        app.add_handler(CommandHandler("gsetkick",      cmd_setkick))
        app.add_handler(CommandHandler("gsetban",       cmd_setban))
        app.add_handler(CommandHandler("gsetrules",     cmd_setrules))
        app.add_handler(CommandHandler("glang",         cmd_setlang))
        app.add_handler(CommandHandler("ggai",         cmd_toggle_ai))
        app.add_handler(CommandHandler("glinkfilter",   cmd_linkfilter))
        app.add_handler(CommandHandler("gspamfilter",   cmd_spamfilter))
        app.add_handler(CommandHandler("grepeatfilter", cmd_repeatfilter))
        app.add_handler(CommandHandler("gcaptcha",      cmd_captcha))
        app.add_handler(CommandHandler("gtoggleapply",  cmd_toggleapply))
        app.add_handler(CommandHandler("gcleardata",    cmd_cleardata))
        app.add_handler(CommandHandler("gclearchat",    cmd_clearchat))
        app.add_handler(CommandHandler("gapply",        cmd_apply))
        app.add_handler(CommandHandler("gumbrella",     cmd_umbrella))
        app.add_handler(CommandHandler("a",             cmd_umbrella))
        # Umbrella trigger words
        app.add_handler(MessageHandler(filters.Regex(_re.compile(r'^(امبريلا|أمبريلا|روليت|مظله|مظلة|ا|umbrella|roulette|a)$', _re.IGNORECASE)), cmd_umbrella))
        # Umbrella Help Trigger Words
        app.add_handler(MessageHandler(filters.Regex(_re.compile(r'^(شرح الروليت|قوانين الروليت|غريس اشرحي اللعبه|غريس اشرحي اللعبة|how to play roulette|roulette rules)$', _re.IGNORECASE)), cmd_explain_umbrella))
        app.add_handler(CommandHandler("gadmins",       cmd_admins))
        app.add_handler(CommandHandler("ginfo",         cmd_info))
        app.add_handler(CommandHandler("getid",         cmd_getid))
        app.add_handler(CommandHandler("gstats",        cmd_stats))
        app.add_handler(CommandHandler("gsetlog",       cmd_setlog))
        app.add_handler(CommandHandler("gpromote",      cmd_promote))
        app.add_handler(CommandHandler("gdemote",       cmd_demote))
        app.add_handler(CommandHandler("gwarn",         cmd_warn))
        app.add_handler(CommandHandler("gmute",         cmd_mute))
        app.add_handler(CommandHandler("gkick",         cmd_kick))
        app.add_handler(CommandHandler("gban",          cmd_ban))
        app.add_handler(CommandHandler("gsource",       cmd_source))
        app.add_handler(CommandHandler("gantibot",      cmd_antibot))
        app.add_handler(CommandHandler("gcleanservice", cmd_cleanservice))
        app.add_handler(CommandHandler("gin",          cmd_toggle_in))
        app.add_handler(CommandHandler("gout",         cmd_toggle_out))
        app.add_handler(CommandHandler("gnotifyall",    cmd_notifyall))
        app.add_handler(CommandHandler("glock",        cmd_glock))
        app.add_handler(CommandHandler("gunlock",      cmd_gunlock))
        app.add_handler(CommandHandler("gmenu",        cmd_start))
        app.add_handler(CommandHandler("start",        cmd_start))
        app.add_handler(CommandHandler("gnews",        cmd_news))
        app.add_handler(CommandHandler("ggame",        cmd_news_gaming))
        app.add_handler(CommandHandler("gmcu",         cmd_news_mcu))
        app.add_handler(CommandHandler("gtech",        cmd_news_tech))
        app.add_handler(CommandHandler("gforcesync",    cmd_forcesync))
        app.add_handler(CommandHandler("gsum",          cmd_summary))
        app.add_handler(CommandHandler("gana",          cmd_analyze))
        app.add_handler(CommandHandler("gedit",         cmd_edit_msg))
        app.add_handler(CommandHandler("gnewsctl",      cmd_newsctl))
        app.add_handler(CommandHandler("gnewssrc",      cmd_newssrc))

        # --- Arabic & Short Code News Trigger Words ---
        # gnews (all sectors)
        app.add_handler(MessageHandler(filters.Regex(_re.compile(
            r'^(g|G|غريس|جيجي) (عطني اخر المستجدات|عطيني اخر المستجدات)|^(g|G|غريس|جيجي) (عطني|عطيني)|^(تقرير اليوم يا غريس|تقرير اليوم يا g|تقرير اليوم يا جيجي|تقرير اليوم|زودني)$', _re.IGNORECASE
        )), cmd_news))
        # ggame (gaming)
        app.add_handler(MessageHandler(filters.Regex(_re.compile(
            r'^(g|G|غريس|جيجي) (عطني اخر المستجدات عن الالعاب|عطيني اخر المستجدات عن الالعاب)|^(تقرير الالعاب يا غريس|تقرير الالعاب يا g|تقرير الالعاب يا جيجي|تقرير الالعاب|تقرير الألعاب)$', _re.IGNORECASE
        )), cmd_news_gaming))
        # gmcu (marvel/cinema)
        app.add_handler(MessageHandler(filters.Regex(_re.compile(
            r'^(g|G|غريس|جيجي) (عطني اخر المستجدات عن مارفل|عطيني اخر المستجدات عن مارفل)|^(تقرير مارفل يا غريس|تقرير مارفل يا g|تقرير مارفل يا جيجي|تقرير مارفل)$', _re.IGNORECASE
        )), cmd_news_mcu))
        # gtech (tech)
        app.add_handler(MessageHandler(filters.Regex(_re.compile(
            r'^(g|G|غريس|جيجي) (عطني اخر المستجدات عن التقنية|عطيني اخر المستجدات عن التقنية)|^(تقرير التقنية يا غريس|تقرير التقنية يا g|تقرير التقنية يا جيجي|تقرير التقنية)$', _re.IGNORECASE
        )), cmd_news_tech))

        # Job Queue
        if app.job_queue:
            logger.info("📡 DeepScope Surveillance Jobs are active. Scanning every 30 minutes.")
            # Check for news every 30 minutes (Handles all sources including SaudiGamer)
            app.job_queue.run_repeating(news_job, interval=1800, first=10)
        else:
            logger.warning("⚠️ JobQueue is missing. Automatic news scans will NOT run.")

        # Message handlers
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
        app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER,  farewell_member))

        # Identity/reply handler (group 0)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_who_handler), group=0)

        # Activity tracker (group 1)
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_activity_handler), group=1)

        # Message buffer for /gclearchat (group 3)
        app.add_handler(MessageHandler(filters.ALL, message_buffer_handler), group=3)
        
        # Link filter (group 2)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, link_filter_handler), group=2)

        # Callbacks
        app.add_handler(CallbackQueryHandler(captcha_callback_handler, pattern='^captcha_'))
        app.add_handler(CallbackQueryHandler(apply_answer_callback,    pattern='^ap_'))
        app.add_handler(CallbackQueryHandler(guide_callback,           pattern='^guide_'))
        app.add_handler(CallbackQueryHandler(umbrella_callback_handler,pattern='^ub_'))
        app.add_handler(CallbackQueryHandler(ggai_callback_handler,    pattern='^ggai_'))
        app.add_handler(CallbackQueryHandler(callback_handler))

        app.add_error_handler(error_handler)

        logger.info("✅ Grace Ashcroft Bot is online. Systems operational.")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"❌ Failed to start: {e}", exc_info=True)


if __name__ == "__main__":
    main()
