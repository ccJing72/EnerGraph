"""工具输出模型 (Pydantic)"""
from typing import List, Optional
from pydantic import BaseModel, Field


class MetricsResult(BaseModel):
    """compute_metrics 输出"""
    total_load_kwh: float = Field(..., description="总负载 (kWh)")
    total_solar_kwh: float = Field(..., description="总光伏发电 (kWh)")
    solar_utilization_pct: float = Field(..., description="光伏利用率 (%)")
    valley_load_kwh: float = Field(..., description="谷段负载 (kWh)")
    peak_load_kwh: float = Field(..., description="峰段负载 (kWh)")
    avg_price: float = Field(..., description="平均电价 (元/kWh)")
    # 逐段充放电分析
    period_analysis: Optional[List[dict]] = Field(
        default=None, description="逐时段充放电明细"
    )


class PriceCompareResult(BaseModel):
    """compare_price 输出"""
    min_price: float = Field(..., description="最低电价")
    max_price: float = Field(..., description="最高电价")
    min_price_hour: int = Field(..., description="最低电价时段")
    max_price_hour: int = Field(..., description="最高电价时段")
    price_diff: float = Field(..., description="峰谷价差")
    arbitrage_potential_pct: float = Field(..., description="套利潜力 (%)")


class BenefitResult(BaseModel):
    """calc_benefit 输出"""
    baseline_cost: float = Field(..., description="基准方案成本 (元)")
    optimized_cost: float = Field(..., description="优化方案成本 (元)")
    savings: float = Field(..., description="节省金额 (元)")
    savings_pct: float = Field(..., description="节省比例 (%)")


class ToolError(BaseModel):
    """工具错误返回"""
    tool_name: str = Field(..., description="工具名称")
    error_type: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
