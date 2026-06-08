"""java_backend — Java 后端监控数据工具（COP / 能耗 / 报警）

所属层：tools
依赖：src.schemas.action_agent, httpx, os, yaml
对接 V3 引擎：N/A（对接福加 API 真实监控数据）

Phase 2: Mock fallback 为主，Phase 4 切换为真实 HTTP 调用。
"""
import logging
import os
import random
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.schemas.action_agent import COPData, EnergySummary, AlarmItem, AlarmList

logger = logging.getLogger(__name__)

# 福加 API 配置
FUCA_API_BASE_URL = os.getenv("FUCA_API_BASE_URL")
FUCA_API_TOKEN = os.getenv("FUCA_API_TOKEN")
FUCA_TENANT_ID = os.getenv("FUCA_TENANT_ID")

# 加载站点映射配置
_SITE_MAPPING: Optional[Dict[str, Any]] = None

def _load_site_mapping() -> Dict[str, Any]:
    """加载站点映射配置（缓存）"""
    global _SITE_MAPPING
    if _SITE_MAPPING is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "site_mapping.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            _SITE_MAPPING = yaml.safe_load(f)
    return _SITE_MAPPING

def _is_mock() -> bool:
    """判断是否使用 Mock 数据（未配置 API 地址时）"""
    return FUCA_API_BASE_URL is None


# ── COP 数据 ──────────────────────────────────────────────────────

def fetch_cop_data(site_id: str, chiller_id: str = "CH-01") -> Dict[str, Any]:
    """获取冷水机组实时 COP（能效比）数据。

    Args:
        site_id: 站点 ID（如 SH-01）
        chiller_id: 冷水机组编号，默认 CH-01

    Returns:
        COPData 的 dict 表示
    """
    try:
        if not _is_mock():
            # Phase 4: 真实 HTTP 调用
            import httpx
            resp = httpx.get(
                f"{JAVA_API_BASE_URL}/cop",
                params={"site_id": site_id, "chiller_id": chiller_id},
                timeout=10,
            )
            resp.raise_for_status()
            return COPData(**resp.json()).model_dump()

        # Mock fallback
        return COPData(
            site_id=site_id,
            chiller_id=chiller_id,
            instant_cop=round(random.uniform(5.5, 7.5), 2),
            cumulative_cop=round(random.uniform(6.0, 7.2), 2),
            chilled_water_out_temp=round(random.uniform(6.5, 8.5), 1),
            cooling_water_in_temp=round(random.uniform(28.0, 33.0), 1),
            power_kw=round(random.uniform(180, 350), 1),
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=random.choice(["normal", "normal", "normal", "warning"]),
        ).model_dump()
    except Exception as e:
        logger.error(f"fetch_cop_data 失败: {e}")
        return {"error": f"fetch_cop_data: {e}"}


# ── 能耗汇总 ──────────────────────────────────────────────────────

def fetch_energy_summary(site_id: str, date: str) -> Dict[str, Any]:
    """获取站点单日能耗汇总数据。

    Args:
        site_id: 站点 ID（如 FJJB000001）
        date: 统计日期，格式 YYYY-MM-DD

    Returns:
        EnergySummary 的 dict 表示
    """
    try:
        if not _is_mock():
            import httpx

            # 加载站点配置
            site_mapping = _load_site_mapping()
            site_config = site_mapping.get("sites", {}).get(site_id)
            if not site_config:
                return {"error": f"未找到站点 {site_id} 的配置"}

            # 构造请求体
            payload = {
                "nodeId": site_id,
                "nodeName": site_config["name"],
                "deviceType": site_config["device_type"],
                "classificationCode": site_config["classification_code"],
                "classificationName": site_config["classification_name"],
                "deviceName": site_config["device_name"],
                "dimension": "day",
                "startTime": f"{date} 00:00:00",
                "endTime": f"{date} 23:59:59",
                "deviceCodes": site_config["device_codes"],
                "deviceLevel": site_config["device_level"],
            }

            # 调用福加 API
            resp = httpx.post(
                f"{FUCA_API_BASE_URL}/analysisWeb/energyAnalysis/v1/ECInfo",
                json=payload,
                headers={
                    "Authorization": f"Bearer {FUCA_API_TOKEN}",
                    "tenant_id": FUCA_TENANT_ID,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            # 解析响应
            if data.get("code") != 200:
                return {"error": f"API 返回错误: {data.get('message', '未知错误')}"}

            api_data = data.get("data", {})

            # 字段映射：真实接口 → EnergySummary 模型
            return EnergySummary(
                site_id=site_id,
                date=date,
                total_consumption_kwh=api_data.get("totalEnergy", 0.0),
                pv_generation_kwh=0.0,  # 接口未返回光伏数据
                grid_import_kwh=api_data.get("totalEnergy", 0.0),
                storage_charge_kwh=0.0,  # 接口未返回储能数据
                storage_discharge_kwh=0.0,
                peak_load_kw=api_data.get("maxEnergy", 0.0),
                avg_load_kw=api_data.get("avgEnergy", 0.0),
                carbon_reduction_kg=api_data.get("totalEnergy", 0.0) * api_data.get("carbonCoefficient", 0.0),
            ).model_dump()

        # Mock fallback
        total = round(random.uniform(8000, 15000), 1)
        pv = round(random.uniform(1500, 4000), 1)
        grid = round(total - pv + random.uniform(-500, 500), 1)
        return EnergySummary(
            site_id=site_id,
            date=date,
            total_consumption_kwh=total,
            pv_generation_kwh=pv,
            grid_import_kwh=max(0, round(grid, 1)),
            storage_charge_kwh=round(random.uniform(200, 800), 1),
            storage_discharge_kwh=round(random.uniform(100, 600), 1),
            peak_load_kw=round(random.uniform(400, 900), 1),
            avg_load_kw=round(random.uniform(300, 600), 1),
            carbon_reduction_kg=round(pv * 0.57, 1),
        ).model_dump()
    except Exception as e:
        logger.error(f"fetch_energy_summary 失败: {e}")
        return {"error": f"fetch_energy_summary: {e}"}


# ── 活跃报警 ──────────────────────────────────────────────────────

def fetch_active_alarms(site_id: str) -> Dict[str, Any]:
    """获取站点当前活跃报警列表。

    Args:
        site_id: 站点 ID（如 SH-01）

    Returns:
        AlarmList 的 dict 表示
    """
    try:
        if not _is_mock():
            import httpx
            resp = httpx.get(
                f"{JAVA_API_BASE_URL}/alarms",
                params={"site_id": site_id},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return AlarmList(
                site_id=data["site_id"],
                total_count=data["total_count"],
                alarms=[AlarmItem(**a) for a in data.get("alarms", [])],
            ).model_dump()

        # Mock fallback
        mock_alarms = [
            AlarmItem(
                alarm_id=f"ALM-{site_id}-001",
                level="warning",
                device="冷水机组#1",
                message="冷凝器趋近温度偏高 (3.8℃)，建议清洗冷凝器",
                timestamp=datetime.now(timezone.utc).isoformat(),
                acknowledged=False,
            ),
            AlarmItem(
                alarm_id=f"ALM-{site_id}-002",
                level="warning",
                device="冷却塔#2",
                message="冷却塔风机电流偏差 >15%，请检查皮带",
                timestamp=datetime.now(timezone.utc).isoformat(),
                acknowledged=False,
            ),
            AlarmItem(
                alarm_id=f"ALM-{site_id}-003",
                level="info",
                device="冷冻水泵#1",
                message="变频器频率已达上限 (50Hz)，切换备机检查",
                timestamp=datetime.now(timezone.utc).isoformat(),
                acknowledged=True,
            ),
        ]
        return AlarmList(
            site_id=site_id,
            total_count=len(mock_alarms),
            alarms=mock_alarms,
        ).model_dump()
    except Exception as e:
        logger.error(f"fetch_active_alarms 失败: {e}")
        return {"error": f"fetch_active_alarms: {e}"}
