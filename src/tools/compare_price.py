"""电价对比工具"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def compare_price(grid_price: List[float]) -> Dict[str, Any]:
    """对比不同时段的购电价格，识别峰谷套利机会.

    Args:
        grid_price: 24小时电价数据 (元/kWh).

    Returns:
        价格对比结果；出错时包含 error 字段.
    """
    try:
        if len(grid_price) != 24:
            raise ValueError(f"grid_price 必须为24小时数据，当前长度: {len(grid_price)}")

        min_price = min(grid_price)
        max_price = max(grid_price)

        # 使用列表推导找出所有最低/最高时段（避免 .index() 仅返回第一个的误导）
        min_hours = [h for h, p in enumerate(grid_price) if p == min_price]
        max_hours = [h for h, p in enumerate(grid_price) if p == max_price]

        price_diff = max_price - min_price
        arbitrage_potential = (
            (price_diff / min_price * 100) if min_price > 0 else 0.0
        )

        return {
            "min_price": round(min_price, 2),
            "max_price": round(max_price, 2),
            "min_price_hours": min_hours,
            "max_price_hours": max_hours,
            "price_diff": round(price_diff, 2),
            "arbitrage_potential_pct": round(arbitrage_potential, 1),
        }

    except Exception as e:
        logger.error(f"compare_price 执行失败: {e}")
        return {"error": f"compare_price: {e}"}
