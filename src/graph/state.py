"""state — V3 Agent 全局状态定义

所属层：graph
依赖：langgraph, langchain_core
对接 V3 引擎：N/A
"""
import operator
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from src.schemas.v3_engine import (
    AIDCCoolingStatus,
    ConstraintMatrix,
    HVACKnowledgeResult,
    IntentItem,
    PhysicsResidual,
    TimeDiTForecast,
)
from src.schemas.action_agent import PageContext, UIAction


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

    # HVAC 知识库检索结果
    hvac_knowledge: Optional[HVACKnowledgeResult]

    # HVAC Skill 上下文提示（Phase 3: 拒答/引用指令，由 HVACExpertSkill.execute() 生成）
    hvac_context_hint: Optional[dict]

    # 多意图执行计划（Phase 7: cognitive_parser 识别后填充，interpreter_generator 读取）
    intent_plan: Optional[List[IntentItem]]

    # RAG 预留
    context: Optional[str]

    # Action Agent（Phase 2）
    page_context: Optional[PageContext]
    pending_actions: Annotated[List[UIAction], operator.add]

    # 输出
    final_report: str
    error: Optional[str]
