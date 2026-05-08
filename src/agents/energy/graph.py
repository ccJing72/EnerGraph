"""LangGraph StateGraph — ReAct 能源调度 Agent"""
from langgraph.graph import StateGraph, END

from src.schemas.agent_state import AgentState
from src.agents.energy.nodes import agent_node, tool_node, report_node, should_continue


def create_agent_graph():
    """构建并编译 ReAct 状态图."""
    g = StateGraph(AgentState)

    g.add_node("agent", agent_node)
    g.add_node("tools", tool_node)
    g.add_node("report", report_node)

    g.set_entry_point("agent")
    g.add_conditional_edges("agent", should_continue, {"tools": "tools", "report": "report"})
    g.add_edge("tools", "agent")
    g.add_edge("report", END)

    return g.compile()
