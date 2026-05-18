"""工具注册表 — V3 引擎 Mock Tools + HVAC 知识库

所属层：tools
依赖：src.tools.*
对接 V3 引擎：PhysicsAI / TimeDiT / AIDC_Cooling / HVAC RAG
"""
from typing import Any, Callable, Dict

from src.tools.parse_intent import parse_business_intent
from src.tools.query_timedit import query_timedit_forecast
from src.tools.verify_physics import verify_physics_consistency
from src.tools.fetch_aidc_cooling import fetch_aidc_cooling_status
from src.tools.query_hvac_knowledge import query_hvac_knowledge

TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "parse_business_intent": parse_business_intent,
    "query_timedit_forecast": query_timedit_forecast,
    "verify_physics_consistency": verify_physics_consistency,
    "fetch_aidc_cooling_status": fetch_aidc_cooling_status,
    "query_hvac_knowledge": query_hvac_knowledge,
}

TOOL_SCHEMAS = [
    {
        "name": "parse_business_intent",
        "description": "将自然语言或 ERP/MES 输入解析为 V3 DFL 可读的约束矩阵（ConstraintMatrix）",
        "parameters": {
            "type": "object",
            "properties": {
                "user_input": {"type": "string", "description": "用户自然语言输入"},
            },
            "required": ["user_input"],
        },
    },
    {
        "name": "query_timedit_forecast",
        "description": "调用 QingShan-TimeDiT 时序扩散模型，获取未来 24 小时光伏与负荷概率分布预测",
        "parameters": {
            "type": "object",
            "properties": {
                "target_date": {"type": "string", "description": "目标日期，格式 YYYY-MM-DD"},
            },
            "required": ["target_date"],
        },
    },
    {
        "name": "verify_physics_consistency",
        "description": "调用 PhysicsAI 验证调度策略是否符合热力学热平衡与 SOC 衰减模型",
        "parameters": {
            "type": "object",
            "properties": {
                "strategy_id": {"type": "string", "description": "调度策略 ID"},
            },
            "required": ["strategy_id"],
        },
    },
    {
        "name": "fetch_aidc_cooling_status",
        "description": "获取智算中心 GPU 负载队列与液冷状态，支持算力-冷却-储能协同调度解释",
        "parameters": {
            "type": "object",
            "properties": {
                "datacenter_id": {"type": "string", "description": "数据中心 ID"},
            },
            "required": ["datacenter_id"],
        },
    },
    {
        "name": "query_hvac_knowledge",
        "description": "从暖通空调（HVAC）专业知识库检索相关问答，用于回答暖通规范、能效计算、故障诊断、节能优化等专业问题",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "用户的暖通空调相关问题"},
            },
            "required": ["question"],
        },
    },
]
