from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from schema.agents import InjectionSchema

class InjectorState(TypedDict):
    messages: Annotated[list, add_messages]
    items: list[InjectionSchema] = []