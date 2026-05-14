"""fetch_aidc_cooling — Mock 获取智算中心液冷状态

所属层：tools
依赖：src.schemas.v3_engine
对接 V3 引擎：AIDC_Cooling
"""
import logging
from typing import Any, Dict

from src.schemas.v3_engine import AIDCCoolingStatus

logger = logging.getLogger(__name__)


def fetch_aidc_cooling_status(datacenter_id: str) -> Dict[str, Any]:
    """模拟获取智算中心 GPU 负载队列与液冷状态。

    Args:
        datacenter_id: 数据中心 ID

    Returns:
        AIDCCoolingStatus 的 dict 表示
    """
    try:
        return AIDCCoolingStatus(
            datacenter_id=datacenter_id,
            gpu_queue_depth=42,
            liquid_cooling_temp=28.5,
            pre_cooling_policy="active",
            power_draw_kw=320.0,
        ).model_dump()
    except Exception as e:
        logger.error(f"fetch_aidc_cooling_status 失败: {e}")
        return {"error": f"fetch_aidc_cooling_status: {e}"}
