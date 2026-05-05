"""收益计算工具"""
from typing import Dict, List


def calc_benefit(load: List[float], solar: List[float], grid_price: List[float],
                 soc: float, max_power: float) -> Dict:
    """
    基于调度数据计算预计成本/收益，对比基准方案

    Args:
        load: 24小时负载数据
        solar: 24小时光伏数据
        grid_price: 24小时电价数据
        soc: 当前储能SOC
        max_power: 最大充放电功率

    Returns:
        收益计算结果
    """
    # 基准方案：不使用储能，直接从电网购电
    baseline_cost = sum((load[h] - solar[h]) * grid_price[h] if load[h] > solar[h] else 0
                        for h in range(24))

    # 优化方案：简化的峰谷套利策略
    valley_hours = list(range(0, 6)) + list(range(22, 24))
    peak_hours = list(range(17, 22))

    # 谷段充电成本
    valley_charge = sum(grid_price[h] for h in valley_hours) / len(valley_hours) * max_power * 2
    # 峰段放电收益
    peak_discharge = sum(grid_price[h] for h in peak_hours) / len(peak_hours) * max_power * 2

    optimized_cost = baseline_cost - (peak_discharge - valley_charge)

    savings = baseline_cost - optimized_cost
    savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

    return {
        "baseline_cost": round(baseline_cost, 2),
        "optimized_cost": round(optimized_cost, 2),
        "savings": round(savings, 2),
        "savings_pct": round(savings_pct, 1)
    }
