"""state — V3 Agent 全局状态定义

所属层：graph
依赖：langgraph, langchain_core
对接 V3 引擎：N/A
"""
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.schemas.v3_engine import (
    AIDCCoolingStatus,
    ConstraintMatrix,
    PhysicsResidual,
    TimeDiTForecast,
)


class AgentState(TypedDict, total=False):
    """V3 多模态调度 Agent 全局状态

    messages 使用 add_messages reducer 追加，其余字段直接覆盖。
    """
    # 输入
    user_input: str
    messages: Annotated[List[BaseMessage], add_messages]

    # 意图解析
    constraints: Optional[ConstraintMatrix]

    # 引擎调用结果
    timedit_data: Optional[TimeDiTForecast]
    physics_verification: Optional[PhysicsResidual]
    aidc_cooling: Optional[AIDCCoolingStatus]

    # RAG 预留
    context: Optional[str]

    # 输出
    final_report: str
    error: Optional[str]
