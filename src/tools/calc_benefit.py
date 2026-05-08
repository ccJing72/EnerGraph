"""收益计算工具"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def calc_benefit(
    load: List[float],
    solar: List[float],
    grid_price: List[float],
    soc: float = 0.3,
    max_power: float = 3.0,
) -> Dict[str, Any]:
    """计算调度方案与基准方案的预计成本/收益差异.

    Args:
        load: 24小时负载数据 (kWh).
        solar: 24小时光伏数据 (kWh).
        grid_price: 24小时电价数据 (元/kWh).
        soc: 当前储能 SOC (0-1), 用于估算可放电量.
        max_power: 最大充放电功率 (kW).

    Returns:
        收益计算结果；出错时包含 error 字段.
    """
    try:
        # ── 输入校验 ──
        for name, data in [("load", load), ("solar", solar), ("grid_price", grid_price)]:
            if len(data) != 24:
                raise ValueError(f"{name} 必须为24小时数据，当前长度: {len(data)}")

        # ── 基准方案：不使用储能，不足部分从电网购电 ──
        baseline_cost = 0.0
        for h in range(24):
            net = load[h] - solar[h]
            if net > 0:
                baseline_cost += net * grid_price[h]

        # ── 优化方案：峰谷套利策略 ──
        valley_hours = [h for h in range(24) if grid_price[h] <= sorted(grid_price)[7]]
        peak_hours = [h for h in range(24) if grid_price[h] >= sorted(grid_price, reverse=True)[5]]

        valley_price_avg = (
            sum(grid_price[h] for h in valley_hours) / len(valley_hours)
            if valley_hours else 0
        )
        peak_price_avg = (
            sum(grid_price[h] for h in peak_hours) / len(peak_hours)
            if peak_hours else 0
        )

        # 可用储能容量
        usable_capacity = soc * max_power * 2

        valley_charge_cost = valley_price_avg * usable_capacity
        peak_discharge_benefit = peak_price_avg * usable_capacity

        optimized_cost = baseline_cost - (peak_discharge_benefit - valley_charge_cost)
        savings = baseline_cost - optimized_cost
        savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0.0

        return {
            "baseline_cost": round(baseline_cost, 2),
            "optimized_cost": round(max(optimized_cost, 0), 2),
            "savings": round(max(savings, 0), 2),
            "savings_pct": round(savings_pct, 1),
        }

    except Exception as e:
        logger.error(f"calc_benefit 执行失败: {e}")
        return {"error": f"calc_benefit: {e}"}
