import logging
import sys

def setup_logging():
    """Set up logging configuration"""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set to DEBUG level
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # Set to DEBUG level
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger 