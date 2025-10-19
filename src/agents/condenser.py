from agents.mixins import AgentRetryMixin
from services.llm import LLMService
from schema.agents import CondenserSchema
from agents.tools import CondenserTools
from agents.prompt import CONDENSER_PROMPT, CONDERSER_CONTEXT_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage
import logging
import orjson

logger = logging.getLogger(__name__)

class KnowledgeCondenser(AgentRetryMixin):
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm
        self.tools = CondenserTools()
        self.agent = self._build_agent()
    
    def _build_agent(self):
        return self.llm.client.with_structured_output(CondenserSchema)
    
    def _rebuild_client(self):
        self.llm.client = self.llm._init_client()
        self.agent = self._build_agent()

    def _dump_context(self, context: dict):
        return orjson.dumps(context, option=orjson.OPT_INDENT_2).decode("utf-8")

    async def build_messages(self) -> list[AnyMessage]:
        feedbacks = await self.tools.get_feedbacks([self.cwe_id])
        latest_strategy = await self.tools.get_latest_strategy(self.cwe_id, self.interval)
        cwe_details = await self.tools.get_cwe_details([self.cwe_id])

        if not feedbacks or not cwe_details:
            logger.info(f"No feedbacks or cwe details found for: {self.cwe_id}")
            return []
        
        messsages = [
            SystemMessage(content=CONDENSER_PROMPT),
            HumanMessage(content=CONDERSER_CONTEXT_PROMPT.format(
                previous_strategies=self._dump_context(latest_strategy),
                feedbacks=self._dump_context(feedbacks),
                cwe_details=self._dump_context(cwe_details)
            ))
        ]
        return messsages
    
    async def run(self, cwe_id: str, support_count: int, interval: int):
        self.cwe_id = cwe_id
        self.support_count = support_count
        self.interval = interval
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
        await self.tools.save_cwe_lessons(response,  self.support_count)
        return response  
