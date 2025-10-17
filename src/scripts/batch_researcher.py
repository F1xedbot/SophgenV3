import asyncio
import logging
import traceback
import orjson
from utils.enums import LLMModels
from services.llm import LLMService
from agents.researcher import Researcher
from agents.tools import ResearcherTools
from agents.states import ResearcherState
from services.sqlite import SQLiteDBService
from initializer import init

# ---------------- CONFIG ---------------- #
INPUT_JSON = "data/all_cwes.json"
DB_TABLE = "researches"
MAX_RETRIES = 3
RETRY_DELAY = 15  # seconds between retries
# ---------------------------------------- #

logger = logging.getLogger(__name__)


async def run_validation(index: int, cwe_id: str, llm: LLMService, db: SQLiteDBService):
    # Skip if already researched
    existing = db.get_data_group(DB_TABLE, "cwe_id", cwe_id)
    if existing:
        logger.info(f"[{index}] Skipping '{cwe_id}' — already in DB.")
        return

    researcher_tools = ResearcherTools()
    researcher = Researcher(llm, researcher_tools)
    initial_state = ResearcherState(messages=[], cwe_id=cwe_id)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{index}] Researching '{cwe_id}' (attempt {attempt}/{MAX_RETRIES})...")
            response = await researcher.run(initial_state)
            logger.info(f"[{index}] Research successful for '{cwe_id}'.")
            return 

        except Exception as e:
            logger.warning(f"[{index}] Attempt {attempt} failed: {e}")
            traceback.print_exc()

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(f"[{index}] Failed permanently after {MAX_RETRIES} attempts.")


async def main():
    init()
    logger.info("Starting CWE research...")

    with open(INPUT_JSON, "rb") as f:
        llm_input = orjson.loads(f.read())

    total = len(llm_input)
    logger.info(f"Loaded {total} CWE IDs.")

    llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
    db = SQLiteDBService()

    for i, cwe_id in enumerate(llm_input):
        await run_validation(i, cwe_id, llm, db)

    logger.info("✅ Batch research completed.")


if __name__ == "__main__":
    asyncio.run(main())
