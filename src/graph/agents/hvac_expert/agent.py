"""HVAC Expert Agent — 暖通空调专家问答子图

所属层：graph/agents/hvac_expert
依赖：src.skills.hvac_expert_skill, src.graph.agents.base_agent
对接算法层：HVAC RAG 知识库
"""
from typing import Type
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

from src.graph.agents.base_agent import BaseAgent, BaseAgentState
from src.skills.hvac_expert_skill import HVACExpertSkill


class HVACExpertState(BaseAgentState):
    """HVAC Agent 专属状态"""
    hvac_knowledge: dict
    hvac_context_hint: dict


class HVACExpertAgent(BaseAgent):
    """HVAC 专家 Agent（封装 HVACExpertSkill 为 Subgraph）"""

    def __init__(self):
        self.skill = HVACExpertSkill()

    @property
    def name(self) -> str:
        return "hvac_expert"

    @property
    def description(self) -> str:
        return "暖通空调专家问答（规范查询、能效计算、故障诊断、节能优化）"

    @property
    def state_schema(self) -> Type[TypedDict]:
        return HVACExpertState

    def build_graph(self) -> StateGraph:
        """构建 HVAC 子图（复用现有 Skill 逻辑）"""
        graph = StateGraph(HVACExpertState)

        def hvac_node(state: HVACExpertState):
            """调用 HVACExpertSkill 执行逻辑"""
            # 直接调用现有 Skill 的 execute 方法
            tool_results = []  # HVAC Skill 通过 state 获取 hvac_knowledge
            skill_updates = self.skill.execute(tool_results, state)
            return {**skill_updates, "final_report": state.get("final_report", "")}

        graph.add_node("hvac_process", hvac_node)
        graph.set_entry_point("hvac_process")
        graph.set_finish_point("hvac_process")

        return graph.compile()
