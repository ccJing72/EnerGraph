"""统计指标工具"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def compute_metrics(
    load: List[float],
    solar: List[float],
    grid_price: List[float],
) -> Dict[str, Any]:
    """分时段统计购电、储能充放电、光伏消纳等核心指标.

    Args:
        load: 24小时负载数据 (kWh).
        solar: 24小时光伏数据 (kWh).
        grid_price: 24小时电价数据 (元/kWh).

    Returns:
        包含统计指标和逐段分析的字典；出错时包含 error 字段.
    """
    try:
        # ── 输入校验 ──
        for name, data in [("load", load), ("solar", solar), ("grid_price", grid_price)]:
            if len(data) != 24:
                raise ValueError(f"{name} 必须为24小时数据，当前长度: {len(data)}")
            if name in ("load", "solar") and any(x < 0 for x in data):
                raise ValueError(f"{name} 包含负数")

        total_load = sum(load)
        total_solar = sum(solar)
        solar_utilization = (
            (total_solar / total_load * 100) if total_load > 0 else 0.0
        )

        avg_price = sum(grid_price) / len(grid_price)

        # 时段划分
        valley_hours = list(range(0, 6)) + list(range(22, 24))
        peak_hours = list(range(17, 22))
        flat_hours = [h for h in range(24) if h not in valley_hours and h not in peak_hours]

        valley_load = sum(load[h] for h in valley_hours)
        peak_load = sum(load[h] for h in peak_hours)

        # ── 逐段充放电分析 ──
        period_analysis = _build_period_analysis(load, solar, grid_price)

        return {
            "total_load_kwh": round(total_load, 2),
            "total_solar_kwh": round(total_solar, 2),
            "solar_utilization_pct": round(solar_utilization, 1),
            "valley_load_kwh": round(valley_load, 2),
            "peak_load_kwh": round(peak_load, 2),
            "avg_price": round(avg_price, 2),
            "period_analysis": period_analysis,
        }

    except Exception as e:
        logger.error(f"compute_metrics 执行失败: {e}")
        return {"error": f"compute_metrics: {e}"}


def _build_period_analysis(
    load: List[float],
    solar: List[float],
    grid_price: List[float],
) -> List[Dict[str, Any]]:
    """构建逐时段的充放电分析明细."""
    periods = [
        {"name": "谷段充电期", "hours": list(range(0, 6)), "icon": "moon", "type": "valley"},
        {"name": "光伏优先期", "hours": list(range(6, 17)), "icon": "sun", "type": "solar"},
        {"name": "峰段放电期", "hours": list(range(17, 21)), "icon": "sunset", "type": "peak"},
        {"name": "补充调整期", "hours": list(range(21, 24)), "icon": "moon", "type": "valley"},
    ]

    result = []
    for p in periods:
        hours = p["hours"]
        p_load = sum(load[h] for h in hours)
        p_solar = sum(solar[h] for h in hours)
        p_price = sum(grid_price[h] for h in hours) / len(hours) if hours else 0

        # 简化充放电估算 (后续可接入真实算法)
        if p["type"] == "valley":
            charge_kwh = round(min(p_load * 0.8, 3.2), 1)
            discharge_kwh = 0.0
        elif p["type"] == "solar":
            surplus = max(0, p_solar - p_load)
            charge_kwh = round(min(surplus, 5.8), 1)
            discharge_kwh = 0.0
        else:  # peak
            charge_kwh = 0.0
            discharge_kwh = round(min(p_load * 0.9, 4.5), 1)

        result.append({
            "name": p["name"],
            "icon": p["icon"],
            "hours": f"{hours[0]:02d}:00–{hours[-1]+1:02d}:00",
            "load_kwh": round(p_load, 2),
            "solar_kwh": round(p_solar, 2),
            "avg_price": round(p_price, 2),
            "charge_kwh": charge_kwh,
            "discharge_kwh": discharge_kwh,
        })

    return result
