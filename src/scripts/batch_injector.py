import asyncio
import logging
import traceback
import re
import os
import orjson
from contextlib import suppress
from google.api_core.exceptions import ResourceExhausted

import pandas as pd

from utils.enums import LLMModels
from services.llm import LLMService
from agents.injector import Injector
from utils.filter import filter_list_fields
from schema.agents import Context
from services.sqlite import SQLiteDBService
from initializer import init

from agents.tools import CondenserTools

# ---------------- CONFIG ---------------- #
INPUT_CSV = "data/merged_test_input.csv"
DB_TABLE = "injections"

MAX_RETRIES = 5
DEFAULT_RETRY_DELAY = 20     # seconds between retries
MAX_TASK_TIMEOUT = 120       # max time per injection attempt
RATE_LIMIT_DELAY = 5         # delay between successful LLM calls
# ---------------------------------------- #

logger = logging.getLogger(__name__)

async def run_injection(index: int, row: pd.Series, llm: LLMService, db: SQLiteDBService):
    func_name = row["func_name"]

    # Skip if already exists
    existing = await db.get_data_group(DB_TABLE, "func_name", func_name)
    if existing:
        logger.info(f"[{index}] Skipping '{func_name}' — already injected.")
        return

    func_code = row["raw_code"]
    rois = row["roi"]
    lines = row["merged_roi_lines"]
    cwe_ids = row["cwe_ids"]

    # Retrieve CWE data
    cwe_data = await db.get_data_by_keys("researches", "cwe_id", cwe_ids.split(","))
    cwe_fields = [
        "cwe_id",
        "cwe_name",
        "vulnerable_code_patterns",
        "typical_code_context",
        "minimal_code_modification",
        "code_injection_points",
    ]
    cwe_details = filter_list_fields(cwe_ids.split(","), cwe_data, cwe_fields, key_field="cwe_id")

    if not cwe_details:
        cwe_details = cwe_ids.split(",")

    cwe_details_str = orjson.dumps(cwe_details, option=orjson.OPT_INDENT_2).decode("utf-8")

    injector_agent = Injector(llm)

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{index}] Injecting '{func_name}' (attempt {attempt}/{MAX_RETRIES})...")

            response = await asyncio.wait_for(
                injector_agent.run(
                    Context(
                        func_code=func_code,
                        rois=rois,
                        cwe_details=cwe_details_str,
                        lines=lines,
                        func_name=func_name,
                    ),
                ),
                timeout=MAX_TASK_TIMEOUT
            )

            logger.info(f"[{index}] ✅ Injection successful for '{func_name}'.")
            await asyncio.sleep(RATE_LIMIT_DELAY)
            return

        except asyncio.TimeoutError:
            logger.warning(f"[{index}] Timeout after {MAX_TASK_TIMEOUT}s for '{func_name}'. Skipping.")
            break

        except ResourceExhausted as e:
            # Handle LLM quota errors like "Please retry in 30s"
            match = re.search(r"Please retry in (\d+\.?\d*)s", str(e))
            wait_time = float(match.group(1)) + 1 if match else 60
            if attempt < MAX_RETRIES:
                logger.info(f"[{index}] Quota exceeded, waiting {wait_time:.1f}s before retry.")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[{index}] Quota failure after {MAX_RETRIES} attempts for '{func_name}'.")
                break

        except Exception as e:
            logger.warning(f"[{index}] Attempt {attempt} failed for '{func_name}': {e}")
            traceback.print_exc()

            if attempt < MAX_RETRIES:
                logger.info(f"[{index}] Waiting {DEFAULT_RETRY_DELAY}s before retry.")
                await asyncio.sleep(DEFAULT_RETRY_DELAY)
            else:
                logger.error(f"[{index}] Failed permanently after {MAX_RETRIES} attempts.")
                break


async def main(start_index: int, end_index: int):
    await init()
    logger.info(f"Starting batch injection (range: {start_index}–{end_index})")

    # Load CSV
    llm_input = await asyncio.to_thread(pd.read_csv, INPUT_CSV)
    total = len(llm_input)
    end_index = min(end_index, total)
    logger.info(f"Loaded {total} rows; processing rows {start_index}–{end_index - 1}.")

    llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)

    print(llm.config.api_key)
    db = SQLiteDBService()

    try:
        for i in range(start_index, end_index):
            row = llm_input.iloc[i]
            await run_injection(i, row, llm, db)

        logger.info("✅ Batch injection completed cleanly.")

    finally:
        # Cleanup LLM connections if present
        with suppress(Exception):
            if hasattr(llm, "client") and hasattr(llm.client, "close"):
                await llm.client.close()
        logger.info("Cleanup complete.")
        os._exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reliable batch vulnerability injector runner.")
    parser.add_argument("--start", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end", type=int, default=10, help="End index (exclusive)")
    args = parser.parse_args()

    asyncio.run(main(args.start, args.end))