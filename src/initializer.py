import logging
import os

def init():
    """
    Initialize logging.
    """
    # Basic logging config
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    logging.info("Logging initialized")
