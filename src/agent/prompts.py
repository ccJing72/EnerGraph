"""ReAct Agent Prompt 模板"""
import json
from typing import Any, Dict, List, Optional

from src.tools import TOOL_SCHEMAS

SYSTEM_PROMPT = """你是家庭能源AI调度解释Agent，基于给定数据与工具，通过ReAct循环完成策略解读。

【任务目标】
为用户生成清晰、易懂、数据可溯源的能源调度策略报告，解释系统每一步调度行为的原因与收益。

【可用工具】
{}

【工作流程】
1. Thought：理解用户需求与调度原则，分析输入数据，规划下一步工具调用
2. Action：调用工具获取量化结果
3. Observation：基于工具返回数据，完成归因分析
4. 循环上述步骤，直至所有关键分析完成
5. Final Answer：整合所有结果，生成结构化报告

【输出要求】
- 报告分为：今日调度安排、总体概述、收益对比、总结建议
- 所有分析必须基于工具返回数据，禁止主观臆断
- 语言通俗易懂，突出用户收益
- 格式为Markdown
"""


def build_system_prompt() -> str:
    """构建包含工具列表的 System Prompt."""
    tools_desc = json.dumps(TOOL_SCHEMAS, ensure_ascii=False, indent=2)
    return SYSTEM_PROMPT.format(tools_desc)


def build_user_prompt(
    load: List[float],
    solar: List[float],
    grid_price: List[float],
    soc: float,
    max_power: float,
    user_pref: str,
    query: str,
    tool_results: Optional[Dict[str, Any]] = None,
) -> str:
    """构建 User Prompt.

    Args:
        load: 24小时负载.
        solar: 24小时光伏.
        grid_price: 24小时电价.
        soc: 当前SOC.
        max_power: 最大功率.
        user_pref: 用户偏好.
        query: 用户查询.
        tool_results: 已获取的工具结果（在 Observation 循环中传入）.
    """
    data_block = json.dumps({
        "load": load,
        "solar": solar,
        "grid_price": grid_price,
        "soc": soc,
        "max_power": max_power,
        "user_pref": user_pref,
    }, ensure_ascii=False, indent=2)

    prompt = f"""【输入数据】
{data_block}

【用户查询】
{query}
"""

    if tool_results:
        prompt += f"""

【工具调用结果】
{json.dumps(tool_results, ensure_ascii=False, indent=2)}

请基于以上工具返回的数据，生成最终的结构化调度策略报告。
"""

    else:
        prompt += """

请分析数据，决定需要调用哪些工具来获取所需信息，然后生成报告。
"""

    return prompt
