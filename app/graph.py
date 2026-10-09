from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.nodes import (
    chitchat_node,
    generate_node,
    logger_node,
    relax_node,
    retrieve_node,
    route_after_retrieve,
    route_after_understand,
    understand_node,
)
from app.state import State


def build_graph(checkpointer=None):
    g = StateGraph(State)

    g.add_node("understand", understand_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("relax", relax_node)
    g.add_node("generate", generate_node)
    g.add_node("chitchat", chitchat_node)
    g.add_node("logger", logger_node)

    g.add_edge(START, "understand")
    g.add_conditional_edges(
        "understand", route_after_understand, {"retrieve": "retrieve", "chitchat": "chitchat"}
    )
    g.add_conditional_edges(
        "retrieve", route_after_retrieve, {"relax": "relax", "generate": "generate"}
    )
    g.add_edge("relax", "retrieve")
    g.add_edge("generate", "logger")
    g.add_edge("chitchat", "logger")
    g.add_edge("logger", END)

    return g.compile(checkpointer=checkpointer)


app = build_graph(MemorySaver())