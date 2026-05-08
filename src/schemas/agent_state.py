"""Agent 状态定义 (LangGraph TypedDict)"""
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """ReAct Agent 全局状态

    所有字段均为 Optional，由各节点按需填充。
    使用 total=False 避免 LangGraph 在 partial update 时报 KeyError。
    """

    # ── 输入数据 ──
    load: List[float]
    solar: List[float]
    grid_price: List[float]
    soc: float
    max_power: float
    user_pref: str
    query: str

    # ── 工具返回 ──
    metrics: Dict[str, Any]
    price_analysis: Dict[str, Any]
    benefit: Dict[str, Any]

    # ── LLM 消息 ──
    messages: List[Dict[str, Any]]

    # ── 控制流 ──
    next_action: str                # "call_tool" | "report" | "end"
    tool_to_call: str               # 当前要调用的工具名称
    iteration: int

    # ── 输出 ──
    report: str
    error: Optional[str]

    # ── 扩展预留 ──
    context: Optional[str]          # RAG 检索结果
    history: Optional[List[Dict]]   # 多轮对话历史
