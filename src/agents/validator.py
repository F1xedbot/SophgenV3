from services.llm import LLMService
from agents.tools import ValidatorTools 
from schema.agents import Context, ValidatorOutput
from agents.prompt import VALIDATOR_CONTEXT_PROMPT, VALIDATOR_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
from agents.mixins import AgentRetryMixin
import logging
import orjson

logger = logging.getLogger(__name__)

class Validator(AgentRetryMixin):
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm
        self.tools = ValidatorTools()
        self.agent = self._build_agent()

    def _build_agent(self):
        return self.llm.client.with_structured_output(ValidatorOutput)
    
    def _rebuild_client(self):
        self.llm.client = self.llm._init_client()
        self.agent = self._build_agent()

    def _dump_context(self, context: dict):
        return orjson.dumps(context, option=orjson.OPT_INDENT_2).decode("utf-8")

    async def build_messages(self) -> list[AnyMessage]:
        all_injections = await self.tools.get_injections(self.context.func_name)
        all_cwes = await self.tools.get_injection_cwes(all_injections)

        if not all_injections:
            logger.info(f"No injections found for: {self.context.func_name}")
            return []
        
        messsages = [
            SystemMessage(content=VALIDATOR_PROMPT),
            HumanMessage(content=VALIDATOR_CONTEXT_PROMPT.format(
                function_code=self.context.func_code,
                injections=self._dump_context(all_injections),
                cwe_details=self._dump_context(all_cwes)
            ))
        ]
        return messsages

    async def run(self, context: Context):
        self.context = context
        provider = self.llm.config.provider
        key_manager = self.llm.config.key_manager
        messages = await self.build_messages()
        if not messages:
            return {}

        response = await self.safe_invoke(
            invoke_fn=self.agent.ainvoke,
            provider=provider,
            key_manager=key_manager,
            rebuild_fn=self._rebuild_client,
            input=messages,
        )
        await self.tools.save_validations(response, self.context)
        return response   

