import logging
import os
import platform
import time

class ColoredFormatter(logging.Formatter):
    RED = "\033[91m"
    RESET = "\033[0m"
    
    def format(self, record):
        formatted = super().format(record)
        if record.levelno >= logging.WARNING:
            return f"{self.RED}{formatted}{self.RESET}"
        return formatted

def setup_colored_logging():
    if platform.system() == 'Windows':
        os.system('')
        
    root_logger = logging.getLogger()
    
    # Check if already configured
    if any(getattr(h, 'is_colored', False) for h in root_logger.handlers):
        return
        
    root_logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.is_colored = True
    
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    formatter = ColoredFormatter(log_format, datefmt=date_format)
    console_handler.setFormatter(formatter)
    
    root_logger.handlers = [console_handler]

# Test setup
setup_colored_logging()

# Now simulate other file importing logging and calling basicConfig
logging.basicConfig(level=logging.INFO) # Should be ignored

logger = logging.getLogger("TestLogger")

logger.info("This is an INFO message (should be normal color)")
logger.warning("This is a WARNING message (should be RED!)")
logger.error("This is an ERROR message (should be RED!)")
logger.critical("This is a CRITICAL message (should be RED!)")
