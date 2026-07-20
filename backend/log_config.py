# log_config.py
import logging
import os
import platform
import time


class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter to color WARNING and ERROR messages red in the terminal.
    """
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    
    def format(self, record):
        formatted = super().format(record)
        if record.levelno >= logging.ERROR:
            return f"{self.RED}{formatted}{self.RESET}"
        elif record.levelno >= logging.WARNING:
            return f"{self.YELLOW}{formatted}{self.RESET}"
        return formatted


class EndpointFilter(logging.Filter):
    """
    Filter out noisy uvicorn access log entries for high-frequency polling endpoints.
    
    The frontend polls GET /api/state every ~1 second, generating ~60 log lines/minute
    that drown out important trade/error logs. This filter suppresses those entries
    while keeping all other access logs visible.
    """
    # Endpoints to suppress from access logs (exact path match)
    SUPPRESSED_PATHS = {"/api/state"}
    
    def filter(self, record: logging.LogRecord) -> bool:
        # uvicorn access logs contain the request path in the message
        msg = record.getMessage()
        for path in self.SUPPRESSED_PATHS:
            if f'"{path} ' in msg or f'"{path}?' in msg or f'GET {path} ' in msg:
                return False  # Suppress this log entry
        return True


class RepeatErrorFilter(logging.Filter):
    """
    Throttle repeated identical error/warning messages to prevent log flooding.
    
    When Binance is down, the bot logs the same WebSocket/REST timeout error
    every 5-15 seconds, generating 100+ identical error lines per hour.
    This filter allows the first occurrence, then suppresses duplicates
    for a cooldown period, logging a summary count when a new message appears.
    """
    def __init__(self, cooldown_seconds: int = 300):
        super().__init__()
        self.cooldown_seconds = cooldown_seconds
        self._seen = {}  # key -> {"count": int, "first_at": float, "last_at": float}
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Only throttle WARNING and above
        if record.levelno < logging.WARNING:
            return True
        
        # Use the raw message template as key (before formatting)
        key = f"{record.name}:{record.msg}"
        now = time.time()
        
        if key in self._seen:
            entry = self._seen[key]
            elapsed = now - entry["last_at"]
            
            if elapsed < self.cooldown_seconds:
                # Still within cooldown — suppress but count
                entry["count"] += 1
                entry["last_at"] = now
                return False
            else:
                # Cooldown expired — log summary of suppressed messages, then allow
                suppressed = entry["count"]
                if suppressed > 0:
                    summary = logging.LogRecord(
                        name=record.name, level=logging.WARNING,
                        pathname="", lineno=0, func="",
                        msg=f"↑ Above error repeated {suppressed}x in last {self.cooldown_seconds}s (suppressed)",
                        args=(), exc_info=None
                    )
                    # Get the logger and emit the summary through its handlers
                    logger = logging.getLogger(record.name)
                    for handler in logger.handlers or logging.getLogger().handlers:
                        handler.emit(summary)
                
                # Reset tracker
                self._seen[key] = {"count": 0, "first_at": now, "last_at": now}
                return True
        else:
            # First occurrence — allow it
            self._seen[key] = {"count": 0, "first_at": now, "last_at": now}
            return True


def setup_colored_logging():
    """
    Configure the root logger with the colored formatter.
    This enables ANSI escape colors in the Windows terminal and sets the formatting style.
    """
    # Enable ANSI escape sequences on Windows
    if platform.system() == 'Windows':
        os.system('')
        
    root_logger = logging.getLogger()
    
    # Check if we already configured colored logging to avoid duplicate handlers
    if any(getattr(h, 'is_colored', False) for h in root_logger.handlers):
        return
        
    # Set default level to INFO
    root_logger.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.is_colored = True
    
    # Define a clean, modern log format
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    formatter = ColoredFormatter(log_format, datefmt=date_format)
    console_handler.setFormatter(formatter)
    
    # Clear existing root handlers and set our custom colored handler
    root_logger.handlers = [console_handler]
    
    # ── Apply filters ──
    
    # 1. Suppress /api/state polling spam from uvicorn access logs
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addFilter(EndpointFilter())
    
    # 2. Throttle repeated error messages (e.g. Binance timeout every 15s)
    #    Applied to live_engine and hata_api loggers
    repeat_filter = RepeatErrorFilter(cooldown_seconds=300)  # 5 min cooldown
    for logger_name in ["live_engine", "hata_api"]:
        logging.getLogger(logger_name).addFilter(repeat_filter)


# Automatically initialize when imported
setup_colored_logging()
