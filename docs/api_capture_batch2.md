# API 抓取数据 — Batch 2 + Batch 3（P1/P2 全量抓取）

> **抓取时间**: 2026-06-12
> **抓取方式**: Chrome MCP 自动抓取
> **站点**: 福加智能 (aiot-fuca.com)，tenant_id=1071

---

## 公共请求头（同 Batch 1）

| Header | 值 |
|--------|-----|
| `authorization` | `Bearer {token}` |
| `tenant_id` | `1071` |
| `accept` | `application/json, text/plain, */*` |

---

## 8. 储能月度数据（充电/放电/收益） ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/energyStorageList` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "data": [{"ts":"2025-12", "list":[{"code":"earnings","value":12525.58},{"code":"charge","value":30476.0},{"code":"discharge","value":27704.0}]}, ...]}` |
| **字段映射** | 按月遍历，每月 list 中：`code=charge` → 充电量(kWh), `code=discharge` → 放电量(kWh), `code=earnings` → 收益(元) |
| **跳转路由** | `/coordination/energy` |
| **数据来源** | 自动抓取（fucaView 页面加载） |
| **对应工具** | `fetch_energy_storage_monthly` |

---

## 9. 光伏月度数据（发电量 + 收益） ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/photovoltaicList` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "data": [{"ts":"2025-12", "list":[{"code":"discharge","value":39463.2},{"code":"earnings","value":25076.2}]}, ...]}` |
| **字段映射** | 按月遍历，每月 list 中：`code=discharge` → 发电量(kWh), `code=earnings` → 收益(元) |
| **跳转路由** | `/fucaView` |
| **数据来源** | 自动抓取（fucaView 页面加载） |
| **对应工具** | 复用 `fetch_carbon_info` 或新增 `fetch_photovoltaic_monthly` |

---

## 10. 光伏累计总发电量 ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/photovoltaicTotalElectricity` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "data": {"totalElectricity": 299678.2}}` |
| **字段映射** | `data.totalElectricity` → total_pv_electricity (kWh) |
| **跳转路由** | `/fucaView` |
| **数据来源** | 自动抓取（fucaView 页面加载） |
| **对应工具** | 复用 `fetch_carbon_info`（同概览页） |

---

## 11. 项目装机容量信息 ✅ 完整（Bonus）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/projectInfo` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "data": {"photovoltaicInstalledCapacity":497, "chargingPilesInstalledCapacity":202, "energyStorageInstalledCapacity":783, "transformerCapacity":2000}}` |
| **字段映射** | `data.photovoltaicInstalledCapacity` → 光伏装机(kW), `data.energyStorageInstalledCapacity` → 储能装机(kWh), `data.chargingPilesInstalledCapacity` → 充电桩(kW), `data.transformerCapacity` → 变压器容量(kVA) |
| **跳转路由** | `/fucaView` |
| **对应工具** | 可合并到 `fetch_carbon_info` 或独立工具 |

---

## 12. 日度供需数据（光储充放 + 负荷） ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/photovoltaicStorage/supplyAndDemandList` |
| **请求参数** | `date=2026-06-12`（用户输入日期） |
| **响应体** | 按小时返回 supplyList（电网供电 + 光伏发电）和 demandList（储能充电 + 用电负荷 + 上网卖电），含 `energyStorageDischarge`（储能放电） |
| **字段映射** | 每小时：supply 中 `code=powerGrid` → 电网供电, `code=photovoltaic` → 光伏; demand 中 `code=energyStorageCharge` → 储能充电, `code=electricalLoad` → 用电负荷; supply 中 `code=energyStorageDischarge` → 储能放电 |
| **跳转路由** | `/coordination/energy` |
| **对应工具** | `fetch_energy_storage_daily` |

---

## 13. 日度实时功率（15分钟间隔） ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/photovoltaicStorage/realTimePowerList` |
| **请求参数** | `date=2026-06-12`（用户输入日期） |
| **响应体** | 每 15 分钟返回 powerInfoList：`powerGrid`(电网), `photovoltaic`(光伏), `energyStorage`(储能), `windPower`(风力), `electricalLoad`(负荷) + flowDirectionList + runningList |
| **字段映射** | `code=photovoltaic` → 光伏功率(kW), `code=energyStorage` → 储能功率(kW，正=充电，负=放电), `code=powerGrid` → 电网功率(kW), `code=electricalLoad` → 负荷功率(kW) |
| **跳转路由** | `/coordination/energy` |
| **对应工具** | `fetch_photovoltaic_daily` |
| **备注** | 光伏 value 为负值表示正在发电输出；能量=功率×0.25h，日度发电量需累加 |

---

## 14. 月度 COP 汇总 ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /analysisWeb/EfficiencyCalendar/queryCOP` |
| **请求参数** | `date=2026-06`（年月）, `cwerId=3602` |
| **响应体** | `{"code":200, "data": {"currentCOP":"6.5", "averageCOP":"3.5", "electricity":"3336.3", "cool":"21776.8", "coolPrice":"0.18", "echarge":"4003.56", "eprice":"1.2"}}` |
| **字段映射** | `data.currentCOP` → 当月COP, `data.averageCOP` → 平均COP, `data.electricity` → 用电量(kWh), `data.cool` → 制冷量(kWh), `data.coolPrice` → 冷价(元/kWh), `data.echarge` → 电费(元), `data.eprice` → 电价(元/kWh) |
| **跳转路由** | `/analysis/calendar` |
| **对应工具** | `fetch_efficiency_calendar`（月度模式） |

---

## 15. 日度能效日历 ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /analysisWeb/EfficiencyCalendar/queryCalendar` |
| **请求参数** | `date=2026-06`（年月）, `cwerId=3602` |
| **响应体** | `{"code":200, "data": [{"date":"2026-06-01","cool":"4088.7","electricity":"693.0","cop":"5.9","nowDay":false}, ...]}` |
| **字段映射** | 按天遍历：`date` → 日期, `cop` → 当日COP, `cool` → 制冷量(kWh), `electricity` → 用电量(kWh), `nowDay` → 是否当天 |
| **跳转路由** | `/analysis/calendar` |
| **对应工具** | `fetch_efficiency_calendar`（日度模式） |

---

## 16. 机房设备列表 ✅ 完整（Bonus）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /analysisWeb/EfficiencyCalendar/queryCwerDevice` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "data": [{"deviceName":"冷水机房#1", "deviceCode":"KTXT-CWER-0001", "deviceTypeCode":"CWER", "deviceId":3602, "deviceTypeId":1071000001, "parentId":0, "deviceTypeName":"冷水机房"}]}` |
| **字段映射** | 返回所有机房设备，`deviceId=3602` 即福加江北冷水机房 |
| **用途** | 获取 cwerId/deviceId 列表，供其他接口参数使用 |

---

## 17. 子设备能耗分布 ✅ 完整（Bonus）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /analysisWeb/EfficiencyCalendar/querySubEnergy` |
| **请求参数** | `date=2026-06`（年月）, `cwerId=3602` |
| **响应体** | `{"code":200, "data": [{"totalE":"3336.3","subName":"冷水机组","subE":"2318.6","subProp":"69.5%"}, {"subName":"冷水泵","subE":"395.1","subProp":"11.8%"}, {"subName":"冷却水泵","subE":"512.3","subProp":"15.4%"}, {"subName":"冷却塔","subE":"110.3","subProp":"3.3%"}, {"subName":"模块机","subE":"0.0","subProp":"--"}, {"subName":"水管阀门","subE":"0.0","subProp":"--"}]}` |
| **字段映射** | 每个子设备：`subName` → 设备名, `subE` → 用电量(kWh), `subProp` → 占比, `totalE` → 总用电量 |
| **跳转路由** | `/analysis/calendar` |
| **对应工具** | 可合并到 `fetch_efficiency_calendar` |

---

## 额外发现：fucaView 页面的 tenantTotalEC

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /integrateMonitor/fucaOverviewScreen/tenantTotalEC` |
| **用途** | 租户累计总用电量（用于计算累计绿电占比） |
| **备注** | 原始清单中"累计绿电占比"需要此接口，暂不实现 |
