"""统计指标工具"""
from typing import Dict, List


def compute_metrics(load: List[float], solar: List[float], grid_price: List[float]) -> Dict:
    """
    分时段统计购电、售电、储能充放电、光伏消纳等核心指标

    Args:
        load: 24小时负载数据
        solar: 24小时光伏数据
        grid_price: 24小时电价数据

    Returns:
        统计结果字典
    """
    total_load = sum(load)
    total_solar = sum(solar)
    solar_utilization = (total_solar / total_load * 100) if total_load > 0 else 0

    # 简化的峰谷时段划分
    valley_hours = list(range(0, 6)) + list(range(22, 24))  # 0-6, 22-24
    peak_hours = list(range(17, 22))  # 17-22

    valley_load = sum(load[h] for h in valley_hours)
    peak_load = sum(load[h] for h in peak_hours)

    return {
        "total_load_kwh": round(total_load, 2),
        "total_solar_kwh": round(total_solar, 2),
        "solar_utilization_pct": round(solar_utilization, 1),
        "valley_load_kwh": round(valley_load, 2),
        "peak_load_kwh": round(peak_load, 2),
        "avg_price": round(sum(grid_price) / len(grid_price), 2)
    }
