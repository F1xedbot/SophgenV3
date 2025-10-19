from langgraph.prebuilt.chat_agent_executor import AgentStatePydantic

class ResearcherState(AgentStatePydantic):
    cwe_id: str