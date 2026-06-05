# 福加监控网站页面导航全面分析 — EnerGraph 跳转路由对照

**分析日期**: 2026-06-05  
**网站**: https://aiot-fuca.com  
**框架**: Vue3 + Arco Design（Vue Router）  
**分析方法**: 从 Vue Router 提取全部注册路由 + 实际遍历 34 个页面提取内容  
**目标**: 为 Claude Code 提供完整的前后端对齐方案

---

## 一、页面遍历结果总览

### 1.1 遍历统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 成功加载 | 24 页 | 返回唯一页面内容 |
| 被重定向到 `/fucaView` | 10 页 | 需要项目/权限上下文，当前用户无权或功能未开放 |
| Vue Router 注册路由总数 | 120+ 条 | 含 demo/exception/system 等非业务路由 |

### 1.2 被重定向的 10 个页面（重要发现）

以下页面导航后被 Vue Router Guard 重定向到 `/fucaView`（项目概览页），说明这些功能需要特定的项目上下文或角色权限：

| 菜单项 | 原始路由 | 可能原因 |
|--------|---------|---------|
| 冷水机房 | `/integrated-monitor/conditioning-terminal` | 需要先选择项目/站点 |
| 办公楼空调 | `/integrated-monitor/air-device-monitor` | 同上 |
| 生产厂房空调 | `/integrated-monitor/production-device-monitor` | 同上 |
| 健康诊断 | `/smart-maintenance/health` | 权限或项目未选择 |
| 能源报告 | `/report-center/energy` | 功能可能未完全实现 |
| 驾驶舱 | `/cockpit` | 已合并到 `/fucaView` |
| 碳排总览 | `/carbon/carbon-overview` | 碳排模块可能需要单独配置 |
| 碳排明细 | `/carbon/carbon-detail` | 同上 |
| 碳排分布 | `/carbon/carbon-distribution` | 同上 |
| AI助手 | `/ai/assistant` | AI 模块可能需要单独启用 |
| AI模型 | `/ai/model` | 同上 |

**对 Agent 跳转的影响**：Agent 下发这些路由的跳转信号后，前端 `router.push()` 会被 Guard 拦截并重定向到 `/fucaView`，用户看到的不是预期页面。需要在跳转前判断用户是否有权访问，或在 Prompt 中标注这些路由为"条件可用"。

---

## 二、成功加载的 24 个页面详细内容

### 2.1 首页 `/index/index`

**内容结构**：
- **顶部统计卡片**：累计运行天数(338天)、累计用能(1341.6MWh)、累计制冷量(208.0MWh)、累计减排(51760kgCO₂e)、本月报警数(0)
- **用能情况**：本月设备能耗排名（综合楼照明动力 4892kWh、储能电站 4525kWh...）、今日/本月总用电量及环比
- **用电趋势图**：本月 vs 上月折线图
- **机房能效监控**：冷水机房#1 选择器、设备电能占比（冷水机组66.2%、冷却水泵17.5%...）、瞬时/累计COP、能效趋势图
- **环境参数**：室外温度、湿度、湿球温度、焓值
- **能效日历**：月度日历视图，每日显示 COP 值
- **现场画面**：摄像头轮播（2/3 页）

### 2.2 综合监控 > 能源监控 `/integrated-monitor/energy-monitor`

**内容结构**：
- **工作台 > 综合监控 > 能源监控**（面包屑导航）
- **顶部统计**：今日总能耗(kWh) + 环比、本月总能耗(kWh) + 环比
- **总用能趋势图**：电(kWh)，今日 vs 昨日

### 2.3 光储协同 > 实时能量 `/coordination/energy`

**内容结构**：
- **工作台 > 光储协同 > 实时能量**
- **筛选条件**：日期选择 + 查询/重置按钮
- **能量流向图**：桑基图展示能量流转关系
- **实时功率图**：2026-06-05 实时功率曲线（kW）
  - 电网交互、光伏发电、储能、全厂负荷
- **供需结构图**：当日各能源供需（kWh）
  - 电网交互(买电)、光伏发电、储能充/放、全厂负荷、电网交互(卖电)

### 2.4 用能分析 > 能耗分析 `/analysis/consumption-panel`

**内容结构**：
- **工作台 > 用能分析 > 能耗分析**
- **筛选条件**：区域（福加江北工厂）、设备（全部设备）、能耗类型（电）、时间（日/月/年）、查询/重置/导出
- **统计卡片**：能耗总计(kWh) + 同比/环比、最大值、最小值、平均值
- **能耗趋势图**：用电量折线图
- **设备能耗占比**：饼图/柱图

### 2.5 用能分析 > 峰平谷分析 `/analysis/peak-flat-valley`

**内容结构**：
- **工作台 > 用能分析 > 峰平谷分析**
- **筛选条件**：区域、设备、时间（周/月）、查询/重置/导出
- **尖峰平谷用能对比图**：堆叠柱图（尖/峰/平/谷）
- **电费图**：电费柱图
- **用电总览**：
  - 电量总计、电费总计
  - 尖时段电量/电费、峰1时段电量/电费...
  - 电量占比、电费占比

### 2.6 用能分析 > 能效日历 `/analysis/calendar`

**内容结构**：
- **工作台 > 用能分析 > 能效日历**
- **选择器**：年月选择、冷水机房选择
- **月历视图**：每日显示 COP 值 + 日制冷量(C) + 日耗电量(P)
- **能效评价**：COP 仪表盘（当前:6.4，急需改善/一般/良好/优秀）
- **电量统计**：电量(kWh) + 电费(元)
- **冷量统计**：冷量(kWh) + 单价(元/kWh)
- **分项能耗占比**：饼图

### 2.7 用能分析 > 能效查询 `/analysis/query`

**内容结构**：
- **工作台 > 用能分析 > 能效查询**
- **筛选条件**：参数类型（平均SCOP）、设备点位（冷冻机房-水系统平均SCOP）、时间（日/月/年）、查询/重置/导出
- **能效参数展示**：历史累计值、当日平均值、同比/环比均值
- **能效趋势图**

### 2.8 用能分析 > 能耗排名 `/analysis/rank`

**内容结构**：
- **工作台 > 用能分析 > 能耗排名**
- **筛选条件**：排名方式（按设备/按区域）、冷水机房、能耗类型（电/水/气）、时间（日/月/年）、查询/重置
- **排名表格**：排名、排名对象、能耗(kWh)、同比能耗值、同比变化百分比
- **示例数据**：冷水机组#1 68.4kWh、冷却水泵#1 8.1kWh、冷水泵#1 6kWh、冷却塔#1 0.8kWh...

### 2.9 用能分析 > 负荷预测 `/analysis/load-forecast`

**内容结构**：
- **工作台 > 用能分析 > 负荷预测**
- **冷负荷预测图**：实际负荷 vs 预测负荷 + 天气状态图标
- **今日统计**：平均偏差、评价等级（一级）
- **当前/下一小时预测**：当前负荷、预测负荷
- **昨日冷负荷预测**：昨日平均偏差 + 实际/预测曲线
- **上周冷负荷预测**：上周平均偏差 + 实际/预测曲线

### 2.10 智慧运维 > 设备运行 `/smart-maintenance/equipment-operation`

**内容结构**：
- **工作台 > 智慧运维 > 设备运行**
- **左侧设备树**：
  - 冷水机房 > 冷水机组 > #1/#2
  - 冷水泵 > #1/#2
  - 冷却水泵 > #1/#2
  - 冷却塔 > #1/#2
- **右侧设备详情（以冷水机组#1为例）**：
  - **设备信息**：磁悬浮、关机状态
    - 设计输入功率 121.7kW、设计制冷量 800kW、设计工况COP 6.574
    - 名义工况COP 5.825、名义工况IPLV(GB) 9.641
    - 冷冻水设计工况 10℃/17℃、冷却水设计工况 31℃/36℃
    - 安装日期 2025年01月01日
  - **运行数据（Tab切换：整体/蒸发器/冷凝器）**：
    - 整体：机组实时功率 0.0kW、实时负载 0.1%、累计电能 21248.8kWh、累计运行时间 680.0h
    - 蒸发器：进水温度 19.5℃、出水温度 15.3℃
    - 冷凝器：进水温度 22.5℃、出水温度 23.1℃
  - **实时报警**：(0) 暂无报警
  - **能耗趋势图**：切换 今日/本月/今年
  - **进出水趋势图**

### 2.11 智慧运维 > 工单管理 `/smart-maintenance/work-order-management`

**内容结构**：
- **工作台 > 智慧运维 > 设备运行**（侧边栏高亮）
- **Tab切换**：维修工单 / 保养工单 / 巡检工单
- **筛选条件**：全部来源、全部状态、查询/重置
- **操作按钮**：新增维修单
- **表格**：工单编号、工单名称、工单来源、创建时间、工单状态、负责人、操作

### 2.12 智慧运维 > 任务管理 `/smart-maintenance/task-management`

**内容结构**：
- **工作台 > 智慧运维 > 任务管理**
- **Tab切换**：巡检任务 / 保养任务
- **操作按钮**：新建巡检任务
- **任务卡片**：巡检周期（每周一 08:05）、下次执行、最近执行时间、状态（已派单）

### 2.13 智能算法 > 主动寻优 `/blockchain/optimization`

**内容结构**：
- **工作台 > 智能算法 > 主动寻优**
- **当前工况**：室外温度 26.7℃、室外湿度 52.1%、机房瞬时制冷量/功率/COP
- **寻优过程图**：COP 变化曲线（优秀/出色/良好/一般/欠佳等级）
- **最优点参数表**
- **寻优下发记录**
- **能效评价(COP)图**
- **寻优算法模型**：已执行天数、迭代次数、本轮寻优能效提升百分比
  - 调控前/后对比
  - 节能贡献率：冷水机组、冷水泵、冷却泵、冷却塔分别贡献
- **机房能效能耗趋势**：COP + 能耗双轴图
- **机房冷量曲线**
- **机组COP趋势**
- **设备运行状态**：8台设备的开机/关机状态

### 2.14 智能算法 > 数据公信 `/blockchain/data-monitor`

**内容结构**：
- **工作台 > 智能算法 > 数据公信**
- **子Tab**：平台接入数据
- **筛选条件**：日期选择、查询/重置
- **数据表格**：时间、点位名称、点位值

### 2.15 报告报表 > 自定义报表 `/report-center/custom`

**内容结构**：
- **工作台 > 报告报表 > 自定义报表**
- **筛选条件**：时间范围、查询时间间隔(S)、查询/重置/导出
- **报表展示区**：已保存报表（如"未命名报表_2026-05-19"）

### 2.16 报告报表 > 报表管理 `/report-center/manage`

**内容结构**：
- **工作台 > 报告报表 > 报表管理**
- **筛选条件**：报表类型、报表来源、日期、查询/重置
- **批量操作**：批量删除、批量下载、上传
- **表格**：序号、名称、报表类型、来源、生成时间、操作
- **示例数据**：
  - 福加智能05月运行统计报表.xlsx（运维报表，系统生成）
  - 福加智能05月设备用能统计报表.xlsx（用能报表，系统生成）
  - 福加智能-全部设备-2026-05-01~2026-05-31_尖峰平谷明细表.xlsx
  - ...共 26 项

### 2.17 报警管理 > 实时报警 `/alarm/realtime`

**内容结构**：
- **工作台 > 报警管理 > 实时报警**
- **筛选条件**：日期、报警区域、报警类型、报警等级、查询/重置
- **表格**：报警时间、报警等级、报警区域、报警对象、报警信息、处理建议、操作

### 2.18 报警管理 > 历史报警 `/alarm/history`

**内容结构**：
- **工作台 > 报警管理 > 历史报警**
- **筛选条件**：日期、报警区域、报警类型、报警等级、查询/重置
- **表格**：报警时间、**恢复时间**、报警等级、报警区域、报警对象、报警信息、处理建议、操作

### 2.19 数据大屏 `/data-overview/home`（数据总览）

**内容结构**：
- **全厂能耗监控**：今日内能耗趋势
- **分区域能耗**：综合楼、成品储运部、其他（日/月/年切换）
- **区域能耗详情**：测试中心、制造厂区、思茂特生产、综合楼办公、展厅、食堂
- **光伏直驱发电**：今日/累计发电量、主机用电量、累计碳减排、当前功率、背板温度、环境风速/温度/湿度
- **空调能耗监控**：今日/昨日能耗对比
- **关键设备开动率**

### 2.20 数据大屏 `/data-overview/screen`（综合大屏）

**内容结构**：
- 绿电占比 74.36%
- 月节约标准煤 22,641.5kg
- 月CO₂减排 43,849.1kg
- 全厂月用电量 90,231.0kWh
- 光伏月累计发电量 75,102.5kWh
- 风力月累计发电量 369.3kWh
- 储能月累计放电量 7,557.3kWh

### 2.21 数据大屏 `/data-overview/deviceMonitor`（设备监控大屏）

**内容结构**：
- **楼层选择**：综合楼东区/西区、1F/2F/3F
- **统计卡片**：全厂空调总数 320台、多联机 27台、室内机 293台、今日运行 32台/11%
- **综合楼空调用电量统计**：东区 91kWh、西区 113kWh
- **空调设备状态监控**：各楼层开启率、运行/关机数
- **空调用电量趋势分析**：日/月/年切换
- **近7日空调开启率趋势**

### 2.22 数据大屏 `/data-overview/pvPower`（光伏大屏）

**内容结构**：
- **统计卡片**：当日主机耗电量/市电量/光伏发电量 + 昨日对比 + 同比
- **全年累计**：光伏发电量 9,590kWh、CO₂减排量 8吨标煤
- **设备状态监控**：总数 10台、运行 4台、关机 6台
- **光伏发电系统能耗统计**：主机耗电量/市电量/光伏发电量（日/月/年）
- **设备用电量统计**：磁悬浮主机 21.19kWh、冷却水泵/冷水泵/模块机/冷却塔
- **光伏发电系统能耗趋势分析**
- **室外环境参数**：背板温度 41.6℃、环境湿度 6.4%、露点温度 19.8℃、风速 1.8m/s、环境温度 27.1℃

### 2.23 数据大屏 `/data-overview/energy`（能源大屏 - 储能系统）

**内容结构**：
- **堆系统拓扑图**：市电 → 变压器 → 防逆流电表 → 计量电表 → 5个储能堆
- **每个堆状态**：运行中、SOC(43%)、放电状态、温度 27.7℃、电压 826.7V、电流 -154.8A、功率 -127.9kW
- **当日统计**：充电量 1306.25kWh、放电量 732.57kWh、功率 -639.68kW
- **负荷曲线**：今日内
- **用电分析**：今日内
- **储能系统状态控制**：集控开关、并离网状态（并网/离网）、控制源（本地/远程）、控制模式（总功率/子系统）、计划自动、故障复归、立即复归

### 2.24 项目概览 `/fucaView`（被重定向页面的目标）

**内容结构**：
- **项目概况**：光伏装机容量 497kWp、充电桩装机容量 202kW、储能装机容量 783kWh、变压器容量 2000kVA/10kV
- **碳排信息**：绿电占比 51.0%、本月光伏发电量 9899.0kWh、本月碳减排 5917.6kgCO₂e
- **光伏系统**：发电量/收益（含详情入口）
- **储能系统**：充电/放电/收益（含详情入口）
- **用电统计**：今日/本月用电 + 环比
- **用电占比**：总电能 25021.6kWh（实验室 1.2%、生产制造 7.4%、空调系统 22.8%、其他 68.6%）
- **空调能效**：机房累计 7.00、机房瞬时 0.00、机组累计 9.60、机组瞬时 0.00
- **充电桩**：数量 8个、累计充电次数 858次、累计充电收益 15617.6元、累计充电量 15617.5kWh
- **月度能耗趋势图**：综合楼/生产厂房/办公楼累计

---

## 三、现有代码跳转链路深度分析

### 3.1 跳转链路完整流程

```
前端 POST /stream
    ├── body: { user_input: "冷水机房COP多少", page_context: { current_route: "/index/index", site_id: "SH-01" } }
    │
    ▼
cognitive_parser_node (nodes.py:93)
    ├── 读取 page_context → 注入 system prompt（当前路由 + site_id）
    ├── LLM 分析意图 → 输出 tool_calls: [fetch_cop_data, navigate_to_page]
    │
    ▼
v3_engine_router_node (nodes.py:149)
    ├── 执行 tool_calls:
    │   ├── fetch_cop_data(site_id="SH-01") → COPData dict
    │   └── navigate_to_page(route="/chiller-room") → UIAction dict
    ├── 写入 AgentState 字段（_TOOL_FIELD_MAP）
    ├── Skill 统一调度:
    │   └── UIRouterSkill.execute(tool_results, state)
    │       ├── 优先: LLM 显式调用 navigate_to_page → 采用其 route
    │       └── 兜底: _TOOL_ROUTE_MAP 自动推断 → fetch_cop_data → /chiller-room
    │       └── 返回 { pending_actions: [UIAction] }
    │
    ▼
SSE _sse_generator (api.py:86)
    ├── on_chain_end → 检测 output.pending_actions
    ├── yield "event: action\ndata: { type: navigate, route: /chiller-room, params: {...} }"
    │
    ▼
前端 Vue3
    ├── es.addEventListener('action', ...)
    ├── router.push(data.route, { query: data.params })
    └── 页面跳转
```

### 3.2 链路中的 5 个关键问题

#### 问题 1：Prompt 路由表全是假路径
- **位置**：`prompts.yaml` → `action_agent_nav_hint`
- **现状**：6 条路由（`/`, `/chiller-room`, `/energy-monitor`, `/pv-storage`, `/alarms`, `/settings`）全部是虚构的
- **影响**：LLM 按 Prompt 指示调用 `navigate_to_page("/chiller-room")`，前端 `router.push("/chiller-room")` → 404 或重定向
- **修复**：替换为真实路由

#### 问题 2：`_TOOL_ROUTE_MAP` 自动推断也是假路径
- **位置**：`ui_router_skill.py:30`
- **现状**：`fetch_cop_data → /chiller-room`（假），应为 `/integrated-monitor/conditioning-terminal` 或 `/smart-maintenance/equipment-operation`
- **影响**：即使 LLM 没显式调用 `navigate_to_page`，兜底推断也会跳到错误页面
- **修复**：替换为真实路由

#### 问题 3：`cognitive_parser` 不知道完整路由表
- **位置**：`nodes.py:107-115`
- **现状**：只注入 `current_route` 和 `site_id`，LLM 不知道哪些路由可跳转
- **影响**：LLM 完全依赖 `action_agent_nav_hint` Prompt 中硬编码的 6 条路由
- **改进建议**：可以在 `page_context` 中追加可用路由列表，或通过 `action_agent_nav_hint` Prompt 扩展

#### 问题 4：权限/上下文感知的缺失
- **现状**：Agent 不知道用户当前是否有权限访问某些页面（如冷水机房需要先选择项目）
- **影响**：Agent 下发 `/integrated-monitor/conditioning-terminal` 跳转后，前端被 Guard 拦截重定向到 `/fucaView`
- **改进建议**：
  - `page_context` 增加 `project_id` / `accessible_routes` 字段
  - 或在 Prompt 中标注哪些路由需要前置条件

#### 问题 5：UIAction 只支持 `navigate` 类型
- **位置**：`action_agent.py:36`
- **现状**：`type` 字段目前只有 `navigate` 一种
- **潜在需求**：
  - `highlight`：高亮某个数据卡片（如"COP 偏低，请注意" → 高亮 COP 数值）
  - `open_panel`：打开侧边面板（如展开设备详情）
  - `set_filter`：设置页面筛选条件（如"看看今天的报警" → 跳转到报警页并自动设置日期为今天）
  - `scroll_to`：滚动到页面特定区域
- **建议**：当前不需要实现，但 schema 设计已预留了 `meta` 字段，可后续扩展

---

## 四、前后端对齐方案可行性评估

### 4.1 通过 Prompt + 代码修改来对齐（可行）

**核心思路**：Agent 后端不维护完整路由表，而是在 Prompt 中告知 LLM 可用路由，LLM 自行决策跳转目标。

**优势**：
- 改动量小（Prompt 替换 + `_TOOL_ROUTE_MAP` 修正）
- 不需要前端配合
- LLM 可以灵活匹配用户意图到路由

**风险**：
- Prompt 中的路由表需要人工与前端同步维护
- LLM 可能生成不存在的路由（幻觉）
- 新增页面时需要同时更新 Prompt 和代码

**评估**：**短期内可行**，适合当前阶段（Demo → 联调）

### 4.2 通过 API 端点提供路由表（推荐中期方案）

**核心思路**：新增 `GET /nav-routes` 端点，返回当前可用的路由表（可配置化），前端和 Agent 共用同一数据源。

```
GET /nav-routes
→ {
    routes: [
      { path: "/index/index", name: "首页", category: "overview", keywords: ["首页","总览"] },
      { path: "/integrated-monitor/energy-monitor", name: "能源监控", category: "monitor", keywords: ["能源","监控"] },
      ...
    ]
  }
```

**优势**：
- 路由表单一数据源，前后端一致
- 新增页面只改配置文件
- 可按用户角色过滤可用路由

**风险**：
- 需要开发 API 端点和配置文件
- Agent 需要在每次对话时加载路由表

**评估**：**中期推荐**，适合联调阶段

### 4.3 前端注入路由表到 Agent（最完备方案）

**核心思路**：前端在每次 SSE 请求时，将当前可用路由表注入到 `page_context` 中。

```json
{
  "user_input": "看看COP",
  "page_context": {
    "current_route": "/index/index",
    "site_id": "SH-01",
    "project_id": "FJ-01",
    "accessible_routes": [
      { "path": "/integrated-monitor/conditioning-terminal", "name": "冷水机房" },
      ...
    ]
  }
}
```

**优势**：
- 路由表实时反映用户权限和项目上下文
- 前端是路由表的权威来源
- Agent 永远使用最新路由

**风险**：
- 需要前端团队配合修改请求体
- 路由表可能很大（50+ 条），增加请求体积

**评估**：**长期推荐**，适合生产环境

---

## 五、给 Claude Code 的实施方案

### 5.1 必须修改的文件（按优先级）

#### 优先级 1：`src/config/prompts.yaml` — 替换路由表

将 `action_agent_nav_hint` 的 `## 可用路由表` 部分替换为以下真实路由（按场景分组）：

```yaml
action_agent_nav_hint:
  system: |
    你是青山 V3 多模态调度 Agent 的 UI 导航控制器。你可以调用监控数据工具获取实时数据，
    并在适当时候下发页面跳转信号，将用户导航到最相关的监控页面。

    ## 可用路由表（福加能碳管理平台真实路由）

    ### 总览类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/index/index` | 首页 | 综合概览（用能排名、COP、环境参数、能效日历、现场画面） |
    | `/fucaView` | 项目概览 | 项目概况、碳排、光伏、储能、充电桩、用电占比、空调能效 |

    ### 综合监控类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/integrated-monitor/energy-monitor` | 能源监控 | 今日/本月总能耗、用能趋势 |

    ### 光储协同类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/coordination/energy` | 光储实时能量 | 能量流向桑基图、实时功率、供需结构 |

    ### 用能分析类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/analysis/consumption-panel` | 能耗分析 | 区域/设备/类型/时间筛选的能耗趋势和设备占比 |
    | `/analysis/peak-flat-valley` | 峰平谷分析 | 尖峰平谷电量对比、电费分析 |
    | `/analysis/calendar` | 能效日历 | 月度COP日历、能效评价 |
    | `/analysis/query` | 能效查询 | SCOP等能效参数查询和趋势 |
    | `/analysis/rank` | 能耗排名 | 设备/区域能耗排名和同比 |
    | `/analysis/load-forecast` | 负荷预测 | AI冷负荷预测（今日/昨日/上周） |

    ### 智慧运维类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/smart-maintenance/equipment-operation` | 设备运行 | 设备树、设备详情（信息/运行数据/蒸发器/冷凝器/报警/趋势） |
    | `/smart-maintenance/work-order-management` | 工单管理 | 维修/保养/巡检工单列表 |
    | `/smart-maintenance/task-management` | 任务管理 | 巡检/保养任务管理 |

    ### 智能算法类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/blockchain/optimization` | 主动寻优 | RL寻优过程、最优点参数、节能贡献率、设备状态 |
    | `/blockchain/data-monitor` | 数据公信 | 区块链上链数据查询 |

    ### 报告报表类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/report-center/custom` | 自定义报表 | 自定义时间段和间隔的报表 |
    | `/report-center/manage` | 报表管理 | 系统生成的运维/用能报表列表（可下载） |

    ### 报警类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/alarm/realtime` | 实时报警 | 当前活跃报警列表（可按区域/类型/等级筛选） |
    | `/alarm/history` | 历史报警 | 历史报警记录（含恢复时间） |

    ### 数据大屏类
    | 路由 | 页面名称 | 适用场景 |
    |------|---------|---------|
    | `/data-overview/home` | 数据总览 | 全厂能耗监控、分区域能耗、光伏直驱、空调能耗 |
    | `/data-overview/screen` | 综合大屏 | 绿电占比、碳减排、光伏/风力/储能月累计 |
    | `/data-overview/deviceMonitor` | 设备监控大屏 | 综合楼空调设备按楼层状态监控 |
    | `/data-overview/pvPower` | 光伏大屏 | 光伏发电量/收益、设备状态、环境参数 |
    | `/data-overview/energy` | 能源大屏 | 储能系统拓扑、5堆SOC/充放电、负荷曲线 |

    ## 跳转时机

    1. 用户查询 COP、冷机状态、水温、冷水机房 → 调用 fetch_cop_data → 跳转到 `/smart-maintenance/equipment-operation`
    2. 用户查询能耗、用电量、电费 → 调用 fetch_energy_summary → 跳转到 `/analysis/consumption-panel`
    3. 用户查询光伏、储能、光储 → 跳转到 `/coordination/energy`
    4. 用户查询报警、故障 → 调用 fetch_active_alarms → 跳转到 `/alarm/realtime`
    5. 用户查询峰谷电价、用电时段 → 跳转到 `/analysis/peak-flat-valley`
    6. 用户查询设备排名、最耗电设备 → 跳转到 `/analysis/rank`
    7. 用户查询负荷预测 → 跳转到 `/analysis/load-forecast`
    8. 用户查询设备运行状态、设备参数 → 跳转到 `/smart-maintenance/equipment-operation`
    9. 用户查询每日COP、能效日历 → 跳转到 `/analysis/calendar`
    10. 用户查询 SCOP、能效参数 → 跳转到 `/analysis/query`
    11. 用户要求看报表、下载报表 → 跳转到 `/report-center/manage`
    12. 用户要求看大屏 → 跳转到 `/data-overview/screen`
    13. 用户查询寻优效果、AI优化 → 跳转到 `/blockchain/optimization`
    14. 用户查询工单、运维任务 → 跳转到 `/smart-maintenance/work-order-management`
    15. 用户查询历史报警 → 跳转到 `/alarm/history`
    16. 用户查询碳减排、绿电占比 → 跳转到 `/fucaView`

    ## 原则

    - 跳转是可选的，仅当用户意图明确指向某个监控页面时才下发跳转信号
    - 一般性问答（如"COP 是什么"）不需要跳转，只回答即可
    - 一次对话最多下发一个跳转信号
    - 获取数据后先给出文字总结，再下发跳转信号
    - 路由参数 params 中传入当前上下文中的 site_id 等信息
    - 当不确定跳转到哪个页面时，优先跳转到 `/index/index`（首页）
```

#### 优先级 2：`src/skills/ui_router_skill.py` — 修正 `_TOOL_ROUTE_MAP`

```python
_TOOL_ROUTE_MAP: Dict[str, str] = {
    "fetch_cop_data": "/smart-maintenance/equipment-operation",
    "fetch_energy_summary": "/analysis/consumption-panel",
    "fetch_active_alarms": "/alarm/realtime",
}
```

#### 优先级 3：`src/tools/navigate_to_page.py` — 更新 docstring

```python
def navigate_to_page(route: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """下发页面跳转信号，将 UIAction 写入 AgentState.pending_actions。

    Args:
        route: 目标路由（如 /integrated-monitor/energy-monitor,
               /analysis/consumption-panel, /alarm/realtime）
        params: 路由参数（如 {"site_id": "SH-01", "chiller_id": "CH-01"}）

    Returns:
        UIAction 的 dict 表示
    """
```

#### 优先级 4（可选）：新建 `src/config/nav_routes.yaml` — 路由配置化

```yaml
# 福加能碳管理平台路由配置
# 前端与 Agent 共用，保持单一数据源

routes:
  overview:
    - path: /index/index
      name: 首页
      keywords: [首页, 总览, 概览, dashboard]
    - path: /fucaView
      name: 项目概览
      keywords: [项目, 概况, 碳减排, 绿电占比]

  monitoring:
    - path: /integrated-monitor/energy-monitor
      name: 能源监控
      keywords: [能源监控, 总能耗, 用能趋势]

  coordination:
    - path: /coordination/energy
      name: 光储实时能量
      keywords: [光伏, 储能, 能量流, 光储]
      tools: [fetch_energy_summary]

  analysis:
    - path: /analysis/consumption-panel
      name: 能耗分析
      keywords: [能耗, 用电, 能耗趋势, 设备占比]
      tools: [fetch_energy_summary]
    - path: /analysis/peak-flat-valley
      name: 峰平谷分析
      keywords: [峰谷, 电价, 尖峰平谷]
    - path: /analysis/calendar
      name: 能效日历
      keywords: [能效日历, COP日历, 每日能效]
    - path: /analysis/query
      name: 能效查询
      keywords: [SCOP, 能效参数, 能效查询]
    - path: /analysis/rank
      name: 能耗排名
      keywords: [排名, 最耗电, 能耗排名]
    - path: /analysis/load-forecast
      name: 负荷预测
      keywords: [预测, 负荷预测, 冷负荷]

  maintenance:
    - path: /smart-maintenance/equipment-operation
      name: 设备运行
      keywords: [设备, 运行, 冷水机组, 水泵, 冷却塔, 设备参数]
      tools: [fetch_cop_data]
    - path: /smart-maintenance/work-order-management
      name: 工单管理
      keywords: [工单, 维修, 保养, 巡检]
    - path: /smart-maintenance/task-management
      name: 任务管理
      keywords: [任务, 巡检任务, 保养任务]

  algorithm:
    - path: /blockchain/optimization
      name: 主动寻优
      keywords: [寻优, AI优化, 节能, 能效提升]
    - path: /blockchain/data-monitor
      name: 数据公信
      keywords: [区块链, 数据上链, 数据公信]

  report:
    - path: /report-center/custom
      name: 自定义报表
      keywords: [自定义报表]
    - path: /report-center/manage
      name: 报表管理
      keywords: [报表, 下载报表, 运维报表]

  alarm:
    - path: /alarm/realtime
      name: 实时报警
      keywords: [报警, 故障, 实时报警]
      tools: [fetch_active_alarms]
    - path: /alarm/history
      name: 历史报警
      keywords: [历史报警, 报警记录]

  screen:
    - path: /data-overview/home
      name: 数据总览
      keywords: [数据总览, 全厂监控]
    - path: /data-overview/screen
      name: 综合大屏
      keywords: [大屏, 综合大屏]
    - path: /data-overview/deviceMonitor
      name: 设备监控大屏
      keywords: [设备大屏, 空调监控]
    - path: /data-overview/pvPower
      name: 光伏大屏
      keywords: [光伏大屏, 发电大屏]
    - path: /data-overview/energy
      name: 能源大屏
      keywords: [储能大屏, 能源大屏]

# 需要前置条件（选择项目）的路由
conditional_routes:
  - path: /integrated-monitor/conditioning-terminal
    name: 冷水机房
    requires: project_selected
  - path: /integrated-monitor/air-device-monitor
    name: 空调设备监控
    requires: project_selected
  - path: /smart-maintenance/health
    name: 健康诊断
    requires: project_selected
```

### 5.2 注意事项

1. **不要修改 `navigate_to_page` 工具的函数签名和逻辑**，它的机制是正确的（纯状态变更，写入 pending_actions），只需要更新 Prompt 和 docstring 中的示例路径

2. **`_TOOL_ROUTE_MAP` 中的 `fetch_cop_data` 映射**：有两个候选路由
   - `/smart-maintenance/equipment-operation`：设备运行页面，有完整的设备树和详情（推荐）
   - `/integrated-monitor/conditioning-terminal`：冷水机房综合监控（但当前需要项目上下文，会被重定向）
   - 建议选择 `/smart-maintenance/equipment-operation`，因为该页面已成功加载且包含设备详情

3. **`cognitive_parser` 的 system prompt 中也需要补充**：当前 `cognitive_parser` 的 Prompt 只提到了工具调用指引，没有提到页面跳转。建议在 `cognitive_parser` Prompt 中增加一行：
   ```
   - 当用户查询特定页面数据时，除了调用数据工具，还可以调用 navigate_to_page 引导用户到对应监控页面
   ```

4. **测试文件 `test_action_agent.py` 需要同步更新**：现有测试中 mock 的路由路径也需要改为真实路径

---

## 六、遗漏补充（相比第一版文档）

### 6.1 新增发现的页面

| 页面 | 路由 | 来源 | 说明 |
|------|------|------|------|
| 项目概览 | `/fucaView` | 遍历发现 | 10个路由重定向到此页面，是重要的 fallback 页面 |
| 数据总览大屏 | `/data-overview/home` | Vue Router | 不在侧边栏菜单，但有独立路由 |
| 综合大屏 | `/data-overview/screen` | Vue Router | 同上 |
| 设备监控大屏 | `/data-overview/deviceMonitor` | Vue Router | 同上 |
| 光伏大屏 | `/data-overview/pvPower` | Vue Router | 同上 |
| 能源大屏 | `/data-overview/energy` | Vue Router | 储能系统拓扑和状态 |
| TICA光伏概览 | `/tica-overview/photovoltaic` | Vue Router | TICA 定制页面 |
| TICA风电 | `/tica-overview/wind-power` | Vue Router | 同上 |
| TICA储能 | `/tica-overview/energy-storage` | Vue Router | 同上 |
| TICA高效机房 | `/tica-overview/efficient-room` | Vue Router | 同上 |
| TICA充电桩 | `/tica-overview/charge-piles` | Vue Router | 同上 |
| 地铁站首页 | `/metroHome` | Vue Router | 地铁项目专用 |
| 轻量诊断箱 | `/diagnostic-box/show-page` | Vue Router | 诊断功能 |

### 6.2 侧边栏结构修正

第一版文档中"数据公信"被标记为"智能算法"的子菜单，实际遍历发现侧边栏的层级关系如下：

```
智能算法
├── 主动寻优        (叶子节点)
├── 数据公信        (可展开的子分组)
│   ├── 区块链上链数据
│   └── 平台接入数据
└── 负荷预测        (叶子节点)
```

### 6.3 每个页面的筛选条件/控件详细记录

已在第二节中为每个页面详细列出了筛选条件、Tab 切换、图表类型等内容，供前端对齐和 Prompt 优化参考。

---

*本文档供 Claude Code 实施参考，建议按第五节的优先级顺序逐步修改。*
