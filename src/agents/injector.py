from services.llm import LLMService
from agents.prompt import INJECTOR_CONTEXT_PROMPT, INJECTOR_PROMPT
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from agents.state import InjectorState
from agents.tools import BaseTools

class Injector:
    def __init__(self, llm: LLMService, tools: BaseTools) -> None:
        self.llm = llm
        self.tools = tools
        self.state_schema = InjectorState
        self.agent = create_react_agent(
            model=self.llm.client,
            tools=self.tools.get_tools(),
            state_schema=self.state_schema,
            prompt=self.build_messages,
        )
        self.required_keys = ["raw_code", "roi", "cwe_details"]

    def build_messages(self, state: InjectorState) -> list[AnyMessage]:
        """Construct system + human messages for the injection reasoning context."""
        messages = [
            SystemMessage(content=INJECTOR_PROMPT),
            HumanMessage(
                content=INJECTOR_CONTEXT_PROMPT.format(
                    function_code=state.context.raw_code,
                    roi=state.context.roi,
                    cwe_details=state.context.cwe_details
                )
            ),
            *state.messages
        ]
        print(messages)
        return messages
    
    async def run(self, state: InjectorState) -> InjectorState:
        """
        Invoke the agent graph with the provided state, handling both dict and Pydantic context.
        """
        if hasattr(state.context, "model_dump"):
            context_dict = state.context.model_dump()
        elif isinstance(state.context, dict):
            context_dict = state.context
        else:
            raise TypeError(f"Unsupported context type: {type(state.context)}")

        missing = [k for k in self.required_keys if k not in context_dict]
        if missing:
            raise KeyError(f"Missing required injector keys: {missing}")

        try:
            state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
            initial_state = self.state_schema(**state_data)
            graph = self.agent
            result = graph.invoke(initial_state)
            return result
        except Exception as e:
            raise RuntimeError(f"Agent run failed: {e}") from e

