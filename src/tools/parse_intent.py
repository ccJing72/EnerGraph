"""parse_intent — 业务意图解析工具，将自然语言转化为 ConstraintMatrix

所属层：tools
依赖：langchain_core, src.schemas.v3_engine
对接 V3 引擎：N/A（纯 LLM 调用）
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

import yaml
from langchain_core.messages import HumanMessage, SystemMessage

from src.schemas.v3_engine import ConstraintMatrix

logger = logging.getLogger(__name__)

_PROMPTS_PATH = Path(__file__).resolve().parents[2] / "src" / "config" / "prompts.yaml"


def _get_system_prompt() -> str:
    """从 prompts.yaml 加载 parse_intent system prompt。"""
    if _PROMPTS_PATH.exists():
        with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
            prompts = yaml.safe_load(f) or {}
        return prompts.get("parse_intent", {}).get("system", "")
    return ""


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
            SystemMessage(content=_get_system_prompt()),
            HumanMessage(content=user_input),
        ])
        data = json.loads(response.content)
        return ConstraintMatrix(**data).model_dump()
    except Exception as e:
        logger.error(f"parse_business_intent 失败: {e}")
        return {"error": f"parse_business_intent: {e}"}
