"""java_backend — 福加监控数据工具（COP / 能耗 / 报警 / 碳排 / 光伏 / 排名 / 环境 / 能效日历）

所属层：tools
依赖：src.schemas.action_agent, src.utils.fuca_token_refresher, httpx, os, yaml
对接 V3 引擎：N/A（对接福加 API 真实监控数据）

Phase 4.2: 所有工具接入真实 API，未配置 FUCA_API_BASE_URL 时走 Mock fallback。
Phase 4.3: Token 自动刷新 — 401 时自动调用 fuca_token_refresher 重新登录获取 Token。
"""
import logging
import os
import random
import threading
import yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from src.schemas.action_agent import (
    COPData,
    EnergySummary,
    AlarmItem,
    AlarmList,
    CarbonInfo,
    EnergyUsage,
    DeviceRank,
    EnvironmentParams,
    EfficiencyCalendarDay,
    EfficiencyCalendarMonth,
)

logger = logging.getLogger(__name__)

# ── 福加 API 配置（动态 Token 管理） ──────────────────────────────

FUCA_API_BASE_URL = os.getenv("FUCA_API_BASE_URL")
FUCA_TENANT_ID = os.getenv("FUCA_TENANT_ID")

# Token 动态管理：进程内缓存 + 线程锁，401 时自动刷新
_token_lock = threading.Lock()
_cached_token: Optional[str] = os.getenv("FUCA_API_TOKEN")


def _get_token() -> Optional[str]:
    """获取当前可用的 Token（优先缓存，回退环境变量）。"""
    global _cached_token
    if _cached_token is None:
        _cached_token = os.getenv("FUCA_API_TOKEN")
    return _cached_token


def _refresh_token_if_possible() -> Optional[str]:
    """尝试自动刷新 Token，成功返回新 Token，失败返回 None。

    需要 .env 中配置 FUCA_LOGIN_NAME 和 FUCA_PASSWORD。
    """
    global _cached_token
    from src.utils.fuca_token_refresher import refresh_token

    try:
        new_token = refresh_token(update_env=True)
        _cached_token = new_token
        logger.info("福加 Token 自动刷新成功")
        return new_token
    except Exception as e:
        logger.warning(f"福加 Token 自动刷新失败: {e}")
        return None

# 站点映射配置缓存
_SITE_MAPPING: Optional[Dict[str, Any]] = None


# ── 内部工具函数 ──────────────────────────────────────────────────

def _load_site_mapping() -> Dict[str, Any]:
    """加载站点映射配置（缓存）。"""
    global _SITE_MAPPING
    if _SITE_MAPPING is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "site_mapping.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            _SITE_MAPPING = yaml.safe_load(f)
    return _SITE_MAPPING


def _is_mock() -> bool:
    """判断是否使用 Mock 数据（未配置 API 地址时）。"""
    return FUCA_API_BASE_URL is None


def _get_site_config(site_id: str) -> Dict[str, Any]:
    """获取站点配置，不存在时返回空字典。"""
    return _load_site_mapping().get("sites", {}).get(site_id, {})


def _headers() -> Dict[str, str]:
    """构建福加 API 公共请求头（使用动态 Token）。"""
    token = _get_token()
    return {
        "Authorization": f"Bearer {token}",
        "tenant_id": FUCA_TENANT_ID,
    }


def _api_get(path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """福加 API GET 请求，支持 401 自动刷新 Token 并重试一次。

    Args:
        path: API 路径（如 /integrateMonitor/fucaOverviewScreen/carbonInfo）
        params: 查询参数

    Returns:
        API 响应中的 data 字段

    Raises:
        httpx.HTTPStatusError: 非 401 的 HTTP 错误
        RuntimeError: API 返回 code != 200
    """
    url = f"{FUCA_API_BASE_URL}{path}"
    resp = httpx.get(url, params=params, headers=_headers(), timeout=10)

    # 401 → 自动刷新 Token 并重试一次
    if resp.status_code == 401:
        logger.warning(f"GET {path} 返回 401，尝试自动刷新 Token...")
        with _token_lock:
            _refresh_token_if_possible()
        resp = httpx.get(url, params=params, headers=_headers(), timeout=10)

    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        # 业务层 401（部分福加 API 用 code=401 而非 HTTP 401）
        if body.get("code") == 401:
            logger.warning(f"GET {path} 返回 code=401，尝试自动刷新 Token...")
            with _token_lock:
                _refresh_token_if_possible()
            resp = httpx.get(url, params=params, headers=_headers(), timeout=10)
            resp.raise_for_status()
            body = resp.json()
            if body.get("code") != 200:
                raise RuntimeError(f"API 返回错误（刷新后重试仍失败）: {body.get('message', '未知错误')}")
        else:
            raise RuntimeError(f"API 返回错误: {body.get('message', '未知错误')}")
    return body.get("data", {})


def _api_post(path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    """福加 API POST 请求，支持 401 自动刷新 Token 并重试一次。

    Args:
        path: API 路径
        json_body: 请求体

    Returns:
        API 响应中的 data 字段

    Raises:
        httpx.HTTPStatusError: 非 401 的 HTTP 错误
        RuntimeError: API 返回 code != 200
    """
    url = f"{FUCA_API_BASE_URL}{path}"
    resp = httpx.post(url, json=json_body, headers=_headers(), timeout=10)

    # 401 → 自动刷新 Token 并重试一次
    if resp.status_code == 401:
        logger.warning(f"POST {path} 返回 401，尝试自动刷新 Token...")
        with _token_lock:
            _refresh_token_if_possible()
        resp = httpx.post(url, json=json_body, headers=_headers(), timeout=10)

    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        if body.get("code") == 401:
            logger.warning(f"POST {path} 返回 code=401，尝试自动刷新 Token...")
            with _token_lock:
                _refresh_token_if_possible()
            resp = httpx.post(url, json=json_body, headers=_headers(), timeout=10)
            resp.raise_for_status()
            body = resp.json()
            if body.get("code") != 200:
                raise RuntimeError(f"API 返回错误（刷新后重试仍失败）: {body.get('message', '未知错误')}")
        else:
            raise RuntimeError(f"API 返回错误: {body.get('message', '未知错误')}")
    return body.get("data", {})


def _query_point_group_names(point_names: list, device_code: str = "") -> Dict[str, str]:
    """通用 pointGroupNames 查询（COP 和环境参数共用）。

    Args:
        point_names: 要查询的参数名列表
        device_code: 设备 code（环境参数需要，COP 不需要）

    Returns:
        {参数名: 值, ...}
    """
    body: Dict[str, Any] = {"pointGroupNames": point_names}
    if device_code:
        body["currentDeviceCode"] = device_code
    return _api_post("/integrateMonitor/chillerRoom/getValueByPointGroupNames", body)


# ── COP 数据 ──────────────────────────────────────────────────────

def fetch_cop_data(site_id: str, chiller_id: str = "CH-01") -> Dict[str, Any]:
    """获取冷水机房 COP（能效比）数据 + 机组运行参数（温度/功率）。

    组合两个真实 API:
    - getValueByPointGroupNames: 机房级 COP（水系统累计/瞬时）
    - getDeviceRunningInfo: 机组级运行数据（蒸发器/冷凝器温度、实时功率）

    Args:
        site_id: 站点 ID（如 FJJB000001）
        chiller_id: 冷水机组编号（CH-01 或 CH-02）

    Returns:
        COPData 的 dict 表示
    """
    try:
        if not _is_mock():
            site_config = _get_site_config(site_id)

            # 1. 获取机房级 COP
            point_names = site_config.get("cop_point_names", [
                "水系统累计COP", "水系统瞬时COP"
            ])
            cop_data = _query_point_group_names(point_names)
            instant_cop = float(cop_data.get("水系统瞬时COP", 0))
            cumulative_cop = float(cop_data.get("水系统累计COP", 0))

            # 2. 获取机组级运行数据（温度/功率）
            chiller_ids = site_config.get("chiller_device_ids", {})
            device_id = chiller_ids.get(chiller_id)
            chilled_water_out_temp = 0.0
            cooling_water_in_temp = 0.0
            power_kw = 0.0

            if device_id:
                try:
                    running_info = _api_post(
                        "/integrateMonitor/device/running/getDeviceRunningInfo",
                        {"deviceId": device_id}
                    )
                    # 解析蒸发器温度
                    evaporator = running_info.get("YXSJ-ZFQ", {}).get("YXSJ-ZFQ", [])
                    for item in evaporator:
                        if item.get("propertyName") == "蒸发器出水温度":
                            chilled_water_out_temp = float(item.get("propertyValue", 0))

                    # 解析冷凝器温度
                    condenser = running_info.get("YXSJ-LNQ", {}).get("YXSJ-LNQ", [])
                    for item in condenser:
                        if item.get("propertyName") == "冷凝器进水温度":
                            cooling_water_in_temp = float(item.get("propertyValue", 0))

                    # 解析实时功率
                    overall = running_info.get("ZT", {}).get("ZT", [])
                    for item in overall:
                        if item.get("propertyName") == "机组实时功率":
                            power_kw = float(item.get("propertyValue", 0))
                except Exception as e:
                    logger.warning(f"getDeviceRunningInfo 失败，温度/功率字段为 0: {e}")

            return COPData(
                site_id=site_id,
                chiller_id=chiller_id,
                instant_cop=instant_cop,
                cumulative_cop=cumulative_cop,
                chilled_water_out_temp=chilled_water_out_temp,
                cooling_water_in_temp=cooling_water_in_temp,
                power_kw=power_kw,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status="normal",
            ).model_dump()

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

def fetch_energy_summary(site_id: str, date: str = "") -> Dict[str, Any]:
    """获取站点单日能耗汇总数据。

    组合真实 API: supplyAndDemandList（按小时供需数据：电网/光伏/储能充放电/负荷/卖电）

    Args:
        site_id: 站点 ID（如 FJJB000001）
        date: 统计日期，格式 YYYY-MM-DD，默认今天

    Returns:
        EnergySummary 的 dict 表示
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        if not _is_mock():
            # 1. 获取日度供需数据（按小时）
            supply_data = _api_get(
                "/integrateMonitor/photovoltaicStorage/supplyAndDemandList",
                {"date": date}
            )

            # 2. 汇总各分项（每小时数据，value 单位 kW，×1h = kWh）
            total_grid = 0.0      # 电网取电
            total_pv = 0.0        # 光伏发电
            total_charge = 0.0    # 储能充电
            total_discharge = 0.0 # 储能放电
            total_load = 0.0      # 用电负荷
            total_sell = 0.0      # 上网卖电
            peak_load = 0.0       # 峰值负荷
            loads = []

            for hour in supply_data:
                for item in hour.get("supplyList", []):
                    code = item.get("code", "")
                    val = float(item.get("value", 0))
                    if code == "powerGrid":
                        total_grid += val
                    elif code == "photovoltaic":
                        total_pv += val
                    elif code == "energyStorageDischarge":
                        total_discharge += val

                for item in hour.get("demandList", []):
                    code = item.get("code", "")
                    val = float(item.get("value", 0))
                    if code == "energyStorageCharge":
                        total_charge += val
                    elif code == "electricalLoad":
                        total_load += val
                        loads.append(val)
                        peak_load = max(peak_load, val)
                    elif code == "powerGridSale":
                        total_sell += val

            avg_load = sum(loads) / len(loads) if loads else 0.0
            # 碳减排 = 光伏发电量 × 0.57 kgCO₂e/kWh（国标排放因子）
            carbon_reduction = total_pv * 0.57

            return EnergySummary(
                site_id=site_id,
                date=date,
                total_consumption_kwh=total_load,
                pv_generation_kwh=total_pv,
                grid_import_kwh=total_grid,
                storage_charge_kwh=total_charge,
                storage_discharge_kwh=total_discharge,
                peak_load_kw=peak_load,
                avg_load_kw=round(avg_load, 2),
                carbon_reduction_kg=round(carbon_reduction, 2),
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

    动态计算最近 N 天的时间范围（N 由 site_mapping.yaml 的 alarm_days 配置）。

    Args:
        site_id: 站点 ID

    Returns:
        AlarmList 的 dict 表示
    """
    try:
        if not _is_mock():
            site_config = _get_site_config(site_id)
            alarm_days = site_config.get("alarm_days", 7)
            now = datetime.now()
            start = (now - timedelta(days=alarm_days)).strftime("%Y-%m-%d 00:00:00")
            end = now.strftime("%Y-%m-%d 23:59:59")

            api_data = _api_post("/intelligentAlarm/alarm/listRealAlarms", {
                "startTime": start, "endTime": end, "pageNum": 1, "pageSize": 10,
            })
            records = api_data.get("records", [])
            alarms = [
                AlarmItem(
                    alarm_id=str(r.get("id", f"ALM-{i}")),
                    level=r.get("alarmLevel", "info"),
                    device=r.get("deviceName", "未知设备"),
                    message=r.get("alarmContent", r.get("alarmName", "未知报警")),
                    timestamp=r.get("alarmTime", datetime.now(timezone.utc).isoformat()),
                    acknowledged=r.get("status", 0) == 1,
                )
                for i, r in enumerate(records)
            ]
            return AlarmList(
                site_id=site_id,
                total_count=api_data.get("total", 0),
                alarms=alarms,
            ).model_dump()

        # Mock fallback
        mock_alarms = [
            AlarmItem(
                alarm_id=f"ALM-{site_id}-001", level="warning", device="冷水机组#1",
                message="冷凝器趋近温度偏高 (3.8℃)，建议清洗冷凝器",
                timestamp=datetime.now(timezone.utc).isoformat(), acknowledged=False,
            ),
            AlarmItem(
                alarm_id=f"ALM-{site_id}-002", level="warning", device="冷却塔#2",
                message="冷却塔风机电流偏差 >15%，请检查皮带",
                timestamp=datetime.now(timezone.utc).isoformat(), acknowledged=False,
            ),
            AlarmItem(
                alarm_id=f"ALM-{site_id}-003", level="info", device="冷冻水泵#1",
                message="变频器频率已达上限 (50Hz)，切换备机检查",
                timestamp=datetime.now(timezone.utc).isoformat(), acknowledged=True,
            ),
        ]
        return AlarmList(site_id=site_id, total_count=len(mock_alarms), alarms=mock_alarms).model_dump()
    except Exception as e:
        logger.error(f"fetch_active_alarms 失败: {e}")
        return {"error": f"fetch_active_alarms: {e}"}


# ── 碳排信息（光伏月发电 + 碳减排） ──────────────────────────────

def fetch_carbon_info(site_id: str) -> Dict[str, Any]:
    """获取碳排信息：本月光伏发电量、碳减排量、累计碳减排、环比数据。

    Args:
        site_id: 站点 ID

    Returns:
        CarbonInfo 的 dict 表示
    """
    try:
        if not _is_mock():
            api_data = _api_get("/integrateMonitor/fucaOverviewScreen/carbonInfo")
            return CarbonInfo(
                photovoltaic_month_kwh=float(api_data.get("photovoltaicMonth", 0)),
                carbon_reduce_month_kg=float(api_data.get("carbonReduceMonth", 0)),
                carbon_reduce_total_kg=float(api_data.get("carbonReduceTotal", 0)),
                pv_mom_pct=float(api_data.get("photovoltaicMonthMoM", 0)),
                carbon_mom_pct=float(api_data.get("carbonReduceMonthMoM", 0)),
            ).model_dump()

        # Mock fallback
        pv = round(random.uniform(20000, 40000), 1)
        return CarbonInfo(
            photovoltaic_month_kwh=pv,
            carbon_reduce_month_kg=round(pv * 0.6, 1),
            carbon_reduce_total_kg=round(random.uniform(150000, 200000), 1),
            pv_mom_pct=round(random.uniform(-10, 30), 1),
            carbon_mom_pct=round(random.uniform(-10, 30), 1),
        ).model_dump()
    except Exception as e:
        logger.error(f"fetch_carbon_info 失败: {e}")
        return {"error": f"fetch_carbon_info: {e}"}


# ── 光伏月度数据（发电量 + 收益） ─────────────────────────────────

def fetch_photovoltaic_monthly(site_id: str) -> Dict[str, Any]:
    """获取光伏月度发电量和收益明细（按月列表）。

    真实 API: GET /integrateMonitor/fucaOverviewScreen/photovoltaicList

    Args:
        site_id: 站点 ID

    Returns:
        dict: {months: [{month, generation_kwh, earnings_yuan}, ...]}
    """
    try:
        if not _is_mock():
            api_data = _api_get("/integrateMonitor/fucaOverviewScreen/photovoltaicList")
            months = []
            for item in api_data:
                gen = next((x["value"] for x in item.get("list", []) if x["code"] == "discharge"), 0)
                earn = next((x["value"] for x in item.get("list", []) if x["code"] == "earnings"), 0)
                months.append({"month": item["ts"], "generation_kwh": float(gen), "earnings_yuan": float(earn)})
            return {"months": months}

        # Mock fallback
        months = []
        for m in range(1, 7):
            gen = round(random.uniform(30000, 55000), 1)
            months.append({
                "month": f"2026-{m:02d}",
                "generation_kwh": gen,
                "earnings_yuan": round(gen * 0.55, 2),
            })
        return {"months": months}
    except Exception as e:
        logger.error(f"fetch_photovoltaic_monthly 失败: {e}")
        return {"error": f"fetch_photovoltaic_monthly: {e}"}


# ── 日度光伏发电量 ─────────────────────────────────────────────────

def fetch_photovoltaic_daily(site_id: str, date: str = "") -> Dict[str, Any]:
    """获取指定日期的光伏发电量。

    真实 API: GET /integrateMonitor/photovoltaicStorage/realTimePowerList
    返回 15 分钟间隔的功率数据，通过累加（功率 × 0.25h）计算日发电量。

    Args:
        site_id: 站点 ID
        date: 查询日期，格式 YYYY-MM-DD，默认今天

    Returns:
        dict: {date, generation_kwh, peak_power_kw, data_points}
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        if not _is_mock():
            api_data = _api_get("/integrateMonitor/photovoltaicStorage/realTimePowerList", {
                "date": date,
            })

            # 累加光伏发电量：每个数据点间隔 15 分钟 = 0.25 小时
            total_kwh = 0.0
            peak_kw = 0.0
            count = 0
            for item in api_data:
                for p in item.get("powerInfoList", []):
                    if p.get("code") == "photovoltaic":
                        power = abs(float(p.get("value", 0)))  # 光伏值为负，取绝对值
                        total_kwh += power * 0.25  # 15min = 0.25h
                        peak_kw = max(peak_kw, power)
                        count += 1
                        break

            return {
                "date": date,
                "generation_kwh": round(total_kwh, 1),
                "peak_power_kw": round(peak_kw, 1),
                "data_points": count,
            }

        # Mock fallback
        return {
            "date": date,
            "generation_kwh": round(random.uniform(80, 200), 1),
            "peak_power_kw": round(random.uniform(40, 100), 1),
            "data_points": 96,
        }
    except Exception as e:
        logger.error(f"fetch_photovoltaic_daily 失败: {e}")
        return {"error": f"fetch_photovoltaic_daily: {e}"}


# ── 全厂用电量（今日 + 本月 + 趋势） ─────────────────────────────

def fetch_energy_usage(site_id: str) -> Dict[str, Any]:
    """获取全厂用电量：今日用电、本月用电、环比数据。

    Args:
        site_id: 站点 ID

    Returns:
        EnergyUsage 的 dict 表示
    """
    try:
        if not _is_mock():
            api_data = _api_get("/analysisWeb/energyAnalysis/cockpit/energyUsage")
            return EnergyUsage(
                today_kwh=float(api_data.get("todayE", 0)),
                month_kwh=float(api_data.get("monthE", 0)),
                today_mom_pct=float(api_data.get("todayMoM", 0)),
                month_mom_pct=float(api_data.get("monthMoM", 0)),
            ).model_dump()

        # Mock fallback
        return EnergyUsage(
            today_kwh=round(random.uniform(2500, 5000), 1),
            month_kwh=round(random.uniform(40000, 60000), 1),
            today_mom_pct=round(random.uniform(-20, 20), 1),
            month_mom_pct=round(random.uniform(-20, 20), 1),
        ).model_dump()
    except Exception as e:
        logger.error(f"fetch_energy_usage 失败: {e}")
        return {"error": f"fetch_energy_usage: {e}"}


# ── 设备用电排名 ──────────────────────────────────────────────────

def fetch_device_rank(site_id: str, rank_type: str = "factory") -> Dict[str, Any]:
    """获取设备用电排名。

    rank_type="factory": 全厂设备排名 Top5（GET deviceEnergyRankTop5Month）
    rank_type="room": 机房设备排名（GET cockpit/roomEnergy，含 COP）

    Args:
        site_id: 站点 ID
        rank_type: "factory"（全厂）或 "room"（机房）

    Returns:
        DeviceRank 的 dict 表示
    """
    try:
        if not _is_mock():
            if rank_type == "room":
                site_config = _get_site_config(site_id)
                api_data = _api_get("/integrateMonitor/cockpit/roomEnergy", {
                    "deviceId": site_config.get("cwer_id", 3602),
                    "deviceCode": site_config.get("cwer_device_code", "KTXT-CWER-0001"),
                })
                items = [
                    {"name": d["name"], "value_kwh": float(d["value"]), "proportion_pct": float(d["prop"])}
                    for d in api_data.get("deviceEnergyList", [])
                ]
                return DeviceRank(
                    rank_type=rank_type,
                    items=items,
                    room_cop_instant=float(api_data.get("copInstant", 0)),
                    room_cop_avg=float(api_data.get("copAvg", 0)),
                ).model_dump()
            else:
                api_data = _api_get("/integrateMonitor/energyMonitor/v1/deviceEnergyRankTop5Month")
                items = sorted(
                    [{"name": name, "value_kwh": float(value)} for name, value in api_data.items()],
                    key=lambda x: x["value_kwh"], reverse=True,
                )
                return DeviceRank(rank_type=rank_type, items=items).model_dump()

        # Mock fallback
        if rank_type == "room":
            items = [
                {"name": "冷水机组", "value_kwh": round(random.uniform(2000, 3000), 1), "proportion_pct": 69.5},
                {"name": "冷却水泵", "value_kwh": round(random.uniform(400, 600), 1), "proportion_pct": 15.4},
                {"name": "冷水泵", "value_kwh": round(random.uniform(300, 500), 1), "proportion_pct": 11.8},
                {"name": "冷却塔", "value_kwh": round(random.uniform(80, 150), 1), "proportion_pct": 3.3},
            ]
        else:
            items = [
                {"name": "综合楼照明动力", "value_kwh": round(random.uniform(10000, 15000), 1)},
                {"name": "园区储能电站", "value_kwh": round(random.uniform(8000, 12000), 1)},
                {"name": "生产厂房照明动力", "value_kwh": round(random.uniform(3000, 6000), 1)},
                {"name": "办公室顶楼电表", "value_kwh": round(random.uniform(3000, 5000), 1)},
                {"name": "生产厂房生产用电", "value_kwh": round(random.uniform(2000, 4000), 1)},
            ]
        return DeviceRank(rank_type=rank_type, items=items).model_dump()
    except Exception as e:
        logger.error(f"fetch_device_rank 失败: {e}")
        return {"error": f"fetch_device_rank: {e}"}


# ── 环境参数 ──────────────────────────────────────────────────────

def fetch_environment_params(site_id: str) -> Dict[str, Any]:
    """获取室外环境参数：温度、湿度、湿球温度、焓值。

    与 COP 共用 pointGroupNames 接口。

    Args:
        site_id: 站点 ID

    Returns:
        EnvironmentParams 的 dict 表示
    """
    try:
        if not _is_mock():
            site_config = _get_site_config(site_id)
            point_names = site_config.get("env_point_names", [
                "室外温度", "室外湿度", "室外湿球温度", "室外焓值"
            ])
            device_code = site_config.get("cwer_device_code", "KTXT-CWER-0001")
            api_data = _query_point_group_names(point_names, device_code)
            return EnvironmentParams(
                outdoor_temp_c=float(api_data.get("室外温度", 0)),
                outdoor_humidity_pct=float(api_data.get("室外湿度", 0)),
                wet_bulb_temp_c=float(api_data.get("室外湿球温度", 0)),
                enthalpy_kj_kg=float(api_data.get("室外焓值", 0)),
            ).model_dump()

        # Mock fallback
        return EnvironmentParams(
            outdoor_temp_c=round(random.uniform(25, 38), 1),
            outdoor_humidity_pct=round(random.uniform(40, 70), 1),
            wet_bulb_temp_c=round(random.uniform(18, 26), 1),
            enthalpy_kj_kg=round(random.uniform(55, 75), 1),
        ).model_dump()
    except Exception as e:
        logger.error(f"fetch_environment_params 失败: {e}")
        return {"error": f"fetch_environment_params: {e}"}


# ── 能效日历 ──────────────────────────────────────────────────────

def fetch_efficiency_calendar(site_id: str, date: str = "", mode: str = "day") -> Dict[str, Any]:
    """获取能效日历数据（日度或月度）。

    mode="day": 当月每天的 COP / 制冷量 / 用电量
    mode="month": 月度汇总（COP / 制冷量 / 电费 / 电价）

    Args:
        site_id: 站点 ID
        date: 查询月份，格式 YYYY-MM，默认当月
        mode: "day" 或 "month"

    Returns:
        日度: {month, days: [EfficiencyCalendarDay, ...]}
        月度: EfficiencyCalendarMonth 的 dict
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m")

        if not _is_mock():
            site_config = _get_site_config(site_id)
            cwer_id = site_config.get("cwer_id", 3602)

            if mode == "month":
                api_data = _api_get("/analysisWeb/EfficiencyCalendar/queryCOP", {
                    "date": date, "cwerId": cwer_id,
                })
                return EfficiencyCalendarMonth(
                    month=date,
                    current_cop=float(api_data.get("currentCOP", 0)),
                    average_cop=float(api_data.get("averageCOP", 0)),
                    electricity_kwh=float(api_data.get("electricity", 0)),
                    cool_kwh=float(api_data.get("cool", 0)),
                    cool_price=float(api_data.get("coolPrice", 0)),
                    electricity_charge=float(api_data.get("echarge", 0)),
                    electricity_price=float(api_data.get("eprice", 0)),
                ).model_dump()
            else:
                api_data = _api_get("/analysisWeb/EfficiencyCalendar/queryCalendar", {
                    "date": date, "cwerId": cwer_id,
                })
                days = [
                    EfficiencyCalendarDay(
                        date=r.get("date", ""),
                        cop=float(r.get("cop", 0)),
                        cool_kwh=float(r.get("cool", 0)),
                        electricity_kwh=float(r.get("electricity", 0)),
                        is_today=r.get("nowDay", False),
                    ).model_dump()
                    for r in api_data
                ]
                return {"month": date, "days": days}

        # Mock fallback
        if mode == "month":
            return EfficiencyCalendarMonth(
                month=date,
                current_cop=round(random.uniform(5.0, 8.0), 1),
                average_cop=round(random.uniform(3.0, 6.0), 1),
                electricity_kwh=round(random.uniform(2500, 4000), 1),
                cool_kwh=round(random.uniform(15000, 25000), 1),
                cool_price=0.18,
                electricity_charge=round(random.uniform(3000, 5000), 2),
                electricity_price=1.2,
            ).model_dump()
        else:
            days = [
                EfficiencyCalendarDay(
                    date=f"{date}-{d:02d}",
                    cop=round(random.uniform(4.5, 8.0), 1),
                    cool_kwh=round(random.uniform(500, 5000), 1),
                    electricity_kwh=round(random.uniform(50, 800), 1),
                    is_today=(d == datetime.now().day),
                ).model_dump()
                for d in range(1, 13)
            ]
            return {"month": date, "days": days}
    except Exception as e:
        logger.error(f"fetch_efficiency_calendar 失败: {e}")
        return {"error": f"fetch_efficiency_calendar: {e}"}


# ── 能效查询通用详情 ──────────────────────────────────────────────

def fetch_efficiency_detail(site_id: str, param_name: str = "水系统平均COP") -> Dict[str, Any]:
    """通用能效查询：按参数名查询任意能效指标的时间序列。

    真实 API: POST /analysisWeb/efficiencyQuery/v1/queryPointEnergyEfficiency
    通过 site_mapping.yaml 的 efficiency_points 目录解析 param_name → pointId。

    可用 param_name:
      水系统平均COP, 冷水主机平均COP, 水系统平均SCOP,
      水系统瞬时制冷量, 水系统累计制冷量,
      水系统瞬时功率, 水系统累计电能, 水系统热平衡系数

    Args:
        site_id: 站点 ID
        param_name: 查询参数名（见上方列表）

    Returns:
        dict: {param_name, unit, current_value, latest_time, time_series_count}
        若 param_name 不在目录中，返回 error 并列出可用参数。
    """
    try:
        site_config = _get_site_config(site_id)
        points = site_config.get("efficiency_points", {})

        if param_name not in points:
            available = list(points.keys())
            return {"error": f"未知参数: {param_name}。可用参数: {', '.join(available)}"}

        point = points[param_name]

        if _is_mock():
            return {
                "param_name": param_name,
                "unit": point.get("unit", ""),
                "current_value": round(random.uniform(3.0, 10.0), 2),
                "latest_time": datetime.now().isoformat(),
                "time_series_count": 120,
            }

        now = datetime.now()
        start = now.strftime("%Y-%m-%d 00:00:00")
        end = (now + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

        api_data = _api_post("/analysisWeb/efficiencyQuery/v1/queryPointEnergyEfficiency", {
            "dimension": "day",
            "startTime": start,
            "endTime": end,
            "pointName": point["point_name"],
            "pointId": point["point_id"],
            "attrType": "I",
            "objName": point["obj_name"],
            "paramName": point["param_name"],
            "unit": point.get("unit", ""),
        })

        values = api_data.get("pointValues", [])
        current = float(values[-1]["v"]) if values else 0.0
        latest_ts = values[-1]["ts"] if values else ""

        return {
            "param_name": param_name,
            "unit": point.get("unit", ""),
            "current_value": current,
            "latest_time": latest_ts,
            "time_series_count": len(values),
        }
    except Exception as e:
        logger.error(f"fetch_efficiency_detail 失败: {e}")
        return {"error": f"fetch_efficiency_detail: {e}"}
