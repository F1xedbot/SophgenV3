import asyncio
import logging
import traceback
import re
import orjson
from google.api_core.exceptions import ResourceExhausted
from typing import Dict

import pandas as pd

from utils.enums import LLMModels, AgentTable
from services.llm import LLMService
from agents.injector import Injector
from agents.validator import Validator
from agents.condenser import KnowledgeCondenser
from schema.agents import Context
from services.sqlite import SQLiteDBService
from initializer import init

from agents.tools import CondenserTools

# ---------------- CONFIG ---------------- #
INPUT_CSV = "data/merged_test_input.csv"
DB_TABLE = AgentTable.INJECTOR

MAX_RETRIES = 5
DEFAULT_RETRY_DELAY = 20      # seconds between retries
MAX_TASK_TIMEOUT = 120        # max time per injection attempt
RATE_LIMIT_DELAY = 5          # delay between successful LLM calls
# ---------------------------------------- #

logger = logging.getLogger(__name__)

async def run_batch_validation(batch: list[Context], validator: Validator):
    """
    Runs validation sequentially for a batch of successfully injected contexts.
    """
    if not batch:
        return

    logger.info(f"Running validation sequentially for {len(batch)} items...")
    
    for context in batch:
        func_name = context.func_name
        try:
            await validator.run(context)
            logger.info(f"   - ✅ Validation successful for '{func_name}'.")
        except Exception as e:
            logger.error(f"   - ❌ Validation failed for '{func_name}': {e}")
            traceback.print_exc()
            
    logger.info("Batch validation complete.")

async def run_condensation_checks(
    db: SQLiteDBService,
    condenser: KnowledgeCondenser,
    condense_every: int,
    previous_counts: Dict[str, int],
) -> Dict[str, int]:
    """
    Checks if any CWE's validation count has crossed a multiple of `condense_every`.
    If so, runs the KnowledgeCondenser for that CWE sequentially.
    """
    logger.info("Checking for knowledge condensation triggers...")
    current_counts = await db.get_all_counts_by_key("validations", "cwe_label")
    
    triggered_any = False
    for cwe_id, current_count in current_counts.items():
        previous_count = previous_counts.get(cwe_id, 0)

        if (previous_count // condense_every) < (current_count // condense_every):
            logger.info(
                f"CWE '{cwe_id}' reached a new threshold of {current_count}. "
                "Triggering knowledge condenser."
            )
            try:
                await condenser.run(cwe_id, current_count, condense_every)
                triggered_any = True
            except Exception as e:
                logger.error(f"Condenser run failed for '{cwe_id}': {e}")
                traceback.print_exc()

    if triggered_any:
        logger.info("Knowledge condensation run complete.")
    else:
        logger.info("No new condensation thresholds were met.")
        
    return current_counts


async def run_injection(index: int, row: pd.Series, llm: LLMService, db: SQLiteDBService) -> Context | None:
    func_name = row["func_name"]

    existing = await db.get_data_group(DB_TABLE, "func_name", func_name)
    if existing:
        logger.info(f"[{index}] Skipping '{func_name}' — already injected.")
        return None

    func_code = row["raw_code"]
    rois = row["roi"]
    lines = row["merged_roi_lines"]
    cwe_ids = row["cwe_ids"]

    condenser_tools = CondenserTools()
    merged_data = await condenser_tools.enrich_cwe_details(cwe_ids)
    cwe_details_str = orjson.dumps(merged_data, option=orjson.OPT_INDENT_2).decode("utf-8")

    injector_agent = Injector(llm)
    context = Context(func_code=func_code, func_name=func_name, lines=lines)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[{index}] Injecting '{func_name}' (attempt {attempt}/{MAX_RETRIES})...")
            await asyncio.wait_for(
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
            return context

        except asyncio.TimeoutError:
            logger.warning(f"[{index}] Timeout after {MAX_TASK_TIMEOUT}s for '{func_name}'. Skipping.")
            break
        except ResourceExhausted as e:
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
    return None

async def main(start_index: int, end_index: int, validate_every: int, condense_every: int):
    await init()
    logger.info(f"Starting batch injection (range: {start_index}–{end_index})")
    logger.info(f"Validation will run for every {validate_every} successful injections.")
    logger.info(f"Condensation will run when a CWE's count crosses a multiple of {condense_every}.")

    llm_input = await asyncio.to_thread(pd.read_csv, INPUT_CSV)
    total = len(llm_input)
    end_index = min(end_index, total)
    logger.info(f"Loaded {total} rows; processing rows {start_index}–{end_index - 1}.")

    llm = LLMService(LLMModels.GEMINI_2_5_FLASH)
    db = SQLiteDBService()
    validator = Validator(llm)
    condenser = KnowledgeCondenser(llm)

    validation_batch = []
    cwe_counts = await db.get_all_counts_by_key("validations", "cwe_label")
    logger.info(f"Initial CWE counts loaded: {cwe_counts}")

    for i in range(start_index, end_index):
        row = llm_input.iloc[i]
        successful_context = await run_injection(i, row, llm, db)

        if successful_context:
            validation_batch.append(successful_context)

        if len(validation_batch) >= validate_every:
            await run_batch_validation(validation_batch, validator)
            cwe_counts = await run_condensation_checks(db, condenser, condense_every, cwe_counts)
            validation_batch.clear()

    if validation_batch:
        logger.info("Processing final batch...")
        await run_batch_validation(validation_batch, validator)
        await run_condensation_checks(db, condenser, condense_every, cwe_counts)
        validation_batch.clear()

    logger.info("✅ Batch injection, validation, and condensation completed cleanly.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reliable batch vulnerability injector runner.")
    parser.add_argument("--start", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end", type=int, default=100, help="End index (exclusive)")
    parser.add_argument("--validate-every", type=int, default=10, help="Run validation after every N successful injections.")
    parser.add_argument("--condense-every", type=int, default=10, help="Run condenser when a CWE count crosses a multiple of N.")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.start, args.end, args.validate_every, args.condense_every))
    except Exception as e:
        logger.error("A critical error occurred and the script has stopped.")
        logger.error(f"Error Details: {e}")
        traceback.print_exc()
    finally:
        logger.info("Script finished. Cleanup complete.")