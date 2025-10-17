from services.llm import LLMService
from agents.prompt import RESEARCHER_PROMPT
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage, AIMessage
from agents.states import ResearcherState
from agents.tools import BaseTools
from agents.mixins import AgentRetryMixin
from schema.agents import ResearcherSchema
import orjson
from utils.filter import filter_json_response

class Researcher(AgentRetryMixin):
    def __init__(self, llm: LLMService, tools: BaseTools) -> None:
        self.llm = llm
        self.tools = tools
        self.state_schema = ResearcherState
        self.agent = self._build_agent()

    def _build_agent(self):
        return create_react_agent(
            model=self.llm.client,
            tools=[self.tools.engine],
            state_schema=self.state_schema,
            prompt=self.build_messages,
        )
    
    def _rebuild_client(self, new_key: str):
        self.llm.client = self.llm._init_client(new_key)
        self.agent = self._build_agent()

    def build_messages(self, state: ResearcherState) -> list[AnyMessage]:
        messages = [
            SystemMessage(content=RESEARCHER_PROMPT),
            HumanMessage(str(state.cwe_id)),
            *state.messages
        ]
        return messages
    
    async def run(self, state: ResearcherState) -> ResearcherState:
        """
        Invoke the agent graph with the provided state, handling both dict and Pydantic context.
        """
        try:
            state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
            initial_state = self.state_schema(**state_data)

            provider = self.llm.config.provider
            key_manager = self.llm.config.key_manager

            result = await self.safe_invoke(
                invoke_fn=self.agent.ainvoke,
                provider=provider,
                key_manager=key_manager,
                rebuild_fn=self._rebuild_client,
                input=initial_state,
            )

            response: AIMessage = result["messages"][-1]
            content = filter_json_response(response.content)

            try:
                payload = orjson.loads(content)
            except orjson.JSONDecodeError:
                raise ValueError(f"Response content is not valid JSON:\n{content}")

            return ResearcherSchema(**payload)
        
        except Exception as e:
            raise RuntimeError(f"Agent run failed: {e}") from e

