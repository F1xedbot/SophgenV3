from services.llm import LLMService
from agents.prompt import INJECTOR_CONTEXT_PROMPT, INJECTOR_PROMPT
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from langgraph.graph import CompiledGraph
from agents.state import InjectorState
from agents.tools import BaseTools


class Injector:
    def __init__(self, llm: LLMService, tools: BaseTools, context: dict):
        self.llm = llm
        self.tools = tools
        self.state_schema = InjectorState
        self.context = context

        messages = self.build_messages()

        self.agent = create_react_agent(
            model=self.llm.client,
            tools=self.tools.get_tools(),
            state_schema=self.state_schema,
            prompt=messages,
        )

    def build_messages(self) -> list[AnyMessage]:
        """Construct system + human messages for the injection reasoning context."""
        required_keys = ["success_attempts", "function_code", "roi", "cwe_details"]

        missing = [k for k in required_keys if k not in self.context]
        if missing:
            raise KeyError(f"Missing required context keys: {missing}")

        return [
            SystemMessage(
                content=INJECTOR_PROMPT.format(
                    success_attempts=self.context["success_attempts"]
                )
            ),
            HumanMessage(
                content=INJECTOR_CONTEXT_PROMPT.format(
                    function_code=self.context["function_code"],
                    roi=self.context["roi"],
                    cwe_details=self.context["cwe_details"]
                )
            ),
        ]

    def build_workflow(self) -> CompiledGraph:
        return self.agent.compile()

    def run(self):
        graph = self.build_workflow()
        return graph.invoke()
