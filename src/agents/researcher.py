import logging
from agents.prompt import RESEARCHER_PROMPT
from services.llm import LLMService
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from agents.states import ResearcherState
from agents.tools import ResearcherTools
from agents.mixins import AgentRetryMixin
from utils.const import MAX_AGENT_RETRIES

logger = logging.getLogger(__name__)

class Researcher(AgentRetryMixin):
    def __init__(self, llm: LLMService, max_retries: int = MAX_AGENT_RETRIES) -> None:
        self.llm = llm
        self.tools = ResearcherTools()
        self.state_schema = ResearcherState
        self.max_retries = max_retries
        self.agent = self._build_agent()

    def _build_agent(self):
        return create_react_agent(
            model=self.llm.client,
            tools=self.tools.get_tools(),
            state_schema=self.state_schema,
            prompt=self.build_messages,
        )
    
    def _rebuild_client(self):
        self.llm.client = self.llm._init_client()
        self.agent = self._build_agent()

    def build_messages(self, state: ResearcherState) -> list[AnyMessage]:
        """
        Build messages for the agent, ensuring system/human messages are not duplicated
        when the agent is retried after a corrective instruction.
        """
        messages = list(state.messages)

        # Only add system message if not already present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages.insert(0, SystemMessage(content=RESEARCHER_PROMPT))

        # Only add initial HumanMessage if not present
        if not any(isinstance(m, HumanMessage) for m in messages):
            messages.insert(1, HumanMessage(content=f"CWE-ID: {str(state.cwe_id)}"))

        return messages

    async def run(self, state: ResearcherState):
        """
        Invoke the agent in a loop, forcing it to retry until all critical tools are called.
        """
        initial_state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
        current_state = self.state_schema(**initial_state_data)

        provider = self.llm.config.provider
        key_manager = self.llm.config.key_manager

        for attempt in range(self.max_retries):
            logger.info(f"Researcher Agent - Attempt {attempt + 1}/{self.max_retries}")
            
            try:
                result = await self.safe_invoke(
                    invoke_fn=self.agent.ainvoke,
                    provider=provider,
                    key_manager=key_manager,
                    rebuild_fn=self._rebuild_client,
                    input=current_state,
                )
                status, corrective_message = self.all_critical_tools_called(result['messages'], self.tools.get_critical_tools())
                if status:
                    return result
                logger.warning("Agent failed to call any critical tools. Adding corrective message and retrying.")
                result['messages'].append(corrective_message)
                current_state = result

            except Exception as e:
                logger.error(f"An exception occurred during agent run on attempt {attempt + 1}: {e}")
                raise RuntimeError(f"Agent run failed with an exception: {e}") from e
            
        raise RuntimeError(f"Agent failed to call any critical tools after {self.max_retries} attempts.")