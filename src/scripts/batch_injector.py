import asyncio
import logging
import pandas as pd
import traceback
from typing import Any, Dict

from utils.enums import LLMModels
from services.llm import LLMService
from agents.injector import Injector
from agents.tools import InjectorTools
from services.local.cache import load_local_cache
from utils.filter import filter_dict_fields
from schema.agents import Context
from agents.states import InjectorState
from services.sqlite import SQLiteDBService
from initializer import init

# ---------------- CONFIG ---------------- #
INPUT_CSV = "data/merged_test_input.csv"
DB_TABLE = "injections"
MAX_RETRIES = 3
RETRY_DELAY = 15  # seconds between retries
# ---------------------------------------- #

logger = logging.getLogger(__name__)


async def run_injection(index: int, row: pd.Series, llm: LLMService, cwe_cache: Dict[str, Any], db: SQLiteDBService):
    func_name = row["func_name"]

    # Skip if already exists
    existing = db.get_data_group(DB_TABLE, "func_name", func_name)
    if existing:
        logger.info(f"[{index}] Skipping '{func_name}' — already in DB.")
        return

    func_code = row["raw_code"]
    rois = row["roi"]
    lines = row["merged_roi_lines"]
    cwe_ids = row["cwe_ids"]

    cwe_fields = ["cwe_id", "cwe_name", "vulnerable_code_patterns", "code_injection_points"]
    cwe_details = filter_dict_fields(cwe_ids.split(","), cwe_cache, cwe_fields)

    injector_tools = InjectorTools()
    injector_agent = Injector(llm, injector_tools)

    initial_state = InjectorState(
        messages=[],
        context=Context(
            func_code=func_code,
            rois=rois,
            cwe_details=cwe_details,
            lines=lines,
            func_name=func_name,
        ),
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{index}] Injecting '{func_name}' (attempt {attempt}/{MAX_RETRIES})...")
            response = await injector_agent.run(initial_state)
            logger.info(f"[{index}] Injection successful for '{func_name}'.")
            return

        except Exception as e:
            logger.warning(f"[{index}] Attempt {attempt} failed: {e}")
            traceback.print_exc()

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(f"[{index}] Failed permanently after {MAX_RETRIES} attempts.")


async def main(start_index: int, end_index: int):
    # Initialize logging and database (via your init())
    init()
    logger.info(f"Starting batch injection (range: {start_index}–{end_index})")

    # Load dataset
    llm_input = await asyncio.to_thread(pd.read_csv, INPUT_CSV)
    total = len(llm_input)
    end_index = min(end_index, total)
    logger.info(f"Loaded {total} rows; processing rows {start_index}–{end_index - 1}.")

    # Init dependencies
    llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
    db = SQLiteDBService()
    cwe_cache = await load_local_cache()

    for i in range(start_index, end_index):
        row = llm_input.iloc[i]
        await run_injection(i, row, llm, cwe_cache, db)

    logger.info("✅ Batch injection completed.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch vulnerability injector runner.")
    parser.add_argument("--start", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end", type=int, default=10, help="End index (exclusive)")
    args = parser.parse_args()

    asyncio.run(main(args.start, args.end))
