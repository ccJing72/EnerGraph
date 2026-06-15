"""PowerAI Agent — 储能调度智能体子图（骨架）

所属层：graph/agents/powerai
依赖：src.skills.energy_dispatch_skill, src.graph.agents.base_agent
对接算法层：光伏预测/负荷预测/储能优化 MCP Server（待接入）
"""
from typing import Type
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

from src.graph.agents.base_agent import BaseAgent, BaseAgentState
from src.skills.energy_dispatch_skill import EnergyDispatchSkill


class PowerAIState(BaseAgentState):
    """PowerAI Agent 专属状态"""
    constraints: dict
    load_forecast: dict
    solar_forecast: dict
    dispatch_plan: dict


class PowerAIAgent(BaseAgent):
    """PowerAI 储能调度 Agent（骨架，待完善 MCP 接入）"""

    def __init__(self):
        self.skill = EnergyDispatchSkill()

    @property
    def name(self) -> str:
        return "powerai"

    @property
    def description(self) -> str:
        return "能源调度分析（负荷预测、光伏协同、物理验证、排产计划）"

    @property
    def state_schema(self) -> Type[TypedDict]:
        return PowerAIState

    def build_graph(self) -> StateGraph:
        """构建 PowerAI 子图（当前为骨架，待接入 MCP Server）"""
        graph = StateGraph(PowerAIState)

        def powerai_node(state: PowerAIState):
            """调用 EnergyDispatchSkill 执行逻辑"""
            tool_results = []
            skill_updates = self.skill.execute(tool_results, state)
            return {**skill_updates, "final_report": state.get("final_report", "PowerAI 功能开发中，敬请期待")}

        graph.add_node("powerai_process", powerai_node)
        graph.set_entry_point("powerai_process")
        graph.set_finish_point("powerai_process")

        return graph.compile()
