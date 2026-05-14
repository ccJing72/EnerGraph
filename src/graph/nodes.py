"""nodes — V3 Agent LangGraph 节点实现

所属层：graph
依赖：langchain_core, src.tools, src.config.settings
对接 V3 引擎：PhysicsAI / TimeDiT / AIDC_Cooling（通过 Tools）
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

import yaml
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.config.settings import settings
from src.graph.state import AgentState
from src.tools import TOOL_REGISTRY, TOOL_SCHEMAS

logger = logging.getLogger(__name__)

_PROMPTS_PATH = Path(__file__).resolve().parents[2] / "config" / "prompts.yaml"
_prompts: Dict[str, Any] = {}


def _load_prompts() -> Dict[str, Any]:
    global _prompts
    if not _prompts and _PROMPTS_PATH.exists():
        with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
            _prompts = yaml.safe_load(f) or {}
    return _prompts


def _get_llm(bind_tools: bool = False):
    provider = settings.model.provider.lower()
    model_name = settings.model.name
    temperature = settings.model.temperature

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model_name, temperature=temperature)
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model_name, temperature=temperature)

    return llm.bind_tools(TOOL_SCHEMAS) if bind_tools else llm


def cognitive_parser_node(state: AgentState) -> Dict[str, Any]:
    """意图解析节点：分析用户输入，决定调用哪些 V3 引擎工具。"""
    messages = state.get("messages", [])
    if not messages:
        prompts = _load_prompts()
        system_content = prompts.get("cognitive_parser", {}).get("system", "")
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=state.get("user_input", "")),
        ]

    try:
        llm = _get_llm(bind_tools=True)
        response: AIMessage = llm.invoke(messages)
        return {
            "messages": [*messages, response],
        }
    except Exception as e:
        logger.error(f"cognitive_parser_node 失败: {e}")
        return {"messages": messages, "error": str(e)}


def v3_engine_router_node(state: AgentState) -> Dict[str, Any]:
    """引擎调度节点：执行 LLM 选择的 V3 工具，收集物理数据。"""
    messages = state.get("messages", [])
    last: AIMessage = messages[-1]

    tool_messages = []
    updates: Dict[str, Any] = {}

    for tool_call in last.tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]

        if name not in TOOL_REGISTRY:
            result = {"error": f"工具 '{name}' 不存在"}
        else:
            try:
                result = TOOL_REGISTRY[name](**args)
            except Exception as e:
                logger.error(f"工具 {name} 执行失败: {e}")
                result = {"error": str(e)}

        # 将结果写入对应 state 字段
        _field_map = {
            "query_timedit_forecast": "timedit_data",
            "verify_physics_consistency": "physics_verification",
            "fetch_aidc_cooling_status": "aidc_cooling",
            "parse_business_intent": "constraints",
        }
        if name in _field_map and "error" not in result:
            updates[_field_map[name]] = result

        tool_messages.append(
            ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": tool_messages, **updates}


def interpreter_generator_node(state: AgentState) -> Dict[str, Any]:
    """报告生成节点：将物理数据转化为多维 Markdown 解释报告。"""
    messages = state.get("messages", [])
    last = messages[-1] if messages else None

    # LLM 直接输出文本（无工具调用）时直接使用
    if isinstance(last, AIMessage) and not getattr(last, "tool_calls", None):
        return {"final_report": last.content}

    # 否则用物理数据重新生成报告
    prompts = _load_prompts()
    system_content = prompts.get("interpreter_generator", {}).get("system", "")
    context = json.dumps(
        {
            "constraints": state.get("constraints"),
            "timedit_data": state.get("timedit_data"),
            "physics_verification": state.get("physics_verification"),
            "aidc_cooling": state.get("aidc_cooling"),
        },
        ensure_ascii=False,
        indent=2,
    )

    try:
        llm = _get_llm()
        response = llm.invoke([
            SystemMessage(content=system_content),
            HumanMessage(content=f"以下是 V3 引擎返回的物理数据，请生成报告：\n{context}"),
        ])
        return {"final_report": response.content}
    except Exception as e:
        logger.error(f"interpreter_generator_node 失败: {e}")
        return {"final_report": f"报告生成失败：{e}", "error": str(e)}
