from schema.agents import InjectionSchema, Context
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic

class InjectorState(AgentStatePydantic):
    items: list[InjectionSchema] = []
    context: Context