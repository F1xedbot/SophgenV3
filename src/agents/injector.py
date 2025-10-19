from services.llm import LLMService
from agents.prompt import INJECTOR_CONTEXT_PROMPT, INJECTOR_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from agents.tools import InjectorTools
from schema.agents import InjectorOutput, Context
from agents.mixins import AgentRetryMixin
from utils.const import MAX_AGENT_RETRIES
import logging

logger = logging.getLogger(__name__)

class Injector(AgentRetryMixin):
    def __init__(self, llm: LLMService, max_retries: int = MAX_AGENT_RETRIES) -> None:
        self.llm = llm
        self.tools = InjectorTools()
        self.max_retries = max_retries
        self.agent = self._build_agent()
        self.required_keys = ["rois", "cwe_details"]

    def _build_agent(self):
        return self.llm.client.with_structured_output(InjectorOutput)
    
    def _rebuild_client(self):
        self.llm.client = self.llm._init_client()
        self.agent = self._build_agent()

    def build_messages(self, messages: list[AnyMessage]) -> list[AnyMessage]:
        """
        Build messages for the agent, ensuring system/human messages are not duplicated
        when the agent is retried after a corrective instruction.
        """
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages.insert(0, SystemMessage(content=INJECTOR_PROMPT))
        if not any(isinstance(m, HumanMessage) for m in messages):
            messages.insert(1, HumanMessage(content=INJECTOR_CONTEXT_PROMPT.format(
                    function_code=self.context.func_code,
                    rois=self.context.rois,
                    cwe_details=self.context.cwe_details
            )))
        return messages
    
    async def run(self, context: Context):
        context_dict = context.model_dump()
        missing = [k for k in self.required_keys if k not in context_dict]
        if missing:
            raise KeyError(f"Missing required injector keys: {missing}")
        
        self.context = context
        provider = self.llm.config.provider
        key_manager = self.llm.config.key_manager
        messages = self.build_messages([])
        
        for attempt in range(self.max_retries):
            logger.info(f"Injector Agent - Attempt {attempt + 1}/{self.max_retries}")
            
            try:
                response = await self.safe_invoke(
                    invoke_fn=self.agent.ainvoke,
                    provider=provider,
                    key_manager=key_manager,
                    rebuild_fn=self._rebuild_client,
                    input=messages,
                )
                corrective_messages = await self.tools.save_injections(response, self.context)
                return response
                # messages.append(HumanMessage(content="CORRECTIVE MESSAGE: " + "\n".join(corrective_messages)))
            except Exception as e:
                logger.error(f"An exception occurred during agent run on attempt {attempt + 1}: {e}")
                raise RuntimeError(f"Agent run failed with an exception: {e}") from e
            
        raise RuntimeError(f"Agent failed to correct its mistakes after {self.max_retries} attempts.")

