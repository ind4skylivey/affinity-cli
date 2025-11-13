"""
Logging Utilities
"""

import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

from affinity_cli import config


def setup_logger(name: str = "affinity_cli", level: str = "INFO") -> logging.Logger:
    """
    Setup logger with Rich console handler
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler with Rich
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=False,
        show_path=False
    )
    console_handler.setLevel(level)
    
    # File handler
    log_dir = config.CONFIG_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "affinity-cli.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Default logger
logger = setup_logger()
