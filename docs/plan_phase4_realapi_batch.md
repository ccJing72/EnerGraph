# Phase 4.2 — 批量对接福加真实监控 API

> **目标**: 通过半自动化方式批量对接福加平台的监控数据接口，将所有 Mock 工具替换为真实 API 调用

---

## 背景

**当前状态**（Phase 4.1 完成）:
- ✅ `fetch_energy_summary` 已接入真实 API (`/analysisWeb/energyAnalysis/v1/ECInfo`)
- ❌ `fetch_cop_data`（设备 COP）仍为 Mock
- ❌ `fetch_active_alarms`（实时报警）仍为 Mock
- ❌ 其他监控数据（峰平谷、负荷预测、设备排名等）未实现

**目标**: 根据同事提供的接口清单，批量完成真实 API 对接，确保 Agent 能正确调用所有监控数据并生成准确的页面跳转建议。

---

## 方案设计

### 核心思路

用户（魏博源）提出的方案：
1. 同事扩充接口清单表格（关键词 | 接口 URL | 跳转页面）
2. 使用 Chrome MCP 工具自动打开福加页面，抓取网络请求（Request Payload + Response）
3. 整理成标准化表格（接口 URL + 请求体结构 + 响应体结构 + 备注）
4. 根据表格批量更新代码（`java_backend.py` + `ui_router_skill.py` + `site_mapping.yaml`）

**评估**: ✅ **方案可行**，但需分阶段执行并明确细节。

### 优化建议

#### 1. 分阶段验证（避免一次性抓取失败）
- **Phase 4.2.1**: 先抓取 2-3 个高优先级接口（COP、报警），验证自动化方案可行性
- **Phase 4.2.2**: 批量抓取剩余接口（峰平谷、负荷预测、设备排名等）
- **Phase 4.2.3**: 代码实现 + 测试 + 文档更新

#### 2. 明确抓取前提条件
- 浏览器需已登录福加平台（`https://aiot-fuca.com`）
- 每个接口需明确：页面 URL + 触发数据请求的操作步骤（点击、筛选、日期选择等）
- 有些接口可能需要特定权限或参数才能触发

#### 3. 数据验证机制
- 自动化抓取后，需人工确认：
  - 请求参数是否完整（是否有隐藏的必填字段）
  - 响应结构是否稳定（不同站点/时间是否返回格式一致）
  - 错误处理逻辑（接口返回 4xx/5xx 时如何处理）

---

## 执行计划

### Task 0: 路由配置解耦（基础设施优化）⚠️ **前置任务**

**背景**: 当前路由信息散落在 3 个地方（`ui_router_skill.py`、`app.py`、`prompts.yaml`），前端改路由需要同步改 3 处，违反 DRY 原则且容易出现不一致。

**目标**: 将路由配置统一到 `config/routes.yaml`，Agent 和前端动态读取，实现单点配置。

**改动清单**:

#### 0.1 创建 `config/routes.yaml`

结构设计：

```yaml
routes:
  - path: "/analysis/consumption-panel"
    name: "能耗分析面板"
    keywords: ["能耗", "用电量", "电费"]
    tools: ["fetch_energy_summary"]
    category: "用能分析"
    description: "区域/设备/类型/时间筛选的能耗趋势和设备占比"
    
  - path: "/smart-maintenance/equipment-operation"
    name: "设备运行监控"
    keywords: ["COP", "能效", "冷水机组", "冷机"]
    tools: ["fetch_cop_data"]
    category: "智慧运维"
    description: "设备树、设备详情（信息/运行数据/蒸发器/冷凝器/报警/趋势）"
    
  - path: "/alarm/realtime"
    name: "实时报警"
    keywords: ["报警", "故障", "告警"]
    tools: ["fetch_active_alarms"]
    category: "报警"
    description: "当前活跃报警列表（可按区域/类型/等级筛选）"
  
  # ... 其余 31 个路由
```

#### 0.2 更新 `src/config/settings.py`

新增路由加载逻辑（仿照现有 `prompts` 加载）：

```python
@property
def routes(self) -> Dict[str, Any]:
    """加载路由配置"""
    if not hasattr(self, "_routes"):
        routes_path = Path(__file__).parent.parent.parent / "config" / "routes.yaml"
        with open(routes_path, "r", encoding="utf-8") as f:
            self._routes = yaml.safe_load(f)
    return self._routes
```

#### 0.3 更新 `src/skills/ui_router_skill.py`

删除硬编码的 `_TOOL_ROUTE_MAP`，改为从 `settings.routes` 动态构建：

```python
def _build_tool_route_map() -> Dict[str, List[str]]:
    """从 routes.yaml 动态构建工具→路由映射"""
    tool_map = {}
    for route in settings.routes.get("routes", []):
        for tool in route.get("tools", []):
            if tool not in tool_map:
                tool_map[tool] = []
            tool_map[tool].append(route["path"])
    return tool_map

_TOOL_ROUTE_MAP = _build_tool_route_map()  # 启动时构建一次
```

#### 0.4 更新 `src/frontend/app.py`

删除硬编码的 `_ROUTE_NAMES`，改为从 `settings.routes` 动态构建：

```python
from src.config.settings import settings

_ROUTE_NAMES = {
    route["path"]: route["name"]
    for route in settings.routes.get("routes", [])
}
```

#### 0.5 更新 `src/config/prompts.yaml`

从 `action_agent_nav_hint` 删除路由表（第 104-186 行），仅保留推理规则：

```yaml
action_agent_nav_hint:
  system: |
    你是青山 V3 多模态调度 Agent 的 UI 导航控制器。你可以调用监控数据工具获取实时数据，
    并在适当时候下发页面跳转信号，将用户导航到最相关的监控页面。
    
    ## 跳转时机
    
    根据用户查询的关键词和调用的工具，推断最相关的监控页面：
    1. 用户查询 COP、冷机状态、水温、冷水机房 → 调用 fetch_cop_data → 跳转到设备运行监控
    2. 用户查询能耗、用电量、电费 → 调用 fetch_energy_summary → 跳转到能耗分析
    3. 用户查询报警、故障 → 调用 fetch_active_alarms → 跳转到实时报警
    ... (保留跳转规则，删除具体路由表)
    
    ## 原则
    
    - 跳转是可选的，仅当用户意图明确指向某个监控页面时才下发跳转信号
    - 一般性问答（如"COP 是什么"）不需要跳转，只回答即可
    - 获取数据后先给出文字总结，再下发跳转信号
```

路由表在运行时通过 Graph 节点动态注入（见 0.6）。

#### 0.6 更新 `src/graph/nodes.py`（可选，推荐）

在 `cognitive_parser` 节点构建 system prompt 时，动态注入路由表：

```python
def cognitive_parser(state: AgentState) -> dict:
    # 从 settings.routes 构建路由表 Markdown
    routes_md = "\n## 可用路由表（福加能碳管理平台）\n\n"
    for route in settings.routes.get("routes", []):
        routes_md += f"- `{route['path']}` — {route['name']}: {route['description']}\n"
    
    # 动态拼接到 system prompt
    system_prompt = settings.prompts["action_agent_nav_hint"]["system"] + routes_md
    
    # ... 构建 messages 并调用 LLM
```

**优势**: 
- ✅ 前端改路由只需修改 `routes.yaml` 一处
- ✅ Agent 代码零改动自动适配
- ✅ 路由表始终最新，无同步问题
- ✅ 符合 DRY 原则和单一职责原则

**风险**: 
- 🟡 需验证动态注入后 Prompt 完整性（测试 Agent 是否仍能正确识别跳转意图）

**测试验证**:
1. 启动 Streamlit，测试多意图场景（"查 COP，顺便看看报警"）
2. 确认跳转链接生成正确
3. 确认路由名称显示正确

**交付物**: 
- `config/routes.yaml`（新增）
- 更新后的 `settings.py`、`ui_router_skill.py`、`app.py`、`prompts.yaml`

---

### Task 1: 接口清单质量检查与补全（交互式）

**输入**: 同事提供的真实表格（`docs/跳转接口逻辑.md`，36条接口）

#### 1.1 质量检查（Claude 自动执行）

扫描表格，识别以下问题：

| 问题类型 | 检查规则 | 发现数量 |
|---------|---------|---------|
| **跳转路由缺失** | 跳转路由列为空或"-" | 5个 |
| **页面URL缺失** | 无法从"触发操作"推断页面完整URL | 需人工确认 |
| **触发操作模糊** | 描述不够具体（如"左侧点击首页"，无元素ID） | 需逐条确认 |
| **接口信息不完整** | 入参/出参描述不清晰 | 需人工补充 |

**输出**: 问题清单（每个问题附原始行号）

#### 1.2 交互式补全（Claude ↔ 用户）

对于每个发现的问题，Claude 提问：

**示例1**（跳转路由缺失）:
> 接口 #19「室外温度」跳转路由为空，跳转页面显示"福加首页"。  
> **问题**: Agent 回答室外温度后是否需要生成跳转链接？  
> **选项**:  
> A. 需要，跳转到首页（请提供路由，如 `/index/index`）  
> B. 不需要，纯数据查询无需跳转  

**示例2**（触发操作模糊）:
> 接口 #7「全厂今日用电量」触发操作："左侧点击用能分析-能耗分析-不用点查询默认显示当日用电"  
> **问题**: "默认显示"是指页面加载自动请求，还是需要点击某个按钮？  
> **选项**:  
> A. 页面加载自动请求  
> B. 需要点击"查询"按钮  
> C. 其他（请描述）  

**输出**: 补全后的标准化表格 `docs/api_specification_raw.md`（包含完整的优先级、页面URL、明确的触发步骤）

#### 1.3 优先级排序

根据业务价值和信息完整度排序：

| 优先级 | 条件 | 示例 |
|--------|------|------|
| 🔴 P0（高） | 信息完整 + 高业务价值（COP、能耗、报警） | #11/12（COP）、#25（报警）、#26/27（光伏） |
| 🟡 P1（中） | 信息完整 + 中业务价值 | #23/24（排名）、#32/33（储能） |
| 🟢 P2（低） | 信息不完整或低频查询 | #19-22（环境参数，跳转路由缺失） |

**交付物**: `docs/api_mapping_prioritized.md`（优先级排序后的清单）

---

### Task 2: 半自动化抓取网络请求（Chrome MCP + 人工兜底）

**前提条件**:
- 浏览器已登录福加平台（`https://aiot-fuca.com`）
- 已完成 Task 1（优先级排序后的清单）

#### 2.1 迭代式抓取策略

**不再一次性抓取所有接口**，改为小批次迭代：

| 批次 | 接口范围 | 预计耗时 |
|------|---------|---------|
| **Batch 1** | P0 高优先级 2-3个（COP、报警、光伏） | 1-2小时 |
| **Batch 2** | P0 剩余 + P1 部分 | 1-2小时 |
| **Batch 3** | P1 剩余 + P2（可选） | 1-2小时 |

每个批次执行：**抓取 → 确认 → 实现 → 测试 → commit**，避免一次性改动过大。

#### 2.2 单个接口的抓取流程（容错 + 交互）

**Step 1**: 尝试自动抓取

```python
try:
    # 1. 打开目标页面
    navigate_page(url=接口对应的页面URL)
    
    # 2. 等待页面加载
    wait_for(text=["查询", "确定", 页面特征文本])
    
    # 3. 执行触发操作（根据"触发操作"列）
    if 触发操作 == "页面加载自动请求":
        # 直接监听网络请求
        pass
    elif "点击" in 触发操作:
        # 先take_snapshot定位元素
        snapshot = take_snapshot()
        # 从snapshot找到对应按钮的uid
        click(uid=按钮uid)
    elif "选择日期" in 触发操作:
        fill(uid=日期输入框uid, value=日期)
        click(uid=查询按钮uid)
    
    # 4. 捕获网络请求
    requests = list_network_requests(pageSize=50)
    # 过滤出目标接口（匹配接口路径）
    target_req = [r for r in requests if 接口路径 in r.url][0]
    # 获取详情
    details = get_network_request(reqid=target_req.id)
    
    # 5. 保存到临时文件
    save_to_json(f"data/api_capture/{接口关键词}.json", details)
    
    print(f"✅ 成功抓取：{接口关键词}")
    
except Exception as e:
    print(f"❌ 自动抓取失败：{接口关键词}")
    print(f"   原因：{e}")
    # 进入人工兜底流程（Step 2）
```

**Step 2**: 自动抓取失败时的兜底策略

Claude 提示用户：

> ❌ **自动抓取失败**：接口「全厂今日用电量」  
> **失败原因**: 无法定位"查询"按钮（页面快照中未找到匹配元素）  
>   
> **请选择处理方式**:  
> A. 我手动操作浏览器触发请求，然后复制 F12 Network 的内容给你  
> B. 跳过该接口，标记为"待手动对接"（后续人工实现）  
> C. 重试（我先调整页面状态，然后你再试一次）  

**Step 3**: 用户选择 A 时的交互流程

Claude 提示：

> 请按以下步骤操作：  
> 1. 在浏览器中打开 `https://aiot-fuca.com/analysis/consumption-panel`  
> 2. 按 F12 打开 DevTools → Network 标签页  
> 3. 执行触发操作：「左侧点击用能分析-能耗分析-不用点查询默认显示当日用电」  
> 4. 在 Network 列表中找到接口 `/analysisWeb/energyAnalysis/cockpit/energyUsage`  
> 5. 右键该请求 → Copy → Copy as cURL (bash)  
> 6. 同时复制 Response 标签页的内容  
> 7. 把这两段内容粘贴给我  

用户粘贴后，Claude 解析并保存：

```python
# 解析 cURL 命令 → 提取请求头、参数
# 解析 Response JSON → 保存
save_to_json(f"data/api_capture/{接口关键词}.json", {
    "method": "GET",
    "url": 从cURL提取,
    "headers": 从cURL提取,
    "request_body": 从cURL提取,
    "response": 用户粘贴的Response,
})
print(f"✅ 已保存（手动提供）：{接口关键词}")
```

#### 2.3 批次确认点

每抓取完一个批次（2-3个接口），Claude 展示汇总：

> **Batch 1 抓取完成**（3个接口）  
>   
> | 接口 | 状态 | 方式 |
> |------|------|------|
> | 机房累计COP | ✅ 成功 | 自动抓取 |
> | 实时报警数量 | ✅ 成功 | 手动提供（F12） |
> | 月度光伏发电量 | ⏭️ 跳过 | 跳转路由缺失，标记待手动对接 |
>   
> **请确认**：是否继续 Batch 2？（输入 yes 继续 / 输入 no 暂停）

**交付物**: 
- `data/api_capture/` 目录（成功抓取的接口 JSON 文件）
- `docs/api_capture_status.md`（抓取状态记录：成功/失败/跳过）

---

### Task 3: 整理接口规范表（人工 + Claude 辅助）

**输入**: Task 2 抓取的 JSON 文件 + 手动提供的数据

**输出**: 标准化的接口规范表格 `docs/api_specification.md`

**新增：数据质量标记**

每个接口增加"数据完整度"标记：

| 标记 | 含义 | 后续处理 |
|------|------|---------|
| ✅ **完整** | 请求/响应结构清晰，字段映射明确 | 直接进入 Task 4 实现 |
| 🟡 **部分** | 响应结构正常，但字段映射需人工确认 | Claude 生成初版映射，用户review |
| ❌ **缺失** | 自动抓取失败，无数据 | 标记"待手动对接"，跳过本轮 |

格式示例：

```markdown
## 1. 机房累计COP ✅ 完整

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /integrateMonitor/chillerRoom/getValueByPointGroupNames` |
| **请求体结构** | `pointGroupNames` (array), `currentDeviceCode` (string, optional) |
| **请求示例** | `{"pointGroupNames": ["水系统累计COP", "机组累计COP"]}` |
| **响应体结构** | `data.水系统累计COP` (float), `data.机组累计COP` (float) |
| **字段映射** | `data.机组累计COP` → `cumulative_cop` |
| **跳转路由** | `/analysis/query` |
| **数据来源** | 自动抓取（Chrome MCP） |
| **备注** | 需要传入具体 `pointGroupNames`，返回对应的实时数据 |

## 2. 实时报警数量 🟡 部分

| 项目 | 内容 |
|------|------|
| **接口 URL** | `GET /intelligentAlarm/alarm/listRealAlarms` |
| **请求参数** | `startTime`, `endTime`, `pageNum`, `pageSize` |
| **响应体结构** | `total` (int), `data[]` (array) |
| **字段映射** | `total` → `total_count`, `data[].alarmId` → `alarm_id` ❓ **待确认** |
| **跳转路由** | `/alarm/realtime` |
| **数据来源** | 手动提供（F12） |
| **备注** | ⚠️ 响应中的 `data[]` 结构需人工确认完整字段 |

## 3. 室外温度 ❌ 缺失

| 项目 | 内容 |
|------|------|
| **接口 URL** | `POST /integrateMonitor/chillerRoom/getValueByPointGroupNames` |
| **跳转路由** | 无（纯数据查询） |
| **状态** | 跳转路由缺失，自动抓取失败 |
| **下一步** | 待魏博源确认是否需要实现该接口 |
```

**人工复核点**：
- 🟡 标记的接口：用户确认字段映射是否正确
- ❌ 标记的接口：用户决定是否跳过或手动补充

**交付物**: `docs/api_specification.md`（完整接口规范文档，含质量标记）

---

### Task 4: 代码实现（批量更新工具函数）

**输入**: `docs/api_specification.md`（接口规范）

**代码修改清单**:

#### 4.1 更新 `src/tools/java_backend.py`

**修改原则**:
- 每个工具函数保持 Mock fallback（`if not _is_mock()` 分支走真实 API，`else` 分支走 Mock）
- 请求体参数从 `site_mapping.yaml` 读取（如果不同接口需要不同配置）
- 响应字段映射到 Pydantic 模型（如 `data.instantCOP` → `instant_cop`）
- 统一错误处理：`{"error": f"工具名: {e}"}`

**示例**（`fetch_cop_data` 从 Mock 改为真实 API）:

```python
def fetch_cop_data(site_id: str, chiller_id: str = "CH-01") -> Dict[str, Any]:
    """获取冷水机组实时 COP（能效比）数据。"""
    try:
        if not _is_mock():
            import httpx
            
            # 构造请求（具体参数根据接口规范填写）
            payload = {
                "nodeId": site_id,
                "deviceCodes": [chiller_id],  # 根据实际接口调整
                "dimension": "realtime",
            }
            
            resp = httpx.post(
                f"{FUCA_API_BASE_URL}/smart-maintenance/deviceData/v1/COPInfo",
                json=payload,
                headers={
                    "Authorization": f"Bearer {FUCA_API_TOKEN}",
                    "tenant_id": FUCA_TENANT_ID,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("code") != 200:
                return {"error": f"API 返回错误: {data.get('message', '未知错误')}"}
            
            api_data = data.get("data", {})
            
            # 字段映射（根据接口规范调整）
            return COPData(
                site_id=site_id,
                chiller_id=chiller_id,
                instant_cop=api_data.get("instantCOP", 0.0),
                cumulative_cop=api_data.get("cumulativeCOP", 0.0),
                chilled_water_out_temp=api_data.get("chilledWaterOutTemp", 0.0),
                cooling_water_in_temp=api_data.get("coolingWaterInTemp", 0.0),
                power_kw=api_data.get("powerKW", 0.0),
                timestamp=api_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                status=api_data.get("status", "normal"),
            ).model_dump()
        
        # Mock fallback（保持现有逻辑）
        return COPData(...).model_dump()
    
    except Exception as e:
        logger.error(f"fetch_cop_data 失败: {e}")
        return {"error": f"fetch_cop_data: {e}"}
```

**批量更新**:
- `fetch_cop_data`（COP 数据）
- `fetch_active_alarms`（实时报警）
- 新增工具（如 `fetch_peak_valley_analysis`、`fetch_load_forecast` 等）

#### 4.2 更新 `config/site_mapping.yaml`

如果不同接口需要不同的 `classificationCode` 或 `deviceCodes`，扩充站点配置：

```yaml
sites:
  FJJB000001:
    name: "福加江北工厂"
    device_type: "FJJB"
    
    # 电力能耗（现有配置）
    energy:
      classification_code: "010000"
      classification_name: "电"
      device_codes: ["LIGHT-0001", "KTXT-CWER-CWEG-0001", ...]
    
    # 冷水机组（新增）
    chiller:
      classification_code: "020000"  # 示例，根据实际接口调整
      classification_name: "冷水机组"
      device_codes: ["KTXT-CWER-CWEG-0001", "KTXT-CWER-CWEG-0002"]
    
    # 报警配置（新增）
    alarm:
      device_level: 0
      device_types: ["chiller", "pump", "cooling_tower"]
```

#### 4.3 更新 `src/skills/ui_router_skill.py`

补充新工具的路由映射（`_TOOL_ROUTE_MAP`）：

```python
_TOOL_ROUTE_MAP: Dict[str, List[str]] = {
    "fetch_cop_data": ["/smart-maintenance/equipment-operation"],
    "fetch_energy_summary": ["/analysis/consumption-panel", "/coordination/energy"],
    "fetch_active_alarms": ["/alarm/realtime"],
    "fetch_peak_valley_analysis": ["/analysis/peak-flat-valley"],  # 新增
    "fetch_load_forecast": ["/analysis/load-forecast"],  # 新增
    "fetch_device_ranking": ["/analysis/rank"],  # 新增
}
```

同时更新前端 `src/frontend/app.py` 的 `_ROUTE_NAMES` 映射。

#### 4.4 更新 `src/tools/__init__.py`

如果新增了工具函数，在 `TOOL_REGISTRY` 和 `TOOL_SCHEMAS` 中注册：

```python
from src.tools.java_backend import (
    fetch_cop_data,
    fetch_energy_summary,
    fetch_active_alarms,
    fetch_peak_valley_analysis,  # 新增
    fetch_load_forecast,  # 新增
)

TOOL_REGISTRY = {
    # ... 现有工具
    "fetch_peak_valley_analysis": fetch_peak_valley_analysis,
    "fetch_load_forecast": fetch_load_forecast,
}

TOOL_SCHEMAS = [
    # ... 现有 schema
    {
        "type": "function",
        "function": {
            "name": "fetch_peak_valley_analysis",
            "description": "获取站点峰平谷电量分析数据",
            "parameters": { ... },
        }
    },
]
```

**交付物**: 更新后的代码文件

---

### Task 5: 测试验证

#### 5.1 单元测试（Mock 环境）

验证工具函数在 Mock 模式下仍能正常工作（保持向后兼容）：

```bash
pytest src/tests/test_java_backend.py -v
```

#### 5.2 集成测试（真实 API）

配置 `.env` 启用真实 API（`FUCA_API_BASE_URL` 等），测试每个工具：

```python
# src/tests/test_realapi_integration.py
def test_fetch_cop_data_real():
    """测试 COP 真实 API 调用"""
    result = fetch_cop_data(site_id="FJJB000001", chiller_id="KTXT-CWER-CWEG-0001")
    assert "error" not in result
    assert result["instant_cop"] > 0
    assert result["site_id"] == "FJJB000001"

def test_fetch_active_alarms_real():
    """测试报警真实 API 调用"""
    result = fetch_active_alarms(site_id="FJJB000001")
    assert "error" not in result
    assert "alarms" in result
```

#### 5.3 端到端测试（Streamlit）

启动 Streamlit 前端，测试多意图场景：

```bash
streamlit run src/frontend/app.py
```

测试用例：
- "查一下今天的 COP，顺便看看有没有报警"
- "帮我分析峰平谷用电情况"
- "今天的负荷预测准不准？"

验证：
- 工具调用是否返回真实数据（非 Mock）
- 页面跳转链接是否正确生成
- 多意图是否都被识别并执行

**交付物**: 测试通过记录 + 截图

---

### Task 6: 文档更新

按照 `CLAUDE.md` 规范更新文档：

#### 6.1 更新 `AI_CONTEXT.md`

- **§4.1 Tools 表格**: 将对应工具的状态从 `Mock` 改为 `✅ 真实`
- **§5 开发阶段**: Phase 4 状态更新为 `✅ 完成`
- **§6 变更日志**: 添加本次变更摘要（保留最近 5 条）

#### 6.2 更新 `CHANGELOG.md`

格式：

```markdown
## 2026-06-XX

### [tools] 批量对接福加真实监控 API

- 接入真实 API：
  - `fetch_cop_data`: `/smart-maintenance/deviceData/v1/COPInfo`
  - `fetch_active_alarms`: `/alarm/active/v1/list`
  - `fetch_peak_valley_analysis`: `/xxx/xxx/v1/XXX`（根据实际接口填写）
- 更新 `site_mapping.yaml`: 新增 `chiller` 和 `alarm` 配置段
- 更新 `ui_router_skill.py`: 补充新工具的路由映射
- 新增测试: `src/tests/test_realapi_integration.py`
- 修复: Mock fallback 逻辑，确保未配置 API 时仍可运行

魏博源
```

#### 6.3 更新 `README.md`（可选）

如果有新增环境变量或配置项，更新安装指南。

**交付物**: 更新后的文档

---

## 风险与注意事项

### 风险点

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **接口不稳定** | 真实 API 返回格式与抓取时不一致 | 保留 Mock fallback，真实 API 失败时自动降级 |
| **权限问题** | 部分接口需要特殊权限，Claude 无法通过浏览器抓取 | 手动提供接口文档或让同事提供 Postman collection |
| **字段映射错误** | 接口字段名与 Pydantic 模型不匹配 | 逐个接口测试验证，错误时回退到 Mock 并记录 |
| **Token 泄露** | 抓取的 JSON 包含敏感 token | 自动脱敏处理（仅保留 token 前 10 位 + `...`）|
| **批量修改引入 Bug** | 一次性修改多个工具可能引入回归问题 | 分阶段执行（先高优先级 2-3 个接口验证）|

### 注意事项

1. **环境变量管理**: 确保 `.env` 已配置 `FUCA_API_BASE_URL`、`FUCA_API_TOKEN`、`FUCA_TENANT_ID`，且不提交到 Git
2. **向后兼容**: 所有工具必须保留 Mock fallback，确保未配置 API 时系统仍可运行
3. **错误处理**: 统一返回 `{"error": "工具名: 错误信息"}`，防止 Agent 崩溃
4. **分阶段提交**: 每完成 2-3 个接口对接后 commit 一次，避免一次性改动过大难以回滚
5. **文档同步**: 每次 commit 必须同步更新 `CHANGELOG.md` 和 `AI_CONTEXT.md`

---

## 时间估算

| Task | 预计耗时 | 依赖 |
|------|---------|------|
| Task 1: 接口清单标准化 | 1-2 小时 | 同事提供初始清单 |
| Task 2: 自动化抓取（2-3 个高优先级接口） | 2-3 小时 | Task 1 |
| Task 3: 整理接口规范表 | 1 小时 | Task 2 |
| Task 4: 代码实现（高优先级接口） | 3-4 小时 | Task 3 |
| Task 5: 测试验证 | 1-2 小时 | Task 4 |
| Task 6: 文档更新 | 30 分钟 | Task 5 |
| **第一轮验证总计** | **8-12 小时** | |
| Task 2-6 重复（剩余接口批量处理） | 6-10 小时 | 第一轮验证通过 |
| **总计** | **14-22 小时** | |

建议分 2-3 个 session 完成，每个 session 聚焦 2-3 个接口。

---

## 执行建议

### 整体策略：迭代式推进 + 交互式决策

**核心原则**：
- ✅ 小批次迭代（每次 2-3 个接口）
- ✅ 抓取后即确认（不等到全部抓取完）
- ✅ 遇到问题立即询问用户（不盲目重试）
- ✅ 每个批次独立 commit（便于回滚）

---

### Session 1: Task 0 + Task 1（路由解耦 + 接口质量检查）

**目标**: 完成基础设施优化 + 确认接口清单质量

**Task 0**: 路由配置解耦（1-2 小时）
- 创建 `config/routes.yaml`
- 更新 `settings.py`、`ui_router_skill.py`、`app.py`、`prompts.yaml`
- 测试：启动 Streamlit，确认跳转链接生成正常
- ✅ Commit: `[refactor] 路由配置解耦，单点管理`

**Task 1**: 接口质量检查（30分钟）
- Claude 自动扫描 `docs/跳转接口逻辑.md`
- 识别问题：5个跳转路由缺失、触发操作模糊的条目
- **交互点 #1**: Claude 提问每个缺失项的处理方式
  - 用户回答后，Claude 生成补全后的清单
- 优先级排序：P0（高）3-5个 → P1（中）→ P2（低）
- 输出：`docs/api_mapping_prioritized.md`

**检查点**: 
- ✅ 路由配置是否解耦成功？（Streamlit 测试通过）
- ✅ 接口清单是否补全？（跳转路由缺失问题已解决）

---

### Session 2: Task 2.1 Batch 1（首批接口抓取验证）

**目标**: 抓取 P0 高优先级 2-3 个接口，验证半自动化方案可行性

**接口选择**（从用户表格中提取）:
1. #11/12: 机房累计COP / 瞬时COP（`/integrateMonitor/chillerRoom/getValueByPointGroupNames`）
2. #25: 实时报警数量（`/intelligentAlarm/alarm/listRealAlarms`）
3. #26/27: 月度/日度光伏发电量（`/integrateMonitor/fucaOverviewScreen/carbonInfo`）

**执行流程**（每个接口独立）:

1. **尝试自动抓取**
   - 打开目标页面
   - 执行触发操作（点击/填写/等待）
   - 捕获网络请求
   
2. **成功** → 保存 JSON，继续下一个
   
3. **失败** → **交互点 #2**: Claude 询问用户
   > ❌ 自动抓取失败：接口「机房累计COP」  
   > 失败原因：无法定位"查询"按钮  
   > 请选择：A) 我手动F12复制  B) 跳过该接口  C) 重试

4. **用户选A** → Claude 提供详细步骤，等待用户粘贴 cURL + Response

5. **批次完成** → **交互点 #3**: 展示汇总，询问是否继续
   > Batch 1 完成（3个接口）：2个成功，1个手动提供  
   > 是否继续 Batch 2？（yes/no）

**检查点**:
- ✅ Chrome MCP 能否成功抓取？
- ✅ 手动兜底流程是否顺畅？
- ✅ 抓取的数据是否完整？

**输出**: 
- `data/api_capture/*.json`（2-3个接口）
- ✅ Commit: `[tools] 抓取 Batch 1 接口数据（COP/报警/光伏）`

---

### Session 3: Task 3 + Task 4.1（Batch 1 实现）

**目标**: 整理 Batch 1 规范表 + 实现代码

**Task 3**: 整理接口规范（30分钟）
- Claude 根据 JSON 文件生成 `docs/api_specification.md`
- 标记数据质量：✅ 完整 / 🟡 部分 / ❌ 缺失
- **交互点 #4**: 对于 🟡 标记的接口，用户确认字段映射

**Task 4.1**: 代码实现（1-2小时）
- 在 `java_backend.py` 实现 Batch 1 的 3 个工具函数
- 更新 `site_mapping.yaml`（如果需要新配置）
- 更新 `ui_router_skill.py` 的路由映射（已自动从 routes.yaml 读取）

**Task 5**: 测试验证（30分钟）
- 启动 Streamlit
- 测试："查一下机房COP，顺便看看有没有报警"
- 确认：工具返回真实数据、跳转链接正确

**检查点**:
- ✅ 工具函数是否正确调用真实 API？
- ✅ 响应字段映射是否正确？
- ✅ 前端显示是否正常？

**输出**: ✅ Commit: `[tools] 接入 Batch 1 真实 API（COP/报警/光伏）`

---

### Session 4-5: 重复 Session 2-3 流程（Batch 2, Batch 3）

每个批次：
1. 抓取 2-3 个接口
2. 遇到问题询问用户
3. 实现 + 测试
4. Commit

**预计批次**:
- Batch 2: 能耗排名、储能充放电、能效日历
- Batch 3: 环境参数、驾驶舱数据、其他低优先级

---

### 交互式决策清单（供 Claude 参考）

| 场景 | Claude 应该询问用户 |
|------|---------------------|
| 跳转路由缺失 | 是否需要跳转？路由是什么？ |
| 触发操作模糊 | 具体步骤是什么？需要点哪个按钮？ |
| 自动抓取失败 | A) 手动F12  B) 跳过  C) 重试 |
| 字段映射不确定 | 响应中的 `xxx` 字段对应 Pydantic 模型的哪个字段？ |
| 批次完成 | 是否继续下一批次？ |
| 测试发现问题 | 返回数据不符合预期，是接口问题还是代码问题？ |

---

## 总结

### 方案评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **可行性** | ⭐⭐⭐⭐⭐ | Chrome MCP + 接口规范化 + 批量实现，技术路径清晰 |
| **效率** | ⭐⭐⭐⭐ | 自动化抓取减少 50% 手动工作，但需要人工复核 |
| **可维护性** | ⭐⭐⭐⭐⭐ | 接口规范文档 + Mock fallback，便于后续维护 |
| **风险** | ⭐⭐⭐ | 接口稳定性依赖福加平台，需保留降级方案 |

### 关键成功因素

1. **清晰的接口清单**：同事提供的表格必须包含页面 URL 和触发操作步骤
2. **分阶段验证**：先验证 2-3 个接口，确保方案可行后再批量处理
3. **人工复核**：自动化抓取后需确认请求/响应结构正确性
4. **向后兼容**：保留 Mock fallback，确保系统在任何环境下都能运行
5. **文档同步**：每次代码修改必须同步更新 `CHANGELOG.md` 和 `AI_CONTEXT.md`

### 下一步行动

1. **魏博源**: 与同事确认接口清单，补充"触发操作"列（Task 1）
2. **Claude（新 session）**: 根据清单执行 Task 2-6，先完成高优先级接口验证
3. **魏博源**: 复核抓取的接口数据，确认字段映射正确性
4. **Claude（新 session）**: 批量处理剩余接口，完成 Phase 4.2

---

## 附录

### 参考文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| 项目规范 | `CLAUDE.md` | Git 规范、代码规范、文档维护规则 |
| 项目状态 | `AI_CONTEXT.md` | 当前阶段、工具注册表、变更日志 |
| 真实 API 示例 | `src/tools/java_backend.py` (L86-141) | `fetch_energy_summary` 的真实 API 实现 |
| 站点配置 | `config/site_mapping.yaml` | 站点参数映射表 |
| 路由映射 | `src/skills/ui_router_skill.py` (L97-101) | 工具 → 页面路由映射 |
| 前端路由名称 | `src/frontend/app.py` (L18-24) | 路由 → 中文名称映射 |
| Pydantic 模型 | `src/schemas/action_agent.py` | 工具输出数据模型定义 |

### Chrome MCP 工具速查

| 工具 | 用途 |
|------|------|
| `mcp__chrome__navigate_page` | 打开页面 |
| `mcp__chrome__list_network_requests` | 列出网络请求 |
| `mcp__chrome__get_network_request` | 获取请求详情（Request + Response）|
| `mcp__chrome__click` | 点击元素 |
| `mcp__chrome__fill` | 填写表单 |
| `mcp__chrome__take_snapshot` | 获取页面快照（用于定位元素 uid）|

---

> **本文档遵循 `CLAUDE.md` 规范，变更需同步更新 `CHANGELOG.md`**

