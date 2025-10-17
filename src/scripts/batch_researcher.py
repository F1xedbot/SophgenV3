import asyncio
import logging
import re
import traceback
from contextlib import suppress
import os
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
MAX_TASK_TIMEOUT = 90     # seconds to forcibly kill any hanging call
RATE_LIMIT_DELAY = 5      # seconds between LLM calls to stay under 15/min
# ---------------------------------------- #

logger = logging.getLogger(__name__)


async def run_validation(index: int, cwe_id: str, llm: LLMService, db: SQLiteDBService):
    existing = await db.get_data_group(DB_TABLE, "cwe_id", cwe_id)
    if existing:
        logger.info(f"[{index}] Skipping '{cwe_id}' — already in DB.")
        return

    researcher_tools = ResearcherTools()
    researcher = Researcher(llm, researcher_tools)
    state = ResearcherState(messages=[], cwe_id=cwe_id)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{index}] Researching '{cwe_id}' (attempt {attempt}/{MAX_RETRIES})...")
            result = await asyncio.wait_for(
                researcher.run(state),
                timeout=MAX_TASK_TIMEOUT
            )
            logger.info(f"[{index}] Success: {result}")
            await asyncio.sleep(RATE_LIMIT_DELAY)
            return

        except asyncio.TimeoutError:
            logger.warning(f"[{index}] Timeout after {MAX_TASK_TIMEOUT}s — skipping '{cwe_id}'.")
            break

        except ResourceExhausted as e:
            match = re.search(r"Please retry in (\d+\.?\d*)s", str(e))
            wait_time = float(match.group(1)) + 1 if match else 60
            if attempt < MAX_RETRIES:
                logger.info(f"[{index}] Waiting {wait_time:.1f}s due to quota.")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[{index}] Failed permanently due to quota for '{cwe_id}'.")
                break

        except Exception as e:
            logger.warning(f"[{index}] Attempt {attempt} failed: {e}")
            traceback.print_exc()
            if attempt < MAX_RETRIES:
                logger.info(f"[{index}] Waiting {DEFAULT_RETRY_DELAY}s before retrying.")
                await asyncio.sleep(DEFAULT_RETRY_DELAY)
            else:
                logger.error(f"[{index}] Failed permanently after {MAX_RETRIES} attempts.")
                break


async def main():
    await init()
    logger.info("Starting CWE research...")

    with open(INPUT_JSON, "rb") as f:
        llm_input = orjson.loads(f.read())

    llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
    db = SQLiteDBService()

    try:
        for i, cwe_id in enumerate(llm_input):
            await run_validation(i, cwe_id, llm, db)
        logger.info("Batch research completed cleanly.")
    finally:
        with suppress(Exception):
            await db.close()
        with suppress(Exception):
            if hasattr(llm, "client") and hasattr(llm.client, "close"):
                await llm.client.close()
        logger.info("Cleanup complete.")
        os._exit(0)


if __name__ == "__main__":
    asyncio.run(main())