import logging
from dotenv import load_dotenv
import os

def init():
    """
    Initialize environment and logging.
    """
    load_dotenv()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.info("Environment loaded and logging initialized")
