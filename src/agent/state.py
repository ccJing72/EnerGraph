"""Agent 状态定义"""
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """ReAct Agent 状态"""
    # 输入数据
    load: List[float]
    solar: List[float]
    grid_price: List[float]
    soc: float
    max_power: float
    user_pref: str
    query: str

    # 工具调用结果
    metrics: Dict[str, Any]
    price_analysis: Dict[str, Any]
    benefit: Dict[str, Any]

    # Agent 控制
    next_action: Optional[str]  # 下一步动作（预留）
    iteration: int

    # 扩展字段（预留 RAG 等功能）
    context: Optional[str]  # RAG 检索的上下文
    history: Optional[List[Dict]]  # 对话历史

    # 输出
    report: str
