from schema.agents import Context, ResearcherSchema
from typing import Optional
from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic

class InjectorState(AgentStatePydantic):
    context: Context

class ResearcherState(AgentStatePydantic):
    cwe_id: str
    structured_response: Optional[ResearcherSchema] = None