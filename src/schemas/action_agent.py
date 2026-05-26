"""action_agent — Action Agent 数据模型

所属层：schemas
依赖：pydantic
对接 V3 引擎：N/A
"""
from typing import Optional
from pydantic import BaseModel, Field


class PageContext(BaseModel):
    """前端页面上下文，由前端在每次请求时注入。

    字段会随前端页面分析逐步扩展。params 承载页面级运行时数据
    （如筛选条件、选中的设备 ID），新增字段直接追加，无需破坏现有结构。
    """
    current_route: str = Field(default="/", description="当前页面路由")
    site_id: Optional[str] = Field(default=None, description="当前选中的站点 ID")
    params: dict = Field(default_factory=dict, description="页面级运行时参数（筛选条件、选中设备等）")
    meta: dict = Field(default_factory=dict, description="扩展元数据，后续前端分析追加字段用此入口")


class ActionAgentInput(BaseModel):
    """POST /stream 请求体。"""
    user_input: str = Field(..., description="用户输入文本")
    page_context: Optional[PageContext] = Field(default=None, description="前端页面上下文")


class UIAction(BaseModel):
    """前端可消费的 UI 动作信号。

    当前支持页面跳转；后续前端页面分析后，可扩展子页面跳转、
    面包屑导航、高亮组件、打开面板等动作。新增字段直接追加，
    params 承载路由参数，meta 承载 UI 层元数据。
    """
    type: str = Field(default="navigate", description="动作类型：navigate / highlight / open_panel（后续前端分析追加）")
    route: str = Field(..., description="目标路由，子页面用 /parent/child 形式")
    params: dict = Field(default_factory=dict, description="路由参数（如 site_id, chiller_id）")
    meta: dict = Field(default_factory=dict, description="UI 元数据（面包屑、查询参数、高亮目标等，后续前端分析追加）")


# ── Java 后端工具输出模型（Phase 2 T3）──────────────────────────────

class COPData(BaseModel):
    """冷水机组 COP（能效比）数据。"""
    site_id: str = Field(..., description="站点 ID")
    chiller_id: str = Field(..., description="冷水机组编号")
    instant_cop: float = Field(..., description="瞬时 COP")
    cumulative_cop: float = Field(..., description="累计 COP")
    chilled_water_out_temp: float = Field(..., description="冷冻水出水温度 (℃)")
    cooling_water_in_temp: float = Field(..., description="冷却水进水温度 (℃)")
    power_kw: float = Field(..., description="实时功率 (kW)")
    timestamp: str = Field(..., description="数据时间戳 (ISO 8601)")
    status: str = Field(default="normal", description="运行状态")


class EnergySummary(BaseModel):
    """站点能耗汇总数据。"""
    site_id: str = Field(..., description="站点 ID")
    date: str = Field(..., description="统计日期 (YYYY-MM-DD)")
    total_consumption_kwh: float = Field(..., description="总用电量 (kWh)")
    pv_generation_kwh: float = Field(default=0.0, description="光伏发电量 (kWh)")
    grid_import_kwh: float = Field(..., description="电网取电量 (kWh)")
    storage_charge_kwh: float = Field(default=0.0, description="储能充电量 (kWh)")
    storage_discharge_kwh: float = Field(default=0.0, description="储能放电量 (kWh)")
    peak_load_kw: float = Field(..., description="峰值负荷 (kW)")
    avg_load_kw: float = Field(..., description="平均负荷 (kW)")
    carbon_reduction_kg: float = Field(default=0.0, description="碳减排量 (kgCO₂)")


class AlarmItem(BaseModel):
    """单条报警记录。"""
    alarm_id: str = Field(..., description="报警 ID")
    level: str = Field(..., description="报警级别：critical / warning / info")
    device: str = Field(..., description="报警设备名称")
    message: str = Field(..., description="报警信息")
    timestamp: str = Field(..., description="报警时间 (ISO 8601)")
    acknowledged: bool = Field(default=False, description="是否已确认")


class AlarmList(BaseModel):
    """站点活跃报警列表。"""
    site_id: str = Field(..., description="站点 ID")
    total_count: int = Field(..., description="活跃报警总数")
    alarms: list[AlarmItem] = Field(default_factory=list, description="报警列表")
