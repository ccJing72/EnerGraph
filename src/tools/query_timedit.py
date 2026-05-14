"""query_timedit — Mock 调用 QingShan-TimeDiT 时序扩散模型

所属层：tools
依赖：src.schemas.v3_engine
对接 V3 引擎：QingShan-TimeDiT
"""
import logging
import math
from typing import Any, Dict

from src.schemas.v3_engine import TimeDiTForecast

logger = logging.getLogger(__name__)


def query_timedit_forecast(target_date: str) -> Dict[str, Any]:
    """模拟调用 TimeDiT，返回未来 24 小时光伏与负荷概率分布预测。

    Args:
        target_date: 目标日期，格式 YYYY-MM-DD

    Returns:
        TimeDiTForecast 的 dict 表示
    """
    try:
        # Mock：正弦曲线模拟日负荷，余弦模拟光伏
        load = [round(30 + 15 * math.sin(math.pi * h / 12), 2) for h in range(24)]
        solar = [round(max(0, 20 * math.sin(math.pi * (h - 6) / 12)), 2) for h in range(24)]
        confidence = [round(0.85 + 0.05 * math.sin(math.pi * h / 24), 3) for h in range(24)]

        return TimeDiTForecast(
            target_date=target_date,
            load_forecast=load,
            solar_forecast=solar,
            confidence_interval=confidence,
        ).model_dump()
    except Exception as e:
        logger.error(f"query_timedit_forecast 失败: {e}")
        return {"error": f"query_timedit_forecast: {e}"}
