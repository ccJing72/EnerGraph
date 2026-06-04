"""schemas — V3 引擎与 Action Agent 数据模型统一导出

所属层：schemas
依赖：pydantic
对接 V3 引擎：PhysicsAI / TimeDiT / AIDC_Cooling
"""
from src.schemas.v3_engine import (
    ConstraintMatrix,
    TimeDiTForecast,
    PhysicsResidual,
    AIDCCoolingStatus,
    HVACKnowledgeResult,
    IntentItem,
)
from src.schemas.action_agent import (
    PageContext,
    ActionAgentInput,
    UIAction,
    COPData,
    EnergySummary,
    AlarmItem,
    AlarmList,
)

__all__ = [
    "ConstraintMatrix",
    "TimeDiTForecast",
    "PhysicsResidual",
    "AIDCCoolingStatus",
    "HVACKnowledgeResult",
    "IntentItem",
    "PageContext",
    "ActionAgentInput",
    "UIAction",
    "COPData",
    "EnergySummary",
    "AlarmItem",
    "AlarmList",
]
