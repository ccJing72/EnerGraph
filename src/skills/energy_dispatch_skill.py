"""energy_dispatch_skill — 能源调度分析技能

所属层：skills
依赖：src.tools.parse_intent, query_timedit, verify_physics, fetch_aidc_cooling
对接 V3 引擎：PhysicsAI / TimeDiT / AIDC_Cooling

SOP：
  1. parse_business_intent → ConstraintMatrix
  2. query_timedit_forecast → 24h 负荷/光伏预测
  3. verify_physics_consistency → 物理合规验证
  4. fetch_aidc_cooling_status → 液冷协同状态（可选）
  5. 交由 v3_interpreter_skill 生成报告

Phase 4 时，各 Tool 内部从 Mock 切换为真实 HTTP，此 Skill 无需改动。

Prompt keys（src/config/prompts.yaml）：
  - energy_dispatch_intent : 能源调度意图解析指令（替代原 cognitive_parser）
"""
from typing import Any, Dict, List, Tuple

from src.skills.base_skill import BaseSkill


class EnergyDispatchSkill(BaseSkill):
    """能源调度分析技能。

    当前为骨架占位，Phase 4 T2-T4 实现真实 API 对接后完善。
    """

    name = "energy_dispatch"
    tools = [
        "parse_business_intent",
        "query_timedit_forecast",
        "verify_physics_consistency",
        "fetch_aidc_cooling_status",
    ]
    prompt_keys = ["energy_dispatch_intent", "interpreter_generator"]
    description = "能源调度分析（负荷预测、光伏协同、物理验证、排产计划）"

    def execute(
        self,
        tool_results: List[Tuple[str, Dict[str, Any], Dict[str, Any]]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """能源调度编排逻辑。Phase 4 完善，当前返回空更新。"""
        return {}
