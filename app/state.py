from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class State(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    intent: str
    query: str
    category: str
    area: str
    max_price: int
    attempt: int
    relaxed: list[str]
    context: str
    sources: list[dict]
    trace: list[dict]