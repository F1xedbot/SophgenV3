from services.llm import LLMService
from agents.prompt import INJECTOR_CONTEXT_PROMPT, INJECTOR_PROMPT
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from agents.states import InjectorState
from agents.tools import BaseTools
from agents.mixins import AgentRetryMixin
from utils.const import MAX_AGENT_RETRIES
import logging

logger = logging.getLogger(__name__)

class Injector(AgentRetryMixin):
    def __init__(self, llm: LLMService, tools: BaseTools, max_retries: int = MAX_AGENT_RETRIES) -> None:
        self.llm = llm
        self.tools = tools
        self.state_schema = InjectorState
        self.max_retries = max_retries
        self.agent = self._build_agent()
        self.required_keys = ["func_name", "func_code", "rois", "cwe_details", "lines"]

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

    def build_messages(self, state: InjectorState) -> list[AnyMessage]:
        """
        Build messages for the agent, ensuring system/human messages are not duplicated
        when the agent is retried after a corrective instruction.
        """
        messages = list(state.messages)

        # Only add system message if not already present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages.insert(0, SystemMessage(content=INJECTOR_PROMPT))

        # Only add initial HumanMessage if not present
        if not any(isinstance(m, HumanMessage) and str(state.cwe_id) in m.content for m in messages):
            messages.insert(1, HumanMessage(content=INJECTOR_CONTEXT_PROMPT.format(
                    function_code=state.context.func_code,
                    rois=state.context.rois,
                    cwe_details=state.context.cwe_details
            )))
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
        

        initial_state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
        current_state = self.state_schema(**initial_state_data)

        provider = self.llm.config.provider
        key_manager = self.llm.config.key_manager
        
        for attempt in range(self.max_retries):
            logger.info(f"Injector Agent - Attempt {attempt + 1}/{self.max_retries}")
            
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

