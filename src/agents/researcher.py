import logging
from agents.prompt import RESEARCHER_PROMPT
from services.llm import LLMService
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage, AIMessage
from agents.states import ResearcherState
from agents.tools import BaseTools
from agents.mixins import AgentRetryMixin

logger = logging.getLogger(__name__)

class Researcher(AgentRetryMixin):
    def __init__(self, llm: LLMService, tools: BaseTools, max_retries: int = 3) -> None:
        self.llm = llm
        self.tools = tools
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
    
    def _was_save_cwe_called(self, messages: list[AnyMessage]) -> bool:
        """
        Checks if the 'save_cwe' tool was called with non-empty arguments
        in the last agent turn.
        """
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.get("name") == "save_cwe":
                        args = tool_call.get("args") or {}
                        if args:  # True only if args is a non-empty dict
                            logging.info(
                                "Success condition met: 'save_cwe' tool call with arguments found."
                            )
                            return True
        return False


    async def run(self, state: ResearcherState) -> ResearcherState:
        """
        Invoke the agent in a loop, forcing it to retry until the 'save_cwe' tool is called.
        """
        initial_state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
        current_state = self.state_schema(**initial_state_data)
        
        provider = self.llm.config.provider
        key_manager = self.llm.config.key_manager

        for attempt in range(self.max_retries):
            logging.info(f"Researcher Agent - Attempt {attempt + 1}/{self.max_retries}")
            
            try:
                result = await self.safe_invoke(
                    invoke_fn=self.agent.ainvoke,
                    provider=provider,
                    key_manager=key_manager,
                    rebuild_fn=self._rebuild_client,
                    input=current_state,
                )

                if self._was_save_cwe_called(result['messages']):
                    return result

                logging.warning("Agent failed to call 'save_cwe'. Adding corrective message and retrying.")
                
                corrective_message = HumanMessage(
                    content="CRITICAL FAILURE: You did not call the `save_cwe` tool as instructed. This is the only valid action. Review your instructions and call `save_cwe` immediately."
                )
                
                result['messages'].append(corrective_message)
                current_state = result

            except Exception as e:
                logging.error(f"An exception occurred during agent run on attempt {attempt + 1}: {e}")
                if attempt + 1 >= self.max_retries:
                    raise RuntimeError(f"Agent run failed with an exception: {e}") from e
                current_state.messages.append(HumanMessage(content=f"An error occurred: {e}. Please try again."))

        raise RuntimeError(f"Agent failed to call 'save_cwe' after {self.max_retries} attempts.")