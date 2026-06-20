# log_config.py
import logging
import os
import platform

class ColoredFormatter(logging.Formatter):
    """
    Custom logging formatter to color WARNING and ERROR messages red in the terminal.
    """
    RED = "\033[91m"
    RESET = "\033[0m"
    
    def format(self, record):
        formatted = super().format(record)
        # Check if log level is WARNING, ERROR, or CRITICAL, and color it red
        if record.levelno >= logging.WARNING:
            return f"{self.RED}{formatted}{self.RESET}"
        return formatted

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

# Automatically initialize when imported
setup_colored_logging()
