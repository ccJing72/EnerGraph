"""skills — 业务技能注册表

所属层：skills（Tools 之上的业务推理层）
依赖：src.skills.*
对接 V3 引擎：N/A（由各 Skill 内部编排 Tools）

Skills 与 Tools 的分工：
  Tools = 原子执行层（确定性函数，强类型 I/O，不含 Prompt）
  Skills = 业务推理层（专属 Prompt + SOP 流程 + Tools 编排）

cognitive_parser 通过 SKILL_REGISTRY 获取技能描述，
决定激活哪个 Skill，再由 Skill 内部编排具体 Tools。
v3_engine_router 通过 get_skill() 统一调度，不依赖具体子类。
"""
from typing import Dict, Optional

from src.skills.base_skill import BaseSkill
from src.skills.hvac_expert_skill import HVACExpertSkill
from src.skills.energy_dispatch_skill import EnergyDispatchSkill
from src.skills.ui_router_skill import UIRouterSkill
from src.skills.v3_interpreter_skill import V3InterpreterSkill

# 技能注册表：key = 技能名，value = 技能实例
SKILL_REGISTRY: Dict[str, BaseSkill] = {
    "hvac_expert": HVACExpertSkill(),
    "energy_dispatch": EnergyDispatchSkill(),
    "ui_router": UIRouterSkill(),
    "v3_interpreter": V3InterpreterSkill(),
}

# 供 cognitive_parser 注入 system prompt 的技能描述菜单
SKILL_DESCRIPTIONS = {
    "hvac_expert": "暖通空调专家问答（规范查询、能效计算、故障诊断、节能优化）",
    "energy_dispatch": "能源调度分析（负荷预测、光伏协同、物理验证、排产计划）",
    "ui_router": "监控页面查询与跳转（实时 COP、能耗、报警，下发页面跳转信号）",
    "v3_interpreter": "V3 引擎数据解读（将物理残差/SOC 曲线转化为 Markdown 报告）",
}


def get_skill(name: str) -> Optional[BaseSkill]:
    """工厂函数：按名称获取 Skill 实例。

    Args:
        name: 技能名（对应 SKILL_REGISTRY 的 key）

    Returns:
        BaseSkill 实例，不存在时返回 None
    """
    return SKILL_REGISTRY.get(name)


def get_matched_skills(tool_names: list) -> list:
    """根据本轮工具调用，返回匹配的 Skill 实例列表。

    Args:
        tool_names: 本轮 LLM 调用的工具名列表

    Returns:
        匹配的 BaseSkill 实例列表
    """
    matched = []
    for skill in SKILL_REGISTRY.values():
        if any(skill.has_tool(t) for t in tool_names):
            matched.append(skill)
    return matched
