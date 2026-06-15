"""energy_dispatch_skill — 能源调度分析技能（PowerAI 核心）

所属层：skills
依赖：src.tools.parse_intent
对接算法层：待 MCP 接入（负荷预测 / 光伏预测 / 储能调度优化）

SOP：
  1. parse_business_intent → ConstraintMatrix
  2. 调用算法模型层预测工具（待 MCP 接入）
  3. 评估储能调度策略
  4. 交由 v3_interpreter_skill 生成报告

Phase 4 时，算法模型通过 MCP Client 调用，此 Skill 编排调度流程。

Prompt keys（src/config/prompts.yaml）：
  - energy_dispatch_intent : 能源调度意图解析指令
"""
from typing import Any, Dict, List, Tuple

from src.skills.base_skill import BaseSkill


class EnergyDispatchSkill(BaseSkill):
    """能源调度分析技能。

    当前为骨架占位，待算法团队 MCP 接口就绪后完善。
    """

    name = "energy_dispatch"
    tools = [
        "parse_business_intent",
    ]
    prompt_keys = ["energy_dispatch_intent", "interpreter_generator"]
    description = "能源调度分析（负荷预测、光伏协同、储能调度、排产计划）"

    def execute(
        self,
        tool_results: List[Tuple[str, Dict[str, Any], Dict[str, Any]]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """能源调度编排逻辑。待 MCP 接入后完善，当前返回空更新。"""
        return {}
