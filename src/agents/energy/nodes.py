"""ReAct 节点实现 — Thought / Action / Observation"""
import json
import logging
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from src.agents.energy.prompts import build_system_prompt, build_user_prompt
from src.config.settings import settings
from src.schemas.agent_state import AgentState
from src.tools import TOOL_REGISTRY, TOOL_SCHEMAS

logger = logging.getLogger(__name__)


def _get_llm():
    """根据配置返回 LLM 实例，绑定工具 schema."""
    provider = settings.model.provider.lower()
    model_name = settings.model.name
    temperature = settings.model.temperature

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model_name, temperature=temperature)
    else:
        # 默认 openai 兼容（支持 DeepSeek 等 OpenAI 兼容接口）
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model_name, temperature=temperature)

    return llm.bind_tools(TOOL_SCHEMAS)


def agent_node(state: AgentState) -> Dict[str, Any]:
    """Thought 节点：LLM 分析数据，决定调用哪个工具或输出最终答案."""
    messages = state.get("messages", [])

    # 首次进入：构建初始消息
    if not messages:
        system_msg = SystemMessage(content=build_system_prompt())
        user_msg = HumanMessage(
            content=build_user_prompt(
                load=state["load"],
                solar=state["solar"],
                grid_price=state["grid_price"],
                soc=state["soc"],
                max_power=state["max_power"],
                user_pref=state["user_pref"],
                query=state["query"],
            )
        )
        messages = [system_msg, user_msg]

    try:
        llm = _get_llm()
        response: AIMessage = llm.invoke(messages)
        messages = messages + [response]

        return {
            "messages": messages,
            "iteration": state.get("iteration", 0) + 1,
        }
    except Exception as e:
        logger.error(f"agent_node 调用 LLM 失败: {e}")
        return {
            "messages": messages,
            "error": str(e),
            "next_action": "report",
        }


def tool_node(state: AgentState) -> Dict[str, Any]:
    """Action 节点：执行 LLM 选择的工具，返回 Observation."""
    messages = state.get("messages", [])
    last_message: AIMessage = messages[-1]

    tool_messages = []
    tool_results: Dict[str, Any] = {}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name not in TOOL_REGISTRY:
            result = {"error": f"工具 '{tool_name}' 不存在"}
        else:
            try:
                # 注入 state 中的数据（工具可能只传部分参数）
                full_args = _inject_state_data(tool_name, tool_args, state)
                result = TOOL_REGISTRY[tool_name](**full_args)
            except Exception as e:
                logger.error(f"工具 {tool_name} 执行失败: {e}")
                result = {"error": str(e)}

        tool_results[tool_name] = result
        tool_messages.append(
            ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                tool_call_id=tool_call["id"],
            )
        )

    # 合并已有工具结果
    existing = {
        "metrics": state.get("metrics", {}),
        "price_analysis": state.get("price_analysis", {}),
        "benefit": state.get("benefit", {}),
    }
    if "compute_metrics" in tool_results:
        existing["metrics"] = tool_results["compute_metrics"]
    if "compare_price" in tool_results:
        existing["price_analysis"] = tool_results["compare_price"]
    if "calc_benefit" in tool_results:
        existing["benefit"] = tool_results["calc_benefit"]

    return {
        "messages": messages + tool_messages,
        **existing,
    }


def report_node(state: AgentState) -> Dict[str, Any]:
    """Final Answer 节点：整合所有工具结果，生成最终报告."""
    from src.utils.report_builder import build_report

    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None

    # 优先使用 LLM 直接输出的文本（无工具调用时）
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        report = last_message.content
    else:
        # 回退：用 report_builder 基于工具结果生成报告
        report = build_report(
            metrics=state.get("metrics", {}),
            price_analysis=state.get("price_analysis", {}),
            benefit=state.get("benefit", {}),
            user_pref=state.get("user_pref", "cost_priority"),
        )

    return {"report": report}


def should_continue(state: AgentState) -> str:
    """条件路由：判断下一步是继续调用工具还是生成报告."""
    messages = state.get("messages", [])
    if not messages:
        return "report"

    last_message = messages[-1]
    iteration = state.get("iteration", 0)
    max_iter = settings.agent.max_iterations

    # 超出最大迭代次数 → 强制生成报告
    if iteration >= max_iter:
        logger.warning(f"达到最大迭代次数 {max_iter}，强制生成报告")
        return "report"

    # 有错误 → 生成报告
    if state.get("error"):
        return "report"

    # LLM 请求调用工具 → 继续
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    # 无工具调用 → 生成报告
    return "report"


def _inject_state_data(
    tool_name: str, tool_args: Dict[str, Any], state: AgentState
) -> Dict[str, Any]:
    """将 state 中的数据注入工具参数（LLM 可能只传部分参数）."""
    defaults = {
        "load": state.get("load", []),
        "solar": state.get("solar", []),
        "grid_price": state.get("grid_price", []),
        "soc": state.get("soc", 0.3),
        "max_power": state.get("max_power", 3.0),
    }
    # tool_args 优先，state 数据作为缺省值
    return {**defaults, **tool_args}
