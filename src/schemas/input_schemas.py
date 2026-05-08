"""输入数据模型 (Pydantic)"""
from typing import List
from pydantic import BaseModel, Field, field_validator


class ForecastData(BaseModel):
    """预测与价格数据"""
    load: List[float] = Field(..., description="24h 负载预测 (kWh)")
    solar: List[float] = Field(..., description="24h 光伏预测 (kWh)")
    grid_price: List[float] = Field(..., description="24h 电价 (元/kWh)")

    @field_validator("load", "solar", "grid_price")
    @classmethod
    def check_length_24(cls, v: List[float]) -> List[float]:
        if len(v) != 24:
            raise ValueError(f"必须为24小时数据，当前长度: {len(v)}")
        return v

    @field_validator("load", "solar")
    @classmethod
    def check_non_negative(cls, v: List[float]) -> List[float]:
        if any(x < 0 for x in v):
            raise ValueError("数值不能为负数")
        return v


class SystemState(BaseModel):
    """储能系统状态"""
    soc: float = Field(..., ge=0, le=1, description="当前 SOC")
    soc_max: float = Field(default=0.9, ge=0, le=1, description="最大 SOC")
    soc_min: float = Field(default=0.2, ge=0, le=1, description="最小 SOC")
    max_power: float = Field(..., gt=0, description="最大充放电功率 (kW)")
    user_pref: str = Field(default="cost_priority", description="用户偏好")


class BasicInfo(BaseModel):
    """基础信息"""
    timezone: str = Field(default="UTC+8", description="时区")
    currency: str = Field(default="CNY", description="货币单位")
    query: str = Field(default="今天的调度策略是什么？", description="用户查询")


class AgentInput(BaseModel):
    """Agent 完整输入"""
    forecast_data: ForecastData
    system_state: SystemState
    basic_info: BasicInfo
