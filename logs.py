import logging
import sys
from datetime import datetime

# =========================
# 🎨 Color Formatter
# =========================
class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[37m",      # White
        "INFO": "\033[36m",       # Cyan
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


# =========================
# ⚙️ Logger Setup
# =========================
def setup_logger(name: str = "app_logger", log_file: str = "app.log") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # prevent duplicate logs

    if logger.handlers:
        return logger  # already configured

    # -------------------------
    # 🖥️ Console Handler
    # -------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    console_format = ColorFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    logger.addHandler(console_handler)
    return logger
