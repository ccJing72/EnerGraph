# API 抓取数据 — Batch 1（P0 高优先级）

> **抓取时间**: 2026-06-12
> **抓取方式**: Chrome MCP 自动抓取
> **站点**: 福加智能 (aiot-fuca.com)，账号 AIFUCA，tenant_id=1071

---

## 公共请求头

所有接口共用以下 Header：

| Header | 值 | 说明 |
|--------|-----|------|
| `authorization` | `Bearer {token}` | 动态获取，登录后返回 |
| `tenant_id` | `1071` | 租户 ID |
| `content-type` | `application/json`（POST）/ 无（GET） | |
| `accept` | `application/json, text/plain, */*` | |

---

## 1. 机房 COP ✅ 完整（已修正两次）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /integrateMonitor/chillerRoom/getValueByPointGroupNames` |
| **请求体** | `{"pointGroupNames": ["水系统累计COP", "水系统瞬时COP"]}` |
| **响应体** | `{"code":200, "data": {"水系统累计COP":"7.00", "水系统瞬时COP":"2.10"}}` |
| **字段映射** | `data.水系统累计COP` → cumulative_cop（**机房COP = 7.0，用户看到的"机房平均COP"**）, `data.水系统瞬时COP` → instant_cop |
| **跳转路由** | `/analysis/query` |
| **数据来源** | 自动抓取（首页加载） |
| **对应工具** | `fetch_cop_data` |
| **修正历史** | ① 初始取 `机组累计COP=9.6`（错误，是机组级非机房级）→ ② 改用 efficiencyQuery API 取 `水系统平均COP=9.6`（仍不对）→ ③ 回到 getValueByPointGroupNames 取 `水系统累计COP=7.0`（✅ 正确） |
| **关键区别** | `水系统累计COP`(7.0) = 机房整体能效（冷水机+水泵+冷却塔） = 用户期望值; `机组累计COP`(9.6) = 仅冷水机组本体能效，不是机房COP |

---

## 2. 实时报警 ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /intelligentAlarm/alarm/listRealAlarms` |
| **请求体** | `{"startTime":"2026-06-05 00:00:00","endTime":"2026-06-12 23:59:59","pageNum":1,"pageSize":10}` |
| **响应体** | `{"code":200, "message":"操作成功", "data": {"records":[], "total":0, "size":10, "current":1}}` |
| **字段映射** | `data.total` → total_alarms, `data.records` → alarms (list) |
| **跳转路由** | `/alarm/realtime` |
| **数据来源** | 自动抓取（报警管理页面加载） |
| **对应工具** | `fetch_active_alarms`（替换现有 Mock） |
| **备注** | startTime/endTime 需动态计算（最近 7 天）；当前无报警所以 records 为空 |

---

## 3. 碳排信息（光伏月发电 + 碳减排） ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/fucaOverviewScreen/carbonInfo` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "message":"操作成功", "data": {"photovoltaicMonth":27486.0, "carbonReduceMonth":16431.13, "carbonReduceMonthMoM":28.0, "photovoltaicMonthMoM":28.0, "carbonReduceTotal":179328.16}}` |
| **字段映射** | `data.photovoltaicMonth` → photovoltaic_month (kWh), `data.carbonReduceMonth` → carbon_reduce_month (kgCO₂e), `data.carbonReduceTotal` → carbon_reduce_total, `data.photovoltaicMonthMoM` → pv_mom (%), `data.carbonReduceMonthMoM` → carbon_mom (%) |
| **跳转路由** | `/coordination/energy`（光伏）/ `/fucaView`（碳排） |
| **数据来源** | 自动抓取（fucaView 首页加载） |
| **对应工具** | 新增 `fetch_carbon_info`（一个接口覆盖光伏 + 碳减排） |

---

## 4. 全厂用电量（今日 + 本月 + 趋势） ✅ 完整（Bonus）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /analysisWeb/energyAnalysis/cockpit/energyUsage` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "data": {"todayE":3168.0, "todayMoM":-62.5, "monthE":47795.0, "monthMoM":-65.5, "energyThisMonthList":[...], "energyLastMonthList":[...]}}` |
| **字段映射** | `data.todayE` → today_energy (kWh), `data.monthE` → month_energy (kWh), `data.todayMoM` → today_mom (%), `data.monthMoM` → month_mom (%) |
| **跳转路由** | `/analysis/consumption-panel` |
| **数据来源** | 自动抓取（首页加载） |
| **对应工具** | 新增 `fetch_energy_usage`（cockpit 版，与现有 v1/ECInfo 互补） |
| **备注** | 还返回每日用电趋势数组（energyThisMonthList / energyLastMonthList），可用于图表展示 |

---

## 5. 全厂设备用电排名（Top5） ✅ 完整（Bonus）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/energyMonitor/v1/deviceEnergyRankTop5Month` |
| **请求参数** | 无 |
| **响应体** | `{"code":200, "data": {"综合楼照明动力":12697.0, "园区储能电站":10560.0, "生产厂房照明动力":4669.0, "办公室顶楼电表":4594.2, "生产厂房生产用电":3783.0}}` |
| **字段映射** | `data` 为 `{设备名: 用电量(MWh)}` 的字典 |
| **跳转路由** | `/analysis/rank` |
| **数据来源** | 自动抓取（首页加载） |
| **对应工具** | 新增 `fetch_device_energy_rank` |

---

## 6. 机房设备能耗 ✅ 完整（Bonus）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /integrateMonitor/cockpit/roomEnergy` |
| **请求参数** | `deviceId=3602`, `deviceCode=KTXT-CWER-0001` |
| **响应体** | `{"code":200, "data": {"copInstant":"7.00", "copAvg":"7.00", "unitCopInstant":"9.80", "unitCopAvg":"9.60", "deviceEnergyList":[{"name":"冷水机组","value":2319.0,"prop":"69.5"}, ...]}}` |
| **字段映射** | `data.copInstant` → 机房瞬时COP, `data.copAvg` → 机房累计COP, `data.unitCopInstant` → 机组瞬时COP, `data.unitCopAvg` → 机组累计COP, `data.deviceEnergyList` → 设备能耗列表 |
| **跳转路由** | `/analysis/rank` |
| **数据来源** | 自动抓取（首页加载） |
| **对应工具** | 新增 `fetch_room_energy`（也可复用 fetch_cop_data，此接口同时返回 COP 和设备能耗） |
| **备注** | 此接口比 COP 接口更丰富，同时返回机房 COP 和各设备能耗占比 |

---

## 7. 环境参数（室外温度/湿度/湿球温度/焓值） ✅ 完整（Bonus）

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /integrateMonitor/chillerRoom/getValueByPointGroupNames` |
| **请求体** | `{"pointGroupNames": ["室外温度", "室外湿度", "室外湿球温度", "室外焓值"], "currentDeviceCode": "KTXT-CWER-0001"}` |
| **响应体** | `{"code":200, "data": {"室外湿球温度":"21.4", "室外温度":"30.3", "室外湿度":"45.5", "室外焓值":"62.3"}}` |
| **字段映射** | `data.室外温度` → outdoor_temp (°C), `data.室外湿度` → outdoor_humidity (%), `data.室外湿球温度` → wet_bulb_temp (°C), `data.室外焓值` → enthalpy (kJ/kg) |
| **跳转路由** | `/index/index` |
| **数据来源** | 自动抓取（首页加载） |
| **对应工具** | 新增 `fetch_environment_params` |
| **备注** | 与 COP 共用同一接口 URL，通过 pointGroupNames 区分 |
