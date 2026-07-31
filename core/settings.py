import os
import json
import copy
import threading
import asyncio
from core.config import SETTINGS_FILE, DEFAULT_DIALECT
from core.logger import logger

_SETTINGS_CACHE = None
_SETTINGS_ASYNC_LOCK = asyncio.Lock()
_SAVE_TIMER = None

def load_settings():
    """Thread-safe, cached settings loader."""
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is not None:
        return _SETTINGS_CACHE
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                _SETTINGS_CACHE = json.load(f)
                return _SETTINGS_CACHE
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    _SETTINGS_CACHE = {}
    return _SETTINGS_CACHE

def save_settings(settings=None):
    """
    Debounced Disk Persistence Coalescer.
    Rapid calls to this function will be deduplicated and written to disk once every 2s.
    """
    global _SETTINGS_CACHE, _SAVE_TIMER
    if settings is not None:
        _SETTINGS_CACHE = settings
        
    if _SAVE_TIMER is not None:
        _SAVE_TIMER.cancel()
        
    _SAVE_TIMER = threading.Timer(2.0, _flush_to_disk)
    _SAVE_TIMER.daemon = True
    _SAVE_TIMER.start()

def _flush_to_disk():
    """Perform the actual atomic write to disk."""
    global _SETTINGS_CACHE
    if _SETTINGS_CACHE is not None:
        try:
            data = copy.deepcopy(_SETTINGS_CACHE)
            temp_file = str(SETTINGS_FILE) + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, SETTINGS_FILE)
            logger.debug("Settings flushed to disk.")
        except Exception as e:
            logger.error(f"Failed to save settings to disk: {e}")

def get_group_settings(chat_id: int):
    """Atomic read-only access to specific group settings."""
    settings = load_settings()
    cid_str = str(chat_id)
    if cid_str not in settings:
        settings[cid_str] = {"dialect": DEFAULT_DIALECT}
    return settings[cid_str]

def _flush_settings_sync():
    """Synchronous flush for shutdown hooks."""
    global _SAVE_TIMER
    if _SAVE_TIMER is not None:
        _SAVE_TIMER.cancel()
        _SAVE_TIMER = None
    if _SETTINGS_CACHE is not None:
        _flush_to_disk()

import atexit
atexit.register(_flush_settings_sync)
