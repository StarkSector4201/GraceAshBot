import os
import asyncio
import logging
import json
import random
import tempfile
import glob
import re as _re
import time as _time
from datetime import datetime, timedelta
import httpx as _httpx
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import RetryAfter

# These will be imported from the main bot or passed in
# For now, we'll assume they are available via the context or passed as globals
# But it's better to pass them or import them.

logger = logging.getLogger(__name__)

# --- Configuration (To be injected or imported) ---
YT_DLP_PATH = None
FFMPEG_PATH = None
COOKIES_PATH = None
GRACE_PROXY = None
GRACE_COOKIES = None
PO_TOKEN = None
VISITOR_DATA = None
MASTER_ID = None
OWNER_ID = None

_MUSIC_COOLDOWN = 60
_music_active = set()
_music_last_used = {}

def init_music_engine(config):
    global YT_DLP_PATH, FFMPEG_PATH, COOKIES_PATH, GRACE_PROXY, GRACE_COOKIES, PO_TOKEN, VISITOR_DATA, MASTER_ID, OWNER_ID
    YT_DLP_PATH = config.get("YT_DLP_PATH")
    FFMPEG_PATH = config.get("FFMPEG_PATH")
    COOKIES_PATH = config.get("COOKIES_PATH")
    GRACE_PROXY = config.get("GRACE_PROXY")
    GRACE_COOKIES = config.get("GRACE_COOKIES")
    PO_TOKEN = config.get("PO_TOKEN")
    VISITOR_DATA = config.get("VISITOR_DATA")
    MASTER_ID = config.get("MASTER_ID")
    OWNER_ID = config.get("OWNER_ID")

def _escape_markdown_v2(text: str) -> str:
    specials = r"[\_\*\[\]\(\)\~\`\#\+\-\=\|\{\}\.\!]"
    return _re.sub(specials, lambda m: "\\" + m.group(0), str(text))

async def cmd_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Need access to get_phrase, get_lock_reason, escape_md
    # I'll pass them or import them. 
    # For now, let's assume they are injected into the context or we import from main.
    from gracebot import get_phrase, get_lock_reason, escape_md
    
    chat_id = update.effective_chat.id
    if reason := get_lock_reason("gmusic"):
        await update.message.reply_text(get_phrase(chat_id, "lock_denied_gmusic", reason=reason), parse_mode="Markdown")
        return

    user = update.effective_user
    if not user or not update.message:
        return
    user_id  = user.id

    if not context.args:
        await update.message.reply_text(get_phrase(chat_id, "music_hint"), parse_mode="MarkdownV2")
        return

    now       = _time.time()
    last_used = _music_last_used.get(user_id, 0)
    remaining = _MUSIC_COOLDOWN - (now - last_used)
    if remaining > 0 and not (user_id == MASTER_ID or user_id == OWNER_ID):
        await update.message.reply_text(
            get_phrase(chat_id, "music_cooldown", time=int(remaining)),
            parse_mode="MarkdownV2"
        )
        return

    if user_id in _music_active:
        await update.message.reply_text(
            get_phrase(chat_id, "music_active"),
            parse_mode="MarkdownV2"
        )
        return

    query_raw = " ".join(context.args).strip()
    query_esc = _escape_markdown_v2(query_raw)

    _music_active.add(user_id)
    _music_last_used[user_id] = now

    tunnel_tag = " 🛡️ `Secure Tunnel Active`" if GRACE_PROXY else ""
    pot_tag    = " 🧬 `Fingerprint Active`" if PO_TOKEN else ""
    cookie_tag = " 🍪 `Session Authenticated`" if GRACE_COOKIES else ""
    
    status = await update.message.reply_text(
        f"{get_phrase(chat_id, 'music_node_engine')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔎 `Query: {query_esc}`\n"
        f"{tunnel_tag}{pot_tag}{cookie_tag}\n\n"
        f"{get_phrase(chat_id, 'music_scan_init')}",
        parse_mode="MarkdownV2"
    )

    last_status_text = ""
    async def safe_edit(text):
        nonlocal last_status_text
        if text != last_status_text:
            try: 
                await status.edit_text(text, parse_mode="MarkdownV2")
                last_status_text = text
            except Exception as e:
                logger.error(f"❌ safe_edit error: {e}")

    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="grace_music_")
        stop_event = asyncio.Event()

        async def _animate():
            idx = 0
            music_frames = get_phrase(chat_id, "music_frames")
            while not stop_event.is_set():
                frame = music_frames[idx % len(music_frames)]
                try:
                    footer = get_phrase(chat_id, "music_footer_1") if idx % 2 == 0 else get_phrase(chat_id, "music_footer_2")
                    await status.edit_text(
                        f"{get_phrase(chat_id, 'music_node_engine')}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔎 `Query: {query_esc}`\n\n"
                        f"{frame}\n"
                        f"_{footer}_",
                        parse_mode="MarkdownV2"
                    )
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                except Exception:
                    pass
                idx += 1
                await asyncio.sleep(4.5)

        anim_task = asyncio.create_task(_animate())

        if not os.path.exists(FFMPEG_PATH):
            stop_event.set()
            await status.edit_text(get_phrase(chat_id, "music_ffmpeg_missing"), parse_mode="MarkdownV2")
            return

        is_spotify_link = "open.spotify.com/" in query_raw.lower()
        official_thumb_path = None
        
        if is_spotify_link:
            await safe_edit(
                f"🎵 **Grace Ashcroft — Spotify Intelligence Layer**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔎 `Detecting Spotify Metadata\\.\\.\\.`\n\n"
                f"📡 **Extracting official tags & HQ artwork\\.\\.\\.**\n"
                f"_Syncing with Spotify database mirrors_"
            )
            
            browser_choice = GRACE_COOKIES if GRACE_COOKIES else "firefox"
            meta_cmd = [
                YT_DLP_PATH, "--print", "title:%(title)s | artist:%(uploader)s | thumb:%(thumbnail)s",
                "--no-cache-dir", "--no-warnings", query_raw
            ]
            if os.path.exists(COOKIES_PATH):
                meta_cmd.extend(["--cookies", COOKIES_PATH])
            elif GRACE_COOKIES:
                meta_cmd.extend(["--cookies-from-browser", browser_choice])

            if GRACE_PROXY and GRACE_PROXY.strip():
                meta_cmd.extend(["--proxy", GRACE_PROXY])
            else:
                meta_cmd.extend(["--proxy", ""]) # Force direct, ignore system 407 proxy
            
            m_proc = await asyncio.create_subprocess_exec(*meta_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            m_stdout, _ = await m_proc.communicate()
            
            if m_proc.returncode == 0 and m_stdout:
                meta_str = m_stdout.decode().strip()
                m_title = _re.search(r"title:(.*?) \|", meta_str)
                m_artist = _re.search(r"artist:(.*?) \|", meta_str)
                m_thumb = _re.search(r"thumb:(.*)", meta_str)
                
                if m_title and m_artist:
                    query_raw = f"{m_title.group(1).strip()} - {m_artist.group(1).strip()}"
                    query_esc = _escape_markdown_v2(query_raw)
                    if m_thumb:
                        try:
                            thumb_url = m_thumb.group(1).strip()
                            proxy_cfg = {"all://": GRACE_PROXY} if GRACE_PROXY else None
                            async with _httpx.AsyncClient(proxies=proxy_cfg) as client:
                                r = await client.get(thumb_url, timeout=10)
                                if r.status_code == 200:
                                    official_thumb_path = os.path.join(tmp_dir, "spotify_art.jpg")
                                    with open(official_thumb_path, "wb") as f:
                                        f.write(r.content)
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to pull HQ Artwork: {e}")

        is_youtube_link = "youtube.com/" in query_raw.lower() or "youtu.be/" in query_raw.lower()
        is_soundcloud_link = "soundcloud.com/" in query_raw.lower()
        
        stages = []
        if is_youtube_link:
            stages = [
                {
                    "name": "YouTube Link (Master Key Access)",
                    "cmd": [
                        YT_DLP_PATH, query_raw, "-x", "--audio-format", "mp3", "--audio-quality", "192k",
                        "--ffmpeg-location", FFMPEG_PATH, "--format", "bestaudio",
                        "--extractor-args", "youtube:player-client=ios,web",
                        "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
                        "--add-header", "Accept-Language:en-US,en;q=0.9",
                        "--add-header", "referer:https://www.youtube.com/",
                        "--force-ipv4", "--write-info-json", "--write-thumbnail",
                        "--no-playlist", "--no-check-certificate", "--quiet", "--no-warnings"
                    ]
                },
                {
                    "name": "YouTube Link (Android Mobile Bypass)",
                    "cmd": [
                        YT_DLP_PATH, query_raw, "-x", "--audio-format", "mp3", "--audio-quality", "192k",
                        "--ffmpeg-location", FFMPEG_PATH, "--format", "bestaudio/best",
                        "--extractor-args", "youtube:player-client=android",
                        "--user-agent", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
                        "--write-info-json", "--write-thumbnail",
                        "--no-playlist", "--no-check-certificate", "--force-ipv4", "--quiet", "--no-warnings"
                    ]
                }
            ]
        elif is_soundcloud_link:
            stages = [
                {
                    "name": "SoundCloud Direct",
                    "cmd": [
                        YT_DLP_PATH, query_raw, "-x", "--audio-format", "mp3", "--audio-quality", "192k",
                        "--ffmpeg-location", FFMPEG_PATH,
                        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "--add-header", "referer:https://soundcloud.com/",
                        "--write-info-json", "--write-thumbnail",
                        "--no-playlist", "--no-check-certificate", "--quiet", "--no-warnings"
                    ]
                }
            ]
        else:
            stages = [
                {
                    "name": "SoundCloud Archives (Proxy)",
                    "cmd": [
                        YT_DLP_PATH, f"scsearch1:{query_raw}",
                        "-x", "--audio-format", "mp3", "--audio-quality", "192k",
                        "--ffmpeg-location", FFMPEG_PATH, "--format", "bestaudio",
                        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "--add-header", "Accept-Language:en-US,en;q=0.9", "--add-header", "referer:https://soundcloud.com/",
                        "--write-info-json", "--write-thumbnail", "--no-playlist", "--no-check-certificate", "--no-warnings"
                    ],
                    "use_proxy": True
                },
                {
                    "name": "SoundCloud Archives (Clean IP)",
                    "cmd": [
                        YT_DLP_PATH, f"scsearch1:{query_raw}",
                        "-x", "--audio-format", "mp3", "--audio-quality", "192k",
                        "--ffmpeg-location", FFMPEG_PATH, "--format", "bestaudio",
                        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "--add-header", "Accept-Language:en-US,en;q=0.9", "--add-header", "referer:https://soundcloud.com/",
                        "--write-info-json", "--write-thumbnail", "--no-playlist", "--no-check-certificate", "--quiet", "--no-warnings"
                    ],
                    "use_proxy": False
                },
                {
                    "name": "YouTube Music (Proxy)",
                    "cmd": [
                        YT_DLP_PATH, f"ytsearch1:{query_raw}",
                        "-x", "--audio-format", "mp3", "--audio-quality", "192k",
                        "--ffmpeg-location", FFMPEG_PATH, "--format", "bestaudio",
                        "--extractor-args", "youtube:player-client=android,ios",
                        "--user-agent", "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
                        "--add-header", "Accept-Language:en-US,en;q=0.9",
                        "--write-info-json", "--write-thumbnail", "--no-playlist", "--no-check-certificate", "--force-ipv4", "--quiet", "--no-warnings"
                    ],
                    "use_proxy": True
                },
                {
                    "name": "YouTube Music (Clean IP)",
                    "cmd": [
                        YT_DLP_PATH, f"ytsearch1:{query_raw}",
                        "-x", "--audio-format", "mp3", "--audio-quality", "192k",
                        "--ffmpeg-location", FFMPEG_PATH, "--format", "bestaudio",
                        "--extractor-args", "youtube:player-client=ios,web",
                        "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
                        "--add-header", "Accept-Language:en-US,en;q=0.9",
                        "--write-info-json", "--write-thumbnail", "--no-playlist", "--no-check-certificate", "--force-ipv4", "--quiet", "--no-warnings"
                    ],
                    "use_proxy": False
                }
            ]

        success = False
        captured_output = []
        for stage in stages:
            if GRACE_PROXY and GRACE_PROXY.strip() and stage.get("use_proxy", True):
                stage["cmd"].extend(["--proxy", GRACE_PROXY])
            else:
                # Force direct connection to avoid picking up system proxies with 407 errors
                stage["cmd"].extend(["--proxy", ""])
            if PO_TOKEN and VISITOR_DATA and ("youtube" in str(stage["cmd"]) or "ytsearch" in str(stage["cmd"]) or "youtube.com" in query_raw.lower()):
                pot_arg = f"youtube:player-client=web,ios,tv;po_token=web+{PO_TOKEN};visitor_data={VISITOR_DATA}"
                stage["cmd"].extend(["--extractor-args", pot_arg])
            if os.path.exists(COOKIES_PATH):
                stage["cmd"].extend(["--cookies", COOKIES_PATH])
            elif GRACE_COOKIES and ("youtube" in str(stage["cmd"]) or "ytsearch" in str(stage["cmd"]) or "youtube.com" in query_raw.lower() or "soundcloud" in str(stage["cmd"])):
                stage["cmd"].extend(["--cookies-from-browser", GRACE_COOKIES])

            st_name_esc = _escape_markdown_v2(stage['name'])
            try:
                scan_line = f"📡 **Scanning: {st_name_esc}\\.\\.\\.**"
                if get_phrase(chat_id, "welcome").startswith("أوه"):
                    scan_line = f"📡 **جاري المسح: {st_name_esc}\\.\\.\\.**"
                await status.edit_text(
                    f"{get_phrase(chat_id, 'music_node_engine')}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔎 `Query: {query_esc}`\n\n"
                    f"{scan_line}\n"
                    f"_{get_phrase(chat_id, 'music_footer_1')}_",
                    parse_mode="MarkdownV2"
                )
            except Exception: pass

            proc = await asyncio.create_subprocess_exec(*stage["cmd"], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=tmp_dir)
            try:
                await asyncio.wait_for(proc.wait(), timeout=40)
                stdout, stderr = await proc.communicate()
                mp3_files = glob.glob(os.path.join(tmp_dir, "*.mp3"))
                json_files = glob.glob(os.path.join(tmp_dir, "*.info.json"))
                
                if mp3_files and proc.returncode == 0:
                    # Forensic Check: Is this a 30-second preview?
                    is_preview = False
                    if json_files:
                        try:
                            with open(json_files[0], "r", encoding="utf-8") as jf:
                                meta = json.load(jf)
                                duration = meta.get("duration", 0)
                                if duration > 0 and duration < 45:
                                    logger.warning(f"⚠️ Detected Preview ({duration}s). Discarding and rotating nodes...")
                                    is_preview = True
                        except: pass
                    
                    if is_preview:
                        # Clean up preview files and try next stage
                        for f in glob.glob(os.path.join(tmp_dir, "*")):
                            try: os.remove(f)
                            except: pass
                        continue 

                    success = True
                    break
                else:
                    captured_output.append(stderr.decode(errors="ignore") if stderr else "No error output")
            except asyncio.TimeoutError:
                proc.terminate()
                await proc.wait()

        stop_event.set()
        try: await anim_task
        except: pass

        mp3_files = glob.glob(os.path.join(tmp_dir, "*.mp3"))
        if not success and is_youtube_link:
            await safe_edit(
                f"🎵 **Grace Ashcroft — Multi\\-Node Acquisition**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔎 `Query: {query_esc}`\n"
                f"{tunnel_tag}\n\n"
                f"🕵️ **Direct link blocked\\. Extracting metadata\\.\\.\\.**\n"
                f"_Triangulating audio from secondary mirrors_"
            )
            real_title = ""
            for client in ["ios", "android", "tv", "web"]:
                meta_cmd = ["yt-dlp", "--print", "%(title)s", "--no-warnings", "--extractor-args", f"youtube:player-client={client}", query_raw]
                if GRACE_PROXY and GRACE_PROXY.strip():
                    meta_cmd.extend(["--proxy", GRACE_PROXY])
                else:
                    meta_cmd.extend(["--proxy", ""])
                m_proc = await asyncio.create_subprocess_exec(*meta_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                m_stdout, _ = await m_proc.communicate()
                if m_proc.returncode == 0 and m_stdout:
                    real_title = m_stdout.decode(errors="ignore").strip()
                    break
            
            if real_title:
                sc_fallback_cmd = ["yt-dlp", f"scsearch1:{real_title}", "-x", "--audio-format", "mp3", "--audio-quality", "192k", "--no-playlist", "--no-check-certificate", "--quiet", "--no-warnings", "--write-info-json", "--write-thumbnail"]
                if GRACE_PROXY and GRACE_PROXY.strip():
                    sc_fallback_cmd.extend(["--proxy", GRACE_PROXY])
                else:
                    sc_fallback_cmd.extend(["--proxy", ""])
                s_proc = await asyncio.create_subprocess_exec(*sc_fallback_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=tmp_dir)
                await s_proc.wait()
                if mp3_files and s_proc.returncode == 0:
                    # Final Forensic Validation
                    is_preview = False
                    json_files = glob.glob(os.path.join(tmp_dir, "*.info.json"))
                    if json_files:
                        try:
                            with open(json_files[0], "r", encoding="utf-8") as jf:
                                dur = json.load(jf).get("duration", 0)
                                if dur > 0 and dur < 45: is_preview = True
                        except: pass
                    
                    if not is_preview:
                        success = True
                    else:
                        # Clean up failed preview
                        for f in glob.glob(os.path.join(tmp_dir, "*")):
                            try: os.remove(f)
                            except: pass

        if not success or not mp3_files:
            q_esc = escape_md(query_raw)
            combined_output = "\n".join(captured_output).lower()
            not_found = any(kw in combined_output for kw in ["no results", "not found", "couldn't find", "no match"])
            if not_found or not mp3_files:
                await status.edit_text(get_phrase(chat_id, "music_no_match", query=q_esc, proxy=tunnel_tag), parse_mode="MarkdownV2")
            else:
                await status.edit_text(get_phrase(chat_id, "music_blocked", proxy=tunnel_tag), parse_mode="MarkdownV2")
            return

        audio_path = mp3_files[0]
        file_size  = os.path.getsize(audio_path)
        if file_size > 49 * 1024 * 1024:
            await status.edit_text(get_phrase(chat_id, "music_too_large"), parse_mode="MarkdownV2")
            return

        performer, title, album = "Unknown", "Unknown", "Original Content"
        json_files = glob.glob(os.path.join(tmp_dir, "*.info.json"))
        if json_files:
            try:
                with open(json_files[0], "r", encoding="utf-8") as jf:
                    meta = json.load(jf)
                    performer = meta.get("artist", meta.get("uploader", meta.get("creator", "Unknown")))
                    title     = meta.get("title", "Unknown")
                    album     = meta.get("album", "Original Content")
                    title = _re.sub(r"\s*\[\d+\]\s*$", "", title)
            except Exception: pass
        
        if title == "Unknown":
            base_name = _re.sub(r"\s*\[\d+\]\s*$", "", os.path.splitext(os.path.basename(audio_path))[0])
            parts = base_name.split(" - ", 1)
            if len(parts) == 2: performer, title = parts[0].strip(), parts[1].strip()
            else: title = base_name

        try:
            await status.edit_text(
                f"{get_phrase(chat_id, 'music_finalised')}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"📥 `Track: {escape_md(title)}`\n"
                f"🎤 `Artist: {escape_md(performer)}`\n"
                f"💿 `Album: {escape_md(album)}`\n"
                f"{tunnel_tag}\n\n"
                f"{get_phrase(chat_id, 'music_initiating_upload')}",
                parse_mode="MarkdownV2"
            )
        except Exception: pass

        await context.bot.send_chat_action(chat_id=chat_id, action="upload_voice")
        size_mb = f"{file_size / (1024 * 1024):.1f}"
        audio_caption = get_phrase(chat_id, "music_caption", title=escape_md(title), performer=escape_md(performer), album=escape_md(album), size=escape_md(size_mb))
        thumb_files = glob.glob(os.path.join(tmp_dir, "*.jpg")) + glob.glob(os.path.join(tmp_dir, "*.png")) + glob.glob(os.path.join(tmp_dir, "*.webp"))
        thumb_path = official_thumb_path if official_thumb_path else (thumb_files[0] if thumb_files else None)

        with open(audio_path, "rb") as af:
            thumb_obj = open(thumb_path, "rb") if thumb_path else None
            try:
                await context.bot.send_audio(
                    chat_id=chat_id, audio=af, thumbnail=thumb_obj,
                    caption=audio_caption, parse_mode="MarkdownV2",
                    title=title, performer=performer,
                    reply_to_message_id=update.message.message_id,
                    connect_timeout=600, read_timeout=600, write_timeout=600
                )
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
                await context.bot.send_audio(
                    chat_id=chat_id, audio=af, thumbnail=thumb_obj,
                    caption=audio_caption, parse_mode="MarkdownV2",
                    title=title, performer=performer,
                    reply_to_message_id=update.message.message_id,
                    connect_timeout=600, read_timeout=600, write_timeout=600
                )
            finally:
                if thumb_obj: thumb_obj.close()
        
        try: await status.delete()
        except: pass
    except Exception as exc:
        logger.error(f"❌ GMusic Error: {exc}", exc_info=True)
        try: await status.edit_text("💥 **System fault during acquisition\\.**\n_Major error logged\\._ 📋", parse_mode="MarkdownV2")
        except: pass
    finally:
        try: stop_event.set()
        except: pass
        _music_active.discard(user_id)
        if tmp_dir and os.path.isdir(tmp_dir):
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
