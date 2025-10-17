import asyncio
import logging
import pandas as pd
import traceback
from utils.enums import LLMModels
from services.llm import LLMService
from agents.validator import Validator
from schema.agents import Context
from services.sqlite import SQLiteDBService
from initializer import init

# ---------------- CONFIG ---------------- #
INPUT_CSV = "data/merged_test_input.csv"
DB_TABLE = "validations"
MAX_RETRIES = 3
RETRY_DELAY = 15  # seconds between retries
# ---------------------------------------- #

logger = logging.getLogger(__name__)


async def run_validation(index: int, row: pd.Series, llm: LLMService, db: SQLiteDBService):
    func_name = row["func_name"]

    # Skip if already validated
    existing = await db.get_data_group(DB_TABLE, "func_name", func_name)
    if existing:
        logger.info(f"[{index}] Skipping '{func_name}' — already in DB.")
        return

    func_code = row["raw_code"]
    lines = row["merged_roi_lines"]

    validator = Validator(llm)
    context = Context(
        func_code=func_code,
        func_name=func_name,
        lines=lines,
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{index}] Validating '{func_name}' (attempt {attempt}/{MAX_RETRIES})...")
            response = await validator.run(context)
            logger.info(f"[{index}] Validation successful for '{func_name}'.")
            return

        except Exception as e:
            logger.warning(f"[{index}] Attempt {attempt} failed: {e}")
            traceback.print_exc()

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(f"[{index}] Failed permanently after {MAX_RETRIES} attempts.")


async def main(start_index: int, end_index: int):
    await init()
    logger.info(f"Starting batch validation (range: {start_index}–{end_index})")

    # Load dataset
    llm_input = await asyncio.to_thread(pd.read_csv, INPUT_CSV)
    total = len(llm_input)
    end_index = min(end_index, total)
    logger.info(f"Loaded {total} rows; processing rows {start_index}–{end_index - 1}.")

    # Initialize services
    llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
    db = SQLiteDBService()

    # Run validator over range
    for i in range(start_index, end_index):
        row = llm_input.iloc[i]
        await run_validation(i, row, llm, db)

    logger.info("✅ Batch validation completed.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch function validator runner.")
    parser.add_argument("--start", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end", type=int, default=10, help="End index (exclusive)")
    args = parser.parse_args()

    asyncio.run(main(args.start, args.end))