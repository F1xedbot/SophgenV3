import asyncio
import logging
import re
import traceback

import orjson
from google.api_core.exceptions import ResourceExhausted

from agents.researcher import Researcher
from agents.states import ResearcherState
from agents.tools import ResearcherTools
from initializer import init
from services.llm import LLMService
from services.sqlite import SQLiteDBService
from utils.enums import LLMModels

# ---------------- CONFIG ---------------- #
INPUT_JSON = "data/all_cwes.json"
DB_TABLE = "researches"
MAX_RETRIES = 5
DEFAULT_RETRY_DELAY = 20  # seconds between non-quota related retries
# ---------------------------------------- #

logger = logging.getLogger(__name__)


async def run_validation(index: int, cwe_id: str, llm: LLMService, db: SQLiteDBService):
    """
    Runs the research process for a single CWE ID with robust retry and quota handling.
    """
    # Skip if already researched
    existing = await db.get_data_group(DB_TABLE, "cwe_id", cwe_id)
    if existing:
        logger.info(f"[{index}] Skipping '{cwe_id}' — already in DB.")
        return

    researcher_tools = ResearcherTools()
    researcher = Researcher(llm, researcher_tools)
    initial_state = ResearcherState(messages=[], cwe_id=cwe_id)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{index}] Researching '{cwe_id}' (attempt {attempt}/{MAX_RETRIES})...")
            await researcher.run(initial_state)
            logger.info(f"[{index}] Research successful for '{cwe_id}'.")
            return

        except ResourceExhausted as e:
            logger.warning(f"[{index}] Quota limit reached on attempt {attempt}.")
            match = re.search(r"Please retry in (\d+\.?\d*)s", str(e))

            if attempt < MAX_RETRIES:
                if match:
                    wait_time = float(match.group(1)) + 1  # Add a 1-second buffer
                    logger.info(f"[{index}] Waiting for {wait_time:.2f} seconds as suggested by the API.")
                    await asyncio.sleep(wait_time)
                else:
                    logger.warning(f"[{index}] Could not parse retry delay. Waiting for a default of 60s.")
                    await asyncio.sleep(60)
            else:
                logger.error(f"[{index}] Failed permanently due to quota issues for '{cwe_id}'.")
                break

        except Exception as e:
            logger.warning(f"[{index}] Attempt {attempt} failed with a non-quota error: {e}")
            traceback.print_exc()

            if attempt < MAX_RETRIES:
                logger.info(f"[{index}] Waiting for {DEFAULT_RETRY_DELAY} seconds before retrying.")
                await asyncio.sleep(DEFAULT_RETRY_DELAY)
            else:
                logger.error(f"[{index}] Failed permanently for '{cwe_id}' after {MAX_RETRIES} attempts.")
                break


async def main():
    """
    Initializes services and orchestrates the batch research process sequentially.
    """
    await init()
    logger.info("Starting CWE research...")

    try:
        with open(INPUT_JSON, "rb") as f:
            llm_input = orjson.loads(f.read())
    except FileNotFoundError:
        logger.error(f"Input file not found: {INPUT_JSON}")
        return

    total = len(llm_input)
    logger.info(f"Loaded {total} CWE IDs.")

    llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
    db = SQLiteDBService()

    for i, cwe_id in enumerate(llm_input):
        await run_validation(i, cwe_id, llm, db)

    logger.info("✅ Batch research completed.")


if __name__ == "__main__":
    asyncio.run(main())
