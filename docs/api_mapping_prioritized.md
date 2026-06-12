# 福加真实 API 接口映射（优先级排序）

> **基于**: `docs/跳转接口逻辑.md`（原始清单，31 条）
> **状态**: Task 1 完成（质量检查 + 交互式补全）
> **更新日期**: 2026-06-12

---

## 全局参数

| 参数 | 值 | 来源 |
|------|-----|------|
| cwerId（机房ID） | `3602` | 福加江北工厂冷水机房 |
| currentDeviceCode | `KTXT-CWER-0001` | 环境参数查询 |
| 设备 deviceCodes | 见下方 P1 批次 | 能耗排名查询 |

---

## 🔴 P0 高优先级（Batch 1）— 接口信息完整 + 高业务价值

### 1. 机房/空调累计COP + 瞬时COP

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /integrateMonitor/chillerRoom/getValueByPointGroupNames` |
| **入参** | `{"pointGroupNames": ["水系统累计COP", "机组累计COP", "机组瞬时COP", "水系统瞬时COP"]}` |
| **出参** | `data` 中对应字段（float） |
| **跳转路由** | `/analysis/query` |
| **跳转页面** | 用能分析_能效查询 |
| **触发方式** | 能效查询页面操作 |
| **对应工具** | `fetch_cop_data`（替换现有 Mock） |
| **备注** | 累计COP 和瞬时COP 共用同一接口，通过 pointGroupNames 区分 |

### 2. 实时报警

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /intelligentAlarm/alarm/listRealAlarms` |
| **入参** | `startTime`（动态：7天前 00:00:00）, `endTime`（动态：今天 23:59:59）, `pageNum=1`, `pageSize=10` |
| **出参** | `total`（int）|
| **跳转路由** | `/alarm/realtime` |
| **跳转页面** | 报警管理_实时报警 |
| **触发方式** | 报警管理-实时报警页面操作 |
| **对应工具** | `fetch_active_alarms`（替换现有 Mock） |

### 3. 月度光伏发电量

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/carbonInfo` |
| **入参** | 无 |
| **出参** | `photovoltaicMonth`（float） |
| **跳转路由** | `/coordination/energy` |
| **跳转页面** | 光储协同_实时能量 |
| **触发方式** | 光储协同-实时能量页面操作 |
| **对应工具** | 新增 `fetch_photovoltaic_monthly` |

---

## 🟡 P1 中优先级（Batch 2）— 接口信息完整 + 中业务价值

### 4. 全厂今日用电量

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /analysisWeb/energyAnalysis/cockpit/energyUsage` |
| **入参** | 无 |
| **出参** | `todayE`（float） |
| **跳转路由** | `/analysis/consumption-panel` |
| **跳转页面** | 用能分析_能耗分析 |
| **触发方式** | **页面加载自动请求**（无需点击查询） |
| **对应工具** | 新增 `fetch_energy_usage_today` |
| **备注** | 与已接入的 `fetch_energy_summary` 是不同接口（cockpit vs v1/ECInfo） |

### 5. 全厂本月用电量

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /analysisWeb/energyAnalysis/cockpit/energyUsage` |
| **入参** | 无 |
| **出参** | `monthE`（float） |
| **跳转路由** | `/analysis/consumption-panel` |
| **跳转页面** | 用能分析_能耗分析 |
| **触发方式** | 能耗分析页面，时间下拉选择月后点击查询 |
| **对应工具** | 复用 #4 的 `fetch_energy_usage_today`（同接口取不同字段） |

### 6. 本月全厂设备用电排名

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/energyMonitor/v1/deviceEnergyRankTop5Month` |
| **入参** | 无 |
| **出参** | `data` 全部字段 |
| **跳转路由** | `/analysis/rank` |
| **跳转页面** | 用能分析_能耗排名 |
| **触发方式** | 能耗排名页面，排名方式选择按区域，默认本月点击查询 |
| **对应工具** | 新增 `fetch_device_energy_rank` |

### 7. 本月机房设备用电排名

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/cockpit/roomEnergy` |
| **入参** | `deviceCodes`: `["KTXT-CWER-CWEG-0001", "KTXT-CWER-CWEG-0002", "KTXT-CWER-LDWP-0001", "KTXT-CWER-LDWP-0002", "KTXT-CWER-LQWP-0001", "KTXT-CWER-LQWP-0002", "KTXT-CWER-LQT-0001", "KTXT-CWER-LQT-0002"]` |
| **排名对象** | 冷水机组#1, 冷却水泵#1, 冷水泵#1, 冷却塔#1, 冷却塔#2, 冷却水泵#2, 冷水机组#2, 冷水泵#2 |
| **出参** | `data` 全部字段 |
| **跳转路由** | `/analysis/rank` |
| **跳转页面** | 用能分析_能耗排名 |
| **触发方式** | 能耗排名页面，默认显示本月冷水机房设备能耗排名 |
| **对应工具** | 新增 `fetch_room_device_rank` |

### 8. 月度储能充电量 / 放电量 / 收益

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/energyStorageList` |
| **入参** | 无 |
| **出参** | `code=charge` → value（充电量）, `code=discharge` → value（放电量）, `code=earnings` → value（收益） |
| **跳转路由** | `/coordination/energy` |
| **跳转页面** | 光储协同_实时能量 |
| **触发方式** | 驾驶舱页面操作 |
| **对应工具** | 新增 `fetch_energy_storage_monthly` |

### 9. 本月碳减排

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/carbonInfo` |
| **入参** | 无 |
| **出参** | `carbonReduceMonth`（float） |
| **跳转路由** | `/fucaView` |
| **跳转页面** | 项目概览 |
| **触发方式** | 驾驶舱-碳排信息 |
| **对应工具** | 复用 #3 的 `fetch_photovoltaic_monthly`（同 carbonInfo 接口，取不同字段） |

---

## 🟢 P2 低优先级（Batch 3）— 跳转路由待确认 或 特殊场景

### 10. 室外温度 / 湿度 / 湿球温度 / 焓值

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /integrateMonitor/chillerRoom/getValueByPointGroupNames` |
| **入参** | `{"pointGroupNames": ["室外温度", "室外湿度", "室外湿球温度", "室外焓值"], "currentDeviceCode": "KTXT-CWER-0001"}` |
| **出参** | `data` 中对应字段 |
| **跳转路由** | `/index/index`（已确认） |
| **跳转页面** | 首页 |
| **触发方式** | **打开首页自动加载**（无需额外操作） |
| **对应工具** | 新增 `fetch_environment_params` |
| **备注** | 与 COP 共用同一接口，通过 pointGroupNames 区分 |

### 11. 能效日历系列（机房某日COP/制冷量/能耗 + 某月）

| 项目 | 内容 |
|------|------|
| **接口 URL (日)** | `GET /analysisWeb/EfficiencyCalendar/queryCalendar` |
| **入参 (日)** | `date`（用户输入）, `cwerId=3602` |
| **出参 (日)** | `data` 数组中匹配 date 的条目，取 `cop` / `cool` / `electricity` |
| **接口 URL (月)** | `GET /analysisWeb/EfficiencyCalendar/queryCOP` |
| **入参 (月)** | `date`（用户输入）, `cwerId=3602` |
| **出参 (月)** | `averageCOP` / `cool` / `electricity` |
| **跳转路由** | `/analysis/calendar` |
| **跳转页面** | 用能分析_能效日历 |
| **触发方式** | 能效日历页面，下拉选择机房ID，点击日期 |
| **对应工具** | 新增 `fetch_efficiency_calendar`（日 + 月合并为一个工具） |

### 12. 日度光伏发电量

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/photovoltaicStorage/realTimePowerList` |
| **入参** | `date`（用户输入日期） |
| **出参** | 各时刻 `code=photovoltaic` 的 `value` 字段累加 |
| **跳转路由** | `/coordination/energy` |
| **跳转页面** | 光储协同_实时能量 |
| **对应工具** | 新增 `fetch_photovoltaic_daily` |

### 13. 日度储能充电量 / 放电量

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/photovoltaicStorage/supplyAndDemandList` |
| **入参** | `date`（用户输入日期） |
| **出参** | `code=energyStorageCharge` 累加（充电）, `code=energyStorageDischarge` 累加（放电） |
| **跳转路由** | `/coordination/energy` |
| **跳转页面** | 光储协同_实时能量 |
| **对应工具** | 新增 `fetch_energy_storage_daily` |

### 14. 月度光伏发电收益 ✅ 已接入

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/photovoltaicList` |
| **入参** | 无 |
| **出参** | 按月列表：`code=discharge` → 发电量(kWh)，`code=earnings` → 收益(元) |
| **跳转路由** | `/fucaView` |
| **对应工具** | `fetch_photovoltaic_monthly` |
| **状态** | ✅ 已接入 — 通过 GET 直接获取，不需要 hover |

### 15. 本月绿电占比 / 累计绿电占比（暂缓）

| 项目 | 内容 |
|------|------|
| **涉及接口** | 需组合多个接口计算（光伏月发电 ÷ 全厂月用电） |
| **状态** | ⏭️ 暂缓 — 用户决定先忽略 |

---

## 汇总

| 优先级 | 批次 | 独立接口数 | 新增/替换工具 |
|--------|------|-----------|-------------|
| 🔴 P0 | Batch 1 | 3 个接口 | `fetch_cop_data`（替换）+ `fetch_active_alarms`（替换）+ `fetch_photovoltaic_monthly`（新增） |
| 🟡 P1 | Batch 2 | 5 个接口 | `fetch_energy_usage_today` + `fetch_device_energy_rank` + `fetch_room_device_rank` + `fetch_energy_storage_monthly`（复用 carbonInfo） |
| 🟢 P2 | Batch 3 | 5 个接口 | `fetch_environment_params` + `fetch_efficiency_calendar` + `fetch_photovoltaic_daily` + `fetch_energy_storage_daily` + `photovoltaicList`（暂缓） |

**已完成**: 月度光伏收益 → `fetch_photovoltaic_monthly`（通过 GET 直接获取，不需要 hover）

**暂缓**: 绿电占比（多接口组合计算，用户决定先忽略）
