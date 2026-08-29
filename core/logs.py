import logging
import sys


class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[37m",      
        "INFO": "\033[36m",       
        "WARNING": "\033[33m",    
        "ERROR": "\033[31m",      
        "CRITICAL": "\033[41m",   
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: str = "app_logger", log_file: str = "app.log") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # prevent duplicate logs

    if logger.handlers:
        return logger  # already configured

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    console_format = ColorFormatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    logger.addHandler(console_handler)
    return logger