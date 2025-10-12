from services.llm import LLMService
from agents.tools import ValidatorTools 
from schema.agents import ValidationOuput, Context
import json
from agents.prompt import VALIDATOR_CONTEXT_PROMPT, VALIDATOR_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage

class Validator:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm
        self.tools = ValidatorTools()
        self.required_keys = ["func_code", "func_name", "lines"]

    def build_messages(self) -> list[AnyMessage]:
        all_injections = self.tools.get_injections(self.context.func_name)
        if not all_injections:
            raise AssertionError(f"No injections found for: {self.context.func_name}")

        messsages = [
            SystemMessage(content=VALIDATOR_PROMPT),
            HumanMessage(content=VALIDATOR_CONTEXT_PROMPT.format(
                function_code=self.context.func_code,
                injections=json.dumps(all_injections, indent=2, ensure_ascii=False)
            ))
        ]
        return messsages

    async def run(self, context: Context):
        context_dict = context.model_dump()
        missing = [k for k in self.required_keys if k not in context_dict]
        if missing:
            raise KeyError(f"Missing required validator keys: {missing}")
        
        self.context = context
        agent = self.llm.client.with_structured_output(ValidationOuput)
        messages = self.build_messages()
        response = await agent.ainvoke(messages)
        return self.tools.save_validations(response, self.context)        

