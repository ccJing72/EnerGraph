"""builder — 组装并编译 V3 LangGraph 状态图

所属层：graph
依赖：langgraph, src.graph.*
对接 V3 引擎：N/A
"""
from langgraph.graph import END, StateGraph

from src.graph.edges import should_continue
from src.graph.nodes import (
    cognitive_parser_node,
    interpreter_generator_node,
    v3_engine_router_node,
)
from src.graph.state import AgentState


def build_graph():
    """构建并返回编译后的 V3 调度 Agent 状态图。"""
    g = StateGraph(AgentState)

    g.add_node("cognitive_parser", cognitive_parser_node)
    g.add_node("v3_engine_router", v3_engine_router_node)
    g.add_node("interpreter_generator", interpreter_generator_node)

    g.set_entry_point("cognitive_parser")

    g.add_conditional_edges(
        "cognitive_parser",
        should_continue,
        {"tools": "v3_engine_router", "report": "interpreter_generator"},
    )
    g.add_edge("v3_engine_router", "cognitive_parser")
    g.add_edge("interpreter_generator", END)

    return g.compile()


# 全局单例，供 frontend 直接导入
graph = build_graph()
