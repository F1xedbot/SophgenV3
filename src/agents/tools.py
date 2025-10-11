import inspect
from typing import List, Callable, Annotated, Union
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel
from schema.agents import InjectionSchema
from agents.state import InjectorState

class BaseTools:
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
    def add_injection(
        self,
        injections: Union[InjectionSchema, dict, list[Union[InjectionSchema, dict]]],
        state: Annotated[InjectorState, InjectedState]
    ) -> str:
        """
        Add one or more CWE injections.

        Accepts:
        - Injection or list[Injection]
        - dict or list[dict] matching the Injection model

        Performs validation for each entry:
        - Skip None or invalid formats
        - Skip if transformed_code == original_pattern
        Returns a detailed message per injection (ROI + CWE + status).
        """
        if injections is None:
            return "No injections provided; nothing added."

        # Normalize input to list
        if not isinstance(injections, list):
            injections = [injections]

        messages = []

        for inj in injections:
            # --- Handle None ---
            if inj is None:
                messages.append("Injection is None, nothing added.")
                continue

            # --- Handle dict conversion ---
            if isinstance(inj, dict):
                try:
                    inj = InjectionSchema(**inj)
                except Exception as e:
                    messages.append(f"Invalid injection format: {e}")
                    continue

            # --- Validate content ---
            if inj.implementation.original_pattern == inj.implementation.transformed_code:
                messages.append(
                    f"ROI {getattr(inj, 'roi_index', '?')} ({getattr(inj, 'cwe_label', '?')}): "
                    f"No meaningful change detected; injection skipped."
                )
                continue

            # --- Add to state ---
            state.items.append(inj)
            messages.append(
                f"Injection for ROI {inj.roi_index} with CWE {inj.cwe_label} added successfully."
            )

        return "\n".join(messages)


