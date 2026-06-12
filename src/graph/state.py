"""state — Agent 全局状态定义

所属层：graph
依赖：langgraph, langchain_core
对接算法层：N/A
"""
import operator
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.schemas.v3_engine import (
    ConstraintMatrix,
    HVACKnowledgeResult,
    IntentItem,
    PhysicsResidual,
)
from src.schemas.action_agent import PageContext, UIAction


class AgentState(TypedDict, total=False):
    """决策层 Agent 全局状态

    messages 使用 add_messages reducer 追加，其余字段直接覆盖。
    """
    # 输入
    user_input: str
    messages: Annotated[List[BaseMessage], add_messages]

    # 意图解析
    constraints: Optional[ConstraintMatrix]

    # 算法模型调用结果（待 MCP 接入后使用）
    physics_verification: Optional[PhysicsResidual]

    # HVAC 知识库检索结果
    hvac_knowledge: Optional[HVACKnowledgeResult]

    # HVAC Skill 上下文提示（Phase 3: 拒答/引用指令）
    hvac_context_hint: Optional[dict]

    # 多意图执行计划（Phase 7）
    intent_plan: Optional[List[IntentItem]]

    # RAG 预留
    context: Optional[str]

    # Action Agent（Phase 2）
    page_context: Optional[PageContext]
    pending_actions: Annotated[List[UIAction], operator.add]

    # 输出
    final_report: str
    error: Optional[str]
