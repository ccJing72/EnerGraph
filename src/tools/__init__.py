"""工具注册表"""
from typing import Any, Callable, Dict

from src.tools.compute_metrics import compute_metrics
from src.tools.compare_price import compare_price
from src.tools.calc_benefit import calc_benefit

# ── 工具注册表 ──
# 新增工具只需在此注册，Agent 自动可用
TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "compute_metrics": compute_metrics,
    "compare_price": compare_price,
    "calc_benefit": calc_benefit,
}

# 工具元信息（供 LLM function calling 使用）
TOOL_SCHEMAS = [
    {
        "name": "compute_metrics",
        "description": "分时段统计购电、储能充放电、光伏消纳等核心指标，返回总量和逐段分析",
        "parameters": {
            "type": "object",
            "properties": {
                "load": {"type": "array", "items": {"type": "number"}, "description": "24小时负载(kWh)"},
                "solar": {"type": "array", "items": {"type": "number"}, "description": "24小时光伏(kWh)"},
                "grid_price": {"type": "array", "items": {"type": "number"}, "description": "24小时电价(元/kWh)"},
            },
            "required": ["load", "solar", "grid_price"],
        },
    },
    {
        "name": "compare_price",
        "description": "对比不同时段购电价格，识别峰谷套利机会",
        "parameters": {
            "type": "object",
            "properties": {
                "grid_price": {"type": "array", "items": {"type": "number"}, "description": "24小时电价(元/kWh)"},
            },
            "required": ["grid_price"],
        },
    },
    {
        "name": "calc_benefit",
        "description": "计算调度方案与基准方案的成本/收益差异",
        "parameters": {
            "type": "object",
            "properties": {
                "load": {"type": "array", "items": {"type": "number"}, "description": "24小时负载(kWh)"},
                "solar": {"type": "array", "items": {"type": "number"}, "description": "24小时光伏(kWh)"},
                "grid_price": {"type": "array", "items": {"type": "number"}, "description": "24小时电价(元/kWh)"},
                "soc": {"type": "number", "description": "当前储能SOC"},
                "max_power": {"type": "number", "description": "最大充放电功率(kW)"},
            },
            "required": ["load", "solar", "grid_price"],
        },
    },
]
