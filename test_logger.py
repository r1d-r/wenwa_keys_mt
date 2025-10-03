"""
Quick test script for the logging system.
"""

from src.config.logger import get_logger

# Create a test logger
logger = get_logger("LoggerTest")


def test_logging():
    """Test all logging levels."""
    logger.info("Testing Magic Keys logging system...")

    # Test different log levels
    logger.debug("DEBUG: This is detailed information for debugging")
    logger.info("INFO: Normal operational message")
    logger.warning("WARNING: Something unexpected happened")
    logger.error("ERROR: An error occurred but app can continue")
    logger.critical("CRITICAL: Serious error, app may not continue")

    # Test exception logging
    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error("Caught division by zero error", exc_info=True)

    logger.info("Logging test completed successfully!")
    print("\n✅ Check the 'logs/' folder for the log file")


if __name__ == "__main__":
    test_logging()
