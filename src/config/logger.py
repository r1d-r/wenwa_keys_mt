"""
Centralized logging configuration for Magic Keys MT5 Trading Manager.
Provides file and console logging with rotation.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    """Centralized logger for the application."""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern to ensure one logger instance."""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger if not already initialized."""
        if not Logger._initialized:
            self._setup_logger()
            Logger._initialized = True

    def _setup_logger(self):
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs"
        )
        os.makedirs(log_dir, exist_ok=True)

        # Create log filename with date
        log_filename = os.path.join(
            log_dir, f'magic_keys_{datetime.now().strftime("%Y%m%d")}.log'
        )

        # Create logger
        self.logger = logging.getLogger("MagicKeys")
        self.logger.setLevel(logging.DEBUG)

        # Clear existing handlers (in case of reinitialization)
        self.logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        simple_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] - %(message)s", datefmt="%H:%M:%S"
        )

        # File handler with rotation (10MB max, keep 5 backup files)
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info("Magic Keys MT5 Trading Manager - Logger Initialized")
        self.logger.info("=" * 80)

    def get_logger(self, name=None):
        """
        Get a logger instance.

        Args:
            name (str, optional): Name for the logger. If None, returns root logger.

        Returns:
            logging.Logger: Logger instance
        """
        if name:
            return logging.getLogger(f"MagicKeys.{name}")
        return self.logger

    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)

    def info(self, message):
        """Log info message."""
        self.logger.info(message)

    def warning(self, message):
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        """Log error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message, exc_info=False):
        """Log critical message with optional exception info."""
        self.logger.critical(message, exc_info=exc_info)


# Create global logger instance
logger = Logger()


# Convenience function for getting module-specific loggers
def get_logger(name):
    """
    Get a module-specific logger.

    Args:
        name (str): Module name (usually __name__)

    Returns:
        logging.Logger: Logger instance for the module

    Example:
        >>> from src.config.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("This is a log message")
    """
    return logger.get_logger(name)


# Example usage and testing
if __name__ == "__main__":
    # Test the logger
    test_logger = get_logger("TestModule")

    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")

    # Test exception logging
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        test_logger.error("Caught an exception", exc_info=True)

    print("\n✅ Logger test completed. Check the logs/ directory for log files.")
