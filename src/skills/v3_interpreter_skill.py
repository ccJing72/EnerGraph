"""v3_interpreter_skill — V3 引擎数据解读技能

所属层：skills
依赖：无（纯 LLM 推理，不调用 Tools）
对接 V3 引擎：N/A（接收其他 Skill 的工具结果，生成报告）

SOP：
  1. 接收任意 Skill 传入的工具结果（ConstraintMatrix / TimeDiTForecast /
     PhysicsResidual / AIDCCoolingStatus / HVACKnowledgeResult）
  2. 按数据类型选择报告模板
  3. 生成包含三个维度的 Markdown 报告：
     - 能耗收益分析
     - 碳排下降说明
     - 设备安全边界证明

此 Skill 是 interpreter_generator_node 的业务逻辑抽象，
将 context 拼装逻辑从节点代码移入此处，节点只负责调用。

Prompt keys（src/config/prompts.yaml）：
  - interpreter_generator : 报告生成指令（已有）
"""
from typing import Any, Dict, List, Tuple

from src.skills.base_skill import BaseSkill


class V3InterpreterSkill(BaseSkill):
    """V3 引擎数据解读与报告生成技能。

    当前为骨架占位，随 Phase 2-4 推进逐步将
    interpreter_generator_node 中的 context 拼装逻辑迁移至此。
    """

    name = "v3_interpreter"
    tools = []  # 纯 LLM 推理，不调用 Tools
    prompt_keys = ["interpreter_generator"]
    description = "V3 引擎数据解读（将物理残差/SOC 曲线转化为 Markdown 报告）"

    def execute(
        self,
        tool_results: List[Tuple[str, Dict[str, Any], Dict[str, Any]]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """报告生成编排逻辑。当前返回空更新，等后续迁移 interpreter 逻辑。"""
        return {}
