"""UI Router Agent — 监控数据查询与页面导航子图

所属层：graph/agents/ui_router
依赖：src.skills.ui_router_skill, src.graph.agents.base_agent
对接算法层：福加运营数据 REST API
"""
from typing import Type
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

from src.graph.agents.base_agent import BaseAgent, BaseAgentState
from src.skills.ui_router_skill import UIRouterSkill


class UIRouterState(BaseAgentState):
    """UI Router Agent 专属状态"""
    page_context: dict
    pending_actions: list


class UIRouterAgent(BaseAgent):
    """UI Router Agent（封装 UIRouterSkill 为 Subgraph）"""

    def __init__(self):
        self.skill = UIRouterSkill()

    @property
    def name(self) -> str:
        return "ui_router"

    @property
    def description(self) -> str:
        return "监控页面查询与跳转（实时 COP、能耗、报警，下发页面跳转信号）"

    @property
    def state_schema(self) -> Type[TypedDict]:
        return UIRouterState

    def build_graph(self) -> StateGraph:
        """构建 UI Router 子图（复用现有 Skill 逻辑）"""
        graph = StateGraph(UIRouterState)

        def ui_router_node(state: UIRouterState):
            """调用 UIRouterSkill 执行逻辑"""
            tool_results = []
            skill_updates = self.skill.execute(tool_results, state)
            return {**skill_updates, "final_report": state.get("final_report", "")}

        graph.add_node("ui_router_process", ui_router_node)
        graph.set_entry_point("ui_router_process")
        graph.set_finish_point("ui_router_process")

        return graph.compile()
