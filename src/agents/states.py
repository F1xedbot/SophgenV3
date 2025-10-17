from schema.agents import Context
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic

class InjectorState(AgentStatePydantic):
    context: Context

class ResearcherState(AgentStatePydantic):
    cwe_id: str