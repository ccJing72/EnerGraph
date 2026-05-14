"""parse_intent — 业务意图解析工具，将自然语言转化为 ConstraintMatrix

所属层：tools
依赖：langchain_core, src.schemas.v3_engine
对接 V3 引擎：N/A（纯 LLM 调用）
"""
import json
import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from src.schemas.v3_engine import ConstraintMatrix

logger = logging.getLogger(__name__)

_SYSTEM = (
    "将用户输入解析为 JSON，字段：load_baseline(str), sla_priority(str), "
    "time_window(str), optimization_goal(str), extra_constraints(dict)。只输出 JSON。"
)


def parse_business_intent(user_input: str) -> Dict[str, Any]:
    """将自然语言或 ERP/MES 输入转化为底层 DFL 可读的约束矩阵。

    Args:
        user_input: 用户自然语言输入，如"明天有大批订单急产"

    Returns:
        ConstraintMatrix 的 dict 表示
    """
    try:
        from src.config.settings import settings

        provider = settings.model.provider.lower()
        model_name = settings.model.name

        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model=model_name, temperature=0)
        else:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=model_name, temperature=0)

        response = llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=user_input),
        ])
        data = json.loads(response.content)
        return ConstraintMatrix(**data).model_dump()
    except Exception as e:
        logger.error(f"parse_business_intent 失败: {e}")
        return {"error": f"parse_business_intent: {e}"}
