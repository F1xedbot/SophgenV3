import inspect
from typing import List, Callable, Annotated, Optional
from langgraph.prebuilt import InjectedState
from schema.agents import InjectionSchema, ValidationOuput, Context, ResearcherSchema
from agents.states import InjectorState, ResearcherState
from services.sqlite import SQLiteDBService
from helpers.pydantic_to_sql import flatten_pydantic
from config.agent import INJECTOR_TOOL_CONFIG, VALIDATOR_TOOL_CONFIG, RESEARCHER_TOOL_CONFIG
from utils.decorators import exclude_tool
from langchain_tavily import TavilySearch
from pydantic import parse_raw_as
import logging
from services.local.cache import read_cache, update_cache

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

    async def save_cwe(self, cwe_info: ResearcherSchema | str | dict) -> bool:
        """
        Save a CWE entry (from ResearcherSchema) into the database.
        Returns True on success, False otherwise.
        """
        if not cwe_info:
            return False
        
        try:
            if isinstance(cwe_info, str):
                cwe_obj = parse_raw_as(ResearcherSchema, cwe_info)
            elif isinstance(cwe_info, dict):
                cwe_obj = ResearcherSchema(**cwe_info)
            else:
                cwe_obj = cwe_info  # probably already a ResearcherSchema
        except Exception as e:
            logging.exception(f"Failed to parse cwe_info: {e}")
            return False
        
        logger.info(f"Calling `save_cwe` on {cwe_info.cwe_id}")

        try:
            data = flatten_pydantic(cwe_info)
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

    async def add_injection(
        self,
        injections: list[InjectionSchema],
        state: Annotated[InjectorState, InjectedState]
    ) -> str:
        """
        Add CWE injections from a list of InjectionSchema objects.

        Skips injections where transformed_code == original_pattern.
        Returns a message per injection (ROI + CWE + status).
        """
        if not injections:
            return "No injections provided; nothing added."

        messages = []
        roi_lines = state.context.lines.split('\n')

        for inj in injections:
            if inj.original_pattern == inj.transformed_code:
                messages.append(
                    f"ROI {inj.roi_index} ({inj.cwe_label}): No meaningful change; skipped."
                )
                continue

            injection_data = flatten_pydantic(inj)
            injection_data["func_name"] = state.context.func_name
            injection_data["lines"] = roi_lines[inj.roi_index - 1]
            await self.db.save_data(self.table_name, injection_data)

            messages.append(
                f"Injection for ROI {inj.roi_index} with CWE {inj.cwe_label} added successfully."
            )

        return "\n".join(messages)
    
class ValidatorTools(BaseTools):
    def __init__(self, config: Optional[dict] | None = VALIDATOR_TOOL_CONFIG):
        super().__init__()
        self.config = config
        self.table_name = self.config["table_name"]
        self.injection_table = self.config["injection_table"]
        self.injection_group_key = self.config["injection_group_key"]
        self.excluded_keys = self.config['excluded_keys']

    @exclude_tool
    async def get_injections(self, func_name: str) -> dict:
        """
        Retrieve all injections for a given function name,
        filtering out excluded keys from each record.
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

        return filtered
    
    @exclude_tool
    async def save_validations(self, validations: ValidationOuput, context: Context) -> bool:
        """
        Save all validation results from ValidationOuput to the database.
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
