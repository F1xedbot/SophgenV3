import inspect
from typing import List, Callable, Annotated, Optional
from langgraph.prebuilt import InjectedState
from schema.agents import InjectionSchema
from agents.states import InjectorState
from services.sqlite import SQLiteDBService
from helpers.pydantic_to_sql import flatten_pydantic
from config.agent import INJECTOR_CONFIG, VALIDATOR_CONFIG

class BaseTools:
    def __init__(self):
        self.db = SQLiteDBService()

    def get_tools(self) -> List[Callable]:
        """
        Collects callable tool methods from subclasses.
        """
        tools = []
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            # Skip private methods and BaseTools methods
            if name.startswith("_") or func.__func__ in BaseTools.__dict__.values():
                continue
            tools.append(func)
        return tools


class InjectorTools(BaseTools):
    def __init__(self, config: Optional[dict] | None = INJECTOR_CONFIG):
        super().__init__()
        self.config = config
        self.table_name = self.config["table_name"]
        self.db = SQLiteDBService()

    def add_injection(
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

        for inj in injections:
            if inj.original_pattern == inj.transformed_code:
                messages.append(
                    f"ROI {inj.roi_index} ({inj.cwe_label}): No meaningful change; skipped."
                )
                continue

            injection_data = flatten_pydantic(inj)
            injection_data["func_name"] = state.func_name
            self.db.save_data(self.table_name, injection_data)

            messages.append(
                f"Injection for ROI {inj.roi_index} with CWE {inj.cwe_label} added successfully."
            )

        return "\n".join(messages)
    
class ValidatorTools(BaseTools):
    def __init__(self, config: Optional[dict] | None = VALIDATOR_CONFIG):
        super().__init__()
        self.config = config
        self.table_name = self.config["table_name"]
        self.injection_table = self.config["injection_table"]
        self.injection_group_key = self.config["injection_group_key"]

    def get_injections(self, func_name: str):
        if not func_name:
            return self.db.get_data_group(self.injection_table, self.injection_group_key, func_name)
        return []
