"""电价对比工具"""
from typing import Dict, List


def compete_price(grid_price: List[float]) -> Dict:
    """
    对比不同时段的购/售电价，识别峰谷套利机会

    Args:
        grid_price: 24小时电价数据

    Returns:
        价格对比结果
    """
    min_price = min(grid_price)
    max_price = max(grid_price)
    min_hour = grid_price.index(min_price)
    max_hour = grid_price.index(max_price)

    price_diff = max_price - min_price
    arbitrage_potential = (price_diff / min_price * 100) if min_price > 0 else 0

    return {
        "min_price": round(min_price, 2),
        "max_price": round(max_price, 2),
        "min_price_hour": min_hour,
        "max_price_hour": max_hour,
        "price_diff": round(price_diff, 2),
        "arbitrage_potential_pct": round(arbitrage_potential, 1)
    }
