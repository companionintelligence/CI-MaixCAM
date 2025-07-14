"""
Logging Utility
Provides centralized logging for the Companion Capture App

Author: Companion Intelligence
Date: July 13, 2025
"""

import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_file="/sd/system.log"):
    """
    Setup centralized logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    
    Returns:
        logger: Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('CompanionCapture')
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create file handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Log startup message
    logger.info("Logging system initialized")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {log_file}")
    
    return logger

def get_logger(name=None):
    """Get logger instance"""
    if name:
        return logging.getLogger(f'CompanionCapture.{name}')
    return logging.getLogger('CompanionCapture')
