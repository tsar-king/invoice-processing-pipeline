# src/logger.py - Professional Logging Module
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Remove default handler
logger.remove()

# Create logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Format for logs
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"

# Console handler - shows all logs
logger.add(
    sys.stdout,
    format=log_format,
    level="INFO",
    colorize=True
)

# File handler - rotating logs
logger.add(
    log_dir / "pipeline_{time:YYYY-MM-DD}.log",
    format=log_format,
    level="DEBUG",
    rotation="1 day",
    retention="30 days",
    compression="zip"
)

# Error file - only errors
logger.add(
    log_dir / "errors_{time:YYYY-MM-DD}.log",
    format=log_format,
    level="ERROR",
    rotation="1 week",
    retention="3 months"
)

# Export logger for easy import
def get_logger():
    """Get the configured logger instance"""
    return logger

# Convenience functions
def info(message):
    logger.info(message)

def error(message):
    logger.error(message)

def warning(message):
    logger.warning(message)

def debug(message):
    logger.debug(message)

def success(message):
    logger.success(message)

if __name__ == "__main__":
    # Test the logger
    logger.info("Logger initialized successfully!")
    logger.success("This is a success message")
    logger.warning("This is a warning")
    logger.error("This is an error message")