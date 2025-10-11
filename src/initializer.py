import logging
import os
from services.sqlite import SQLiteDBService

def init():
    """
    Initialize required components.
    """
    # Basic logging config
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logging.info("Logging initialized")

    db = SQLiteDBService()
    db.init_db()
    logging.info("Database initialized")
