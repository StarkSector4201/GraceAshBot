import os
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

def get_binary_path(name, fallback):
    """Detects binary in system PATH, Environment, or uses fallback."""
    return os.getenv(f"{name.upper().replace('-', '_')}_PATH") or shutil.which(name) or fallback

# --- Paths ---
BASE_DIR = Path(__file__).parent.parent
AVATAR_DIR = BASE_DIR / "Avatar"
SETTINGS_FILE = BASE_DIR / "grace_settings.json"
MUTE_ANIMATION_PATH = AVATAR_DIR / "mute.gif.mp4"
MILA_MUTE_VIDEO_PATH = AVATAR_DIR / "mute2.gif.mp4"
COOKIES_PATH = BASE_DIR / "cookies.txt"

# --- Binaries ---
YT_DLP_PATH = get_binary_path("yt-dlp", r"C:\Users\abyad\AppData\Local\Programs\Python\Python310\Scripts\yt-dlp.exe")
FFMPEG_PATH = get_binary_path("ffmpeg", r"C:\Users\abyad\AppData\Local\Programs\Python\Python310\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")

# --- Environment Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPO", "https://github.com/YourUsername/grace-bot")
DEFAULT_DIALECT = os.getenv("DIALECT", "arabic_fousha")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Beirut"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
MASTER_ID = int(os.getenv("MASTER_ID", "0"))
INVITE_PASSWORD = os.getenv("INVITE_PASSWORD", "")
LOG_CHANNEL = os.getenv("LOG_CHANNEL", "")
INTEL_CHANNEL = os.getenv("INTEL_CHANNEL", "")
GRACE_PROXY   = os.getenv("GRACE_PROXY", "")
PO_TOKEN      = os.getenv("PO_TOKEN", "")
VISITOR_DATA  = os.getenv("VISITOR_DATA", "")
GRACE_COOKIES = os.getenv("GRACE_COOKIES", "")
SAUCENAO_KEY  = os.getenv("SAUCENAO_API_KEY", "")

# --- Sudo Users Parsing ---
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
