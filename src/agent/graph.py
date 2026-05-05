"""LangGraph 状态图定义"""
from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes import agent_node, generate_report_node


def create_agent_graph():
    """创建 Agent 状态图 (ReAct 架构)"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("agent", agent_node)  # ReAct 决策节点
    workflow.add_node("generate_report", generate_report_node)

    # 定义流程 (预留条件边，便于后续扩展)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()
