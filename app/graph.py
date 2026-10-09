from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.nodes import agent_node, logger_node
from app.state import State
from app.tools import ALL_TOOLS


def build_graph():
    g = StateGraph(State)

    g.add_node("agent", agent_node)
    g.add_node("tools", ToolNode(ALL_TOOLS))
    g.add_node("logger", logger_node)

    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: "logger"})
    g.add_edge("tools", "agent")
    g.add_edge("logger", END)

    return g.compile()


app = build_graph()
