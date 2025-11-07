import inspect
from typing import List, Callable, Annotated, Optional
from langgraph.prebuilt import InjectedState
from schema.agents import ValidatorOutput, Context, ResearcherSchema, InjectorOutput, CondenserSchema
from agents.states import ResearcherState
from services.sqlite import SQLiteDBService
from helpers.pydantic_to_sql import flatten_pydantic
from config.agent import INJECTOR_TOOL_CONFIG, VALIDATOR_TOOL_CONFIG, RESEARCHER_TOOL_CONFIG, CONDENSER_TOOL_CONFIG
from utils.decorators import exclude_tool, critical_tool
from langchain_tavily import TavilySearch
from utils.common import hash_data
from utils.filter import remove_c_comments, filter_list_fields
import logging
from services.local.cache import read_cache, update_cache
import random

logger = logging.getLogger(__name__)

class BaseTools:
    def __init__(self):
        self.db = SQLiteDBService()

    def get_tools(self) -> List[Callable]:
        """
        Collects callable tool methods from subclasses.
        """
        tools = []
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            # Skip private methods, BaseTools methods, and excluded decorators
            if (
                name.startswith("_")
                or func.__func__ in BaseTools.__dict__.values()
                or getattr(func.__func__, "_exclude_tool", False)
            ):
                continue
            tools.append(func)
        return tools

    def get_critical_tools(self) -> List[Callable]:
        """
        Collects callable critical tools from subclasses.
        """
        tools = []
        for _, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if (getattr(func.__func__, "_critical_tool", False)):
                tools.append(func.__name__)
        return tools

    
class ResearcherTools(BaseTools):
    def __init__(self, config: Optional[dict] | None = RESEARCHER_TOOL_CONFIG):
        super().__init__()
        self.engine = TavilySearch(max_results=config["max_results"])
        self.table_name = config["table_name"]
        self.fresh_cache = config["fresh_cache"]

    async def web_search(self, query: str, state: Annotated[ResearcherState, InjectedState]) -> str:
        """Perform a web search and return a readable summary of results."""

        if not self.fresh_cache:
            cached_result = await read_cache(state.cwe_id)
            if cached_result:
                return cached_result.get("summary", "")
        try:
            result = await self.engine.ainvoke({"query": query})
            results = result.get("results", [])
            if not results:
                return "No relevant search results found."

            summary = []
            for r in results:
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("content", "")
                summary.append(f"{title}\n{url}\n{snippet}\n")

            summary_text = "\n".join(summary)
            await update_cache(state.cwe_id, {"summary": summary_text, "query": query})
            return summary_text
        except Exception as e:
            return f"[Search error: {e}]"
        
    @critical_tool
    async def save_cwe(self, cwe_info: ResearcherSchema) -> bool:
        """
        Save a CWE entry (from ResearcherSchema) into the database.
        Returns True on success, False otherwise.
        """
        if not cwe_info:
            return False
        
        try:
            if isinstance(cwe_info, str):
                cwe_obj = ResearcherSchema.model_validate_json(cwe_info)    
            elif isinstance(cwe_info, dict):
                cwe_obj = ResearcherSchema(**cwe_info)
            else:
                cwe_obj = cwe_info

        except Exception as e:
            logging.exception(f"Failed to parse cwe_info: {e}")
            return False
        
        logger.info(f"Calling `save_cwe` on {cwe_obj.cwe_id}")

        try:
            data = flatten_pydantic(cwe_obj)
            await self.db.save_data(self.table_name, data)
            return True
        except Exception as e:
            logging.exception(f"Failed to save CWE: {e}")
            return False

class InjectorTools(BaseTools):
    def __init__(self, config: Optional[dict] | None = INJECTOR_TOOL_CONFIG):
        super().__init__()
        self.config = config
        self.table_name = self.config["table_name"]
        self.db = SQLiteDBService()

    async def save_injections(
        self,
        injections: InjectorOutput,
        context: Context
    ) -> list[str]:
        """
        Save CWE injections from InjectorOutput.

        Skips any injection where `transformed_code` matches `original_pattern`.
        Returns a list of messages describing failed injections, including ROI, CWE, and status.
        """
        if not injections or not injections.injection_results:
            return ["No injections provided; at least one is required."]

        messages = []
        roi_lines = context.lines.split('\n')

        for inj in injections.injection_results:
            if remove_c_comments(inj.original_pattern) == remove_c_comments(inj.transformed_code):
                messages.append(
                    f"ROI {inj.roi_index} ({inj.cwe_label}): No meaningful change;"
                )
                continue

            injection_data = flatten_pydantic(inj)
            injection_data["func_name"] = context.func_name
            injection_data["lines"] = roi_lines[inj.roi_index - 1]
            injection_data["ref_hash"] = hash_data(injection_data)
            await self.db.save_data(self.table_name, injection_data)

        return messages
    
class ValidatorTools(BaseTools):
    def __init__(self, config: Optional[dict] | None = VALIDATOR_TOOL_CONFIG):
        super().__init__()
        self.config = config
        self.table_name = self.config["table_name"]
        self.injection_table = self.config["injection_table"]
        self.injection_group_key = self.config["injection_group_key"]
        self.excluded_keys = self.config['excluded_keys']
        self.merge_key = self.config["merge_key"]

    @exclude_tool
    async def get_injections(self, func_name: str) -> list[dict]:
        """
        Retrieve all injections for a given function name,
        filtering out excluded keys from each record,
        and deduplicate by 'ref_hash'.
        """
        if not func_name:
            return []

        all_injections = await self.db.get_data_group(
            self.injection_table,
            self.injection_group_key,
            func_name
        )

        if not all_injections:
            return []

        filtered = [
            {k: v for k, v in row.items() if k not in self.excluded_keys}
            for row in all_injections
        ]

        seen = set()
        deduped = []
        for row in filtered:
            merge_key = row.get(self.merge_key)
            if merge_key not in seen:
                seen.add(merge_key)
                deduped.append(row)

        return deduped
    
    @exclude_tool
    async def get_injection_cwes(self, injections: list[dict]) -> list[dict]:
        condenser_tools = CondenserTools()
        cwe_ids = {inj["cwe_label"].strip() for inj in injections if inj.get("cwe_label")}
        if not cwe_ids:
            return []
        cwe_id_str = ",".join(sorted(cwe_ids))

        enriched_details = await condenser_tools.enrich_cwe_details(
            cwe_ids=cwe_id_str,
            use_latest_strategy=False
        )

        return enriched_details
    
    @exclude_tool
    async def save_validations(self, validations: ValidatorOutput, context: Context) -> bool:
        """
        Save all validation results from ValidatiorOuput to the database.
        Returns True on success, False otherwise.
        """
        if not validations or not validations.validation_results:
            return False
        
        try:
            roi_lines = context.lines.split('\n')
            for item in validations.validation_results:
                validation_data = flatten_pydantic(item)
                validation_data["func_name"] = context.func_name
                validation_data["lines"] = roi_lines[item.roi_index - 1]
                await self.db.save_data(self.table_name, validation_data)
            return True
        except Exception as e:
            logging.exception(f"Failed to save validations: {e}")
            return False

class CondenserTools(BaseTools):
    def __init__(self, config: Optional[dict] | None = CONDENSER_TOOL_CONFIG):
        super().__init__()
        self.config = config
        self.table_name = self.config["table_name"]
        self.references = self.config["references"]
        self.ref_key = self.config["ref_key"]
        self.merge_key = self.config["merge_key"]
        self.excluded_keys = self.config["excluded_keys"]
        self.cwe_table = self.config["cwe_table"]
        self.cwe_table_ref_key = self.config["cwe_table_ref_key"]

    async def save_cwe_lessons(self, cwe_lesson: CondenserSchema, support_count: int) -> bool:
        if not cwe_lesson: 
            return False
        try:
            cwe_lesson_data = flatten_pydantic(cwe_lesson)
            cwe_lesson_data["support_count"] = support_count
            await self.db.save_data(self.table_name, cwe_lesson_data, replace=True, match_fields=[self.ref_key])
            return True
        except Exception as e:
            logging.exception(f"Failed to save cwe lesson: {e}")
            return False

    async def get_latest_strategy(self, cwe_id: str) -> dict | None:
        """
        Retrieve the most recent (latest) strategy entry for a given CWE ID.
        """
        previous = await self.db.get_data_group(self.table_name, self.ref_key, cwe_id)
        if not previous:
            return None

        # Sort or pick latest by timestamp
        latest_entry = max(previous, key=lambda x: x.get("timestamp", 0))

        filtered = {
            k: v
            for k, v in latest_entry.items()
            if k not in self.excluded_keys
        }
        filtered["source"] = "condensed"
        return filtered
    
    async def enrich_cwe_details(self, cwe_ids: str, use_latest_strategy: bool = True) -> list[dict]:
        """
        Retrieve CWE details for multiple IDs.
        Prefer the latest strategy details when available,
        otherwise fall back to the default CWE details.
        """
        cwe_id_list = [c.strip() for c in cwe_ids.split(",") if c.strip()]
        cwe_details = await self.get_cwe_details(cwe_id_list)

        if isinstance(cwe_details, dict):
            cwe_details = [cwe_details]

        merged_results = []
        for cwe_id in cwe_id_list:
            match = next((c for c in cwe_details if c.get("cwe_id") == cwe_id), None)

            if not use_latest_strategy:
                merged_results.append(match or {"cwe_id": cwe_id})
                continue

            added_cwe_details = await self.get_latest_strategy(cwe_id)

            if added_cwe_details:
                merged_results.append(added_cwe_details)
            elif match:
                merged_results.append(match)
            else:
                merged_results.append({"cwe_id": cwe_id})

        return merged_results

    async def get_cwe_details(self, cwe_ids: list[str]) -> dict:
        cwe_data = await self.db.get_data_by_keys(self.cwe_table, self.cwe_table_ref_key, cwe_ids)
        cwe_fields = [
            "cwe_id",
            "cwe_name",
            "vulnerable_code_patterns",
            "typical_code_context",
            "minimal_code_modification",
            "code_injection_points",
        ]
        cwe_details = filter_list_fields(cwe_ids, cwe_data, cwe_fields, key_field=self.cwe_table_ref_key)
        return cwe_details

    async def get_feedbacks(
        self, cwe_id: str, samples: int = 30, limit: int | None = 10
    ) -> list[dict]:
        """
        Fetch feedback data for a given CWE ID across multiple reference tables,
        merge entries by the merge_key, then randomly sample up to `limit` items
        from the `samples` newest entries (by timestamp).
        """
        all_data = []

        for ref in self.references:
            rows = await self.db.get_data_by_keys(ref, self.ref_key, cwe_id)
            all_data.extend(rows)

        merged: dict[str, dict] = {}
        for row in all_data:
            label = row.get(self.merge_key)
            if not label:
                continue
            merged[label] = {**merged.get(label, {}), **row}

        sorted_rows = sorted(
            merged.values(),
            key=lambda x: x.get("timestamp") or "",
            reverse=True
        )

        sampled_pool = sorted_rows[:samples]

        if limit is not None and len(sampled_pool) > limit:
            sampled_pool = random.sample(sampled_pool, limit)

        filtered = [
            {k: v for k, v in row.items() if k not in self.excluded_keys}
            for row in sampled_pool
        ]

        return filtered





        


