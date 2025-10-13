import inspect
from typing import List, Callable, Annotated, Optional
from langgraph.prebuilt import InjectedState
from schema.agents import InjectionSchema, ValidationOuput, Context
from agents.states import InjectorState
from services.sqlite import SQLiteDBService
from helpers.pydantic_to_sql import flatten_pydantic
from config.agent import INJECTOR_TOOL_CONFIG, VALIDATOR_TOOL_CONFIG

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
    def __init__(self, config: Optional[dict] | None = INJECTOR_TOOL_CONFIG):
        super().__init__()
        self.config = config
        self.table_name = self.config["table_name"]
        self.db = SQLiteDBService()

    def add_injections(
        self,
        injections: InjectionSchema | list[InjectionSchema],
        state: Annotated[InjectorState, InjectedState],
    ) -> str:
        """
        Add one or more CWE injections.

        Accepts a single InjectionSchema or a list.
        Skips injections where transformed_code == original_pattern.
        Returns a message per injection (ROI + CWE + status).
        """
        # Normalize to list
        if not injections:
            return "No injections provided; nothing added."
        if isinstance(injections, InjectionSchema):
            injections = [injections]

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
            self.db.save_data(self.table_name, injection_data)

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

    def get_injections(self, func_name: str) -> dict:
        """
        Retrieve all injections for a given function name,
        filtering out excluded keys from each record.
        """
        if not func_name:
            return []

        all_injections = self.db.get_data_group(
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
    
    def save_validations(self, validations: ValidationOuput, context: Context) -> bool:
        """
        Save all validation results from ValidationOuput to the database.
        """
        if not validations or not validations.validation_results:
            return False
        
        roi_lines = context.lines.split('\n')

        for item in validations.validation_results:
            validation_data = flatten_pydantic(item)
            validation_data["func_name"] = context.func_name
            validation_data["lines"] = roi_lines[item.roi_index - 1]
            self.db.save_data(self.table_name, validation_data)
            
        return True

