import logging
import sys

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
        logging.WARNING:  "⚠️",
        logging.ERROR:    "❌",
        logging.CRITICAL: "💀",
    }

    def format(self, record):
        color = self._COLORS.get(record.levelno, self._RESET)
        icon  = self._ICONS.get(record.levelno, "🔹")
        
        # Format the timestamp
        time_str = f"{self._DIM}{self.formatTime(record, '%H:%M:%S')}{self._RESET}"
        
        # Build the final message
        msg = f"{time_str} {color}{self._BOLD}{icon} {record.getMessage()}{self._RESET}"
        return msg

def setup_logger():
    # Forensic Logger Setup
    logger = logging.getLogger("grace_forensic")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.hasHandlers():
        return logger

    # Console Handler (Visual Premium)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_GraceConsoleFormatter())
    logger.addHandler(console_handler)

    # File Handler (Full Traceability)
    file_handler = logging.FileHandler("gracebot.log", encoding="utf-8")
    file_fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()
