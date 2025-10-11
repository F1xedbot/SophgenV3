import inspect
from typing import List, Callable, Annotated
from langgraph.prebuilt import InjectedState
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
            if inj.implementation.original_pattern == inj.implementation.transformed_code:
                messages.append(
                    f"ROI {inj.roi_index} ({inj.cwe_label}): No meaningful change; skipped."
                )
                continue

            state.items.append(inj)
            messages.append(
                f"Injection for ROI {inj.roi_index} with CWE {inj.cwe_label} added successfully."
            )

        return "\n".join(messages)



