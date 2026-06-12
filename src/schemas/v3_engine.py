"""v3_engine — 数据模型定义

所属层：schemas
依赖：pydantic
对接算法层：N/A（数据结构定义）
"""
from typing import List
from pydantic import BaseModel, Field


class IntentItem(BaseModel):
    """单条用户意图（Phase 7: 多意图识别）"""
    id: int = Field(..., description="意图序号（从 1 开始）")
    description: str = Field(..., description="意图描述")
    category: str = Field(default="general", description="意图类别：hvac / monitor / energy / alarm / export / general")
    depends_on: List[int] = Field(default_factory=list, description="依赖的意图 ID 列表")
    status: str = Field(default="pending", description="执行状态：pending / running / done / failed")


class ConstraintMatrix(BaseModel):
    """业务意图解析结果 — 底层 DFL 算法可读的约束边界"""
    load_baseline: str = "+0%"
    sla_priority: str = "Normal"
    time_window: str = ""
    optimization_goal: str = "cost"
    extra_constraints: dict = {}


class PhysicsResidual(BaseModel):
    """设备诊断验证结果（保留字段待算法团队明确 MCP 接口后重构）"""
    strategy_id: str
    is_physically_valid: bool
    langevin_residual: float
    soc_decay_deviation: float
    heat_balance_error: float
    safety_warnings: List[str] = []
class HVACKnowledgeResult(BaseModel):
    """HVAC 知识库 RAG 检索结果"""
    query: str
    results: List[str]          # Top-K 相关 Q&A 文本
    system_types: List[str]     # 对应的场景类型（metro/commercial/standard/general）
    distances: List[float]      # 相似度距离（越小越相关）
    low_confidence: bool = False  # top-1 distance > 阈值时为 True，触发拒答
    source_snippets: List[str] = []  # 检索片段摘要（≤50字），供引用来源标注

