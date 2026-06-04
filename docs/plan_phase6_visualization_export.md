# EnerGraph — Phase 6: 数据可视化 + 报表导出

**目标**: 让 Agent 能够查询多日历史数据，以表格/图表形式下发给前端，支持 CSV 下载和可视化图表渲染。  
**前置条件**: Phase 2 完成（SSE + Java 后端工具体系可用）；建议先完成 `plan_skills_base_class.md`  
**可并行**: 本 Phase 不依赖 Phase 3/4/5，可与任意 Phase 并行执行  
**完成标志**: 用户问"近十天负载消耗"时，Agent 通过 SSE 推送 `event: data_card`，前端可渲染表格/图表并下载 CSV

---

## 业务场景

### 场景 1: 多日数据 + 表格下载
用户问："近十天 SH-01 站点的负载消耗情况？"

Agent 应：
1. 调用 `fetch_energy_range` 获取近 10 天能耗汇总
2. 流式返回文字总结："近十天日均用电 11,200 kWh，峰值出现在 5月28日..."
3. 调用 `export_data_table` 生成 DataCard，通过 SSE `event: data_card` 下发
4. 前端渲染表格 + "下载 CSV" 按钮

### 场景 2: 图表可视化
用户问："光伏发电量和负载消耗的趋势对比？"

Agent 应：
1. 调用 `fetch_energy_range` 获取多日数据
2. 通过 DataCard 的 `chart` 字段下发图表配置（type: "line", x_axis: "date", y_axis: [...]）
3. 前端根据配置渲染折线图/柱状图

### 场景 3: 报警报表导出
用户问："导出本月所有报警记录"

Agent 应：
1. 调用 `fetch_alarm_history` 获取历史报警
2. 生成含表格 + CSV 下载的 DataCard

---

## SSE 协议扩展

在现有 4 种事件基础上新增 `event: data_card`：

| 事件类型 | 用途 | 触发时机 |
|----------|------|----------|
| `event: text` | LLM token 流 | 每次 LLM 生成 |
| `event: action` | 页面跳转信号 | UIAction navigate |
| **`event: data_card`** | **结构化数据卡片** | **多日数据/导出/图表** |
| `event: done` | 流结束 | 图执行完毕 |
| `event: error` | 错误信息 | 异常 |

DataCard 载荷结构：
```json
{
  "card_type": "table | chart | both",
  "title": "SH-01 近十天能耗汇总",
  "columns": [{"key": "date", "label": "日期", "unit": ""}],
  "rows": [{"date": "2026-05-25", "total_consumption_kwh": 11200, ...}],
  "chart": {"type": "bar|line|pie", "x_axis": "date", "y_axis": ["..."], "title": "..."},
  "download": {"format": "csv", "filename": "xxx.csv", "url": "/export/{task_id}"}
}
```

---

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/schemas/data_card.py` | `DataCard` / `TableData` / `ChartConfig` / `DownloadInfo` Pydantic 模型 |
| `src/tools/export_data.py` | 数据导出工具：格式化表格 + 生成 CSV 临时文件 + 返回下载 URL |
| `src/tests/test_data_visualization.py` | 工具/Skill/SSE 端点全链路测试 |

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `src/tools/java_backend.py` | 新增 `fetch_energy_range` + `fetch_alarm_history`（多日查询） |
| `src/tools/__init__.py` | 注册 `fetch_energy_range`、`fetch_alarm_history`、`export_data_table` |
| `src/graph/state.py` | 新增 `pending_data_cards: Annotated[List[DataCard], operator.add]` |
| `src/skills/ui_router_skill.py` | 扩展 tools 列表；新增 `infer_data_card()` 方法 |
| `src/services/api.py` | SSE 新增 `event: data_card`；新增 `GET /export/{task_id}` 下载端点 |
| `src/config/prompts.yaml` | 新增 `data_visualization_hint` Prompt |
| `src/frontend/app.py` | 解析 data_card 事件，渲染表格/图表/下载按钮 |

---

## 子任务（每个子任务 = 一个 commit）

### T1: 数据模型 + AgentState 扩展
- **文件**: `src/schemas/data_card.py`, `src/graph/state.py`
- **改动**:
  - 新建 `data_card.py`，定义 Pydantic 模型：
    - `ColumnDef`: `key` + `label` + `unit`（可选）
    - `TableData`: `columns: List[ColumnDef]` + `rows: List[Dict]`
    - `ChartConfig`: `type`（bar/line/pie）+ `x_axis` + `y_axis` + `title`
    - `DownloadInfo`: `format` + `filename` + `url`
    - `DataCard`: `card_type` + `title` + `table` + `chart` + `download`
  - `state.py` 新增 `pending_data_cards: Annotated[List[DataCard], operator.add]`
- **验收**: `python -c "from src.schemas.data_card import DataCard; print(DataCard(card_type='table', title='test'))"` 无报错

### T2: 日期范围查询工具
- **文件**: `src/tools/java_backend.py`, `src/tools/__init__.py`
- **改动**:
  - 新增 `fetch_energy_range(site_id, start_date, end_date)` → `List[EnergySummary]`
    - Mock: 循环日期范围每天生成随机数据
    - 真实: `GET /energy/range?site_id=&start_date=&end_date=`
  - 新增 `fetch_alarm_history(site_id, start_date, end_date)` → `AlarmList`
  - 注册到 `TOOL_REGISTRY` + `TOOL_SCHEMAS`
- **验收**: Mock 模式正常返回多日数据

### T3: 数据导出工具
- **文件**: `src/tools/export_data.py`, `src/tools/__init__.py`
- **改动**:
  - 新建 `export_data.py`
  - `export_data_table(title, columns, rows, filename)` → `DataCard` dict
    - 生成 CSV 文件存入 `data/exports/`，生成唯一 `task_id`
    - 返回 DataCard 含 `table` + `download`
  - 注册到 `TOOL_REGISTRY` + `TOOL_SCHEMAS`
- **验收**: 调用工具返回含 download url 的 DataCard dict

### T4: UIRouterSkill 扩展 + Prompt
- **文件**: `src/skills/ui_router_skill.py`, `src/config/prompts.yaml`
- **改动**:
  - `UIRouterSkill.tools` 新增 `fetch_energy_range`、`fetch_alarm_history`、`export_data_table`
  - 新增 `infer_data_card()` 静态方法：检测多日工具调用结果，自动推断图表类型并生成 DataCard
  - `prompts.yaml` 新增 `data_visualization_hint`：引导 LLM 识别"多日查询""导出""图表"意图，调用范围查询 + 导出工具
- **验收**: 单元测试验证 `infer_data_card` 生成含 chart 和 download 的 DataCard

### T5: SSE data_card 事件 + 下载端点
- **文件**: `src/services/api.py`
- **改动**:
  - `_sse_generator` 新增 `event: data_card` 推送（检测 `pending_data_cards`）
  - 新增 `GET /export/{task_id}` 端点：读取 `data/exports/{task_id}.csv`，返回 `FileResponse`
  - `POST /invoke` 返回值新增 `data_cards` 字段
- **验收**: curl 测试可见 `event: data_card`，下载端点返回 CSV

### T6: Streamlit 前端适配
- **文件**: `src/frontend/app.py`
- **改动**:
  - 解析 `event: data_card` 事件
  - `st.dataframe()` 渲染表格，`st.bar_chart()` / `st.line_chart()` 渲染图表
  - `st.download_button()` 提供 CSV 下载
- **验收**: 前端可展示表格 + 图表，可下载 CSV

### T7: 集成测试
- **文件**: `src/tests/test_data_visualization.py`
- **改动**: 测试 `fetch_energy_range` / `export_data_table` / `infer_data_card` / SSE data_card 事件 / /export 下载端点
- **验收**: `pytest src/tests/test_data_visualization.py` 全部通过

---

## 关键架构决策

**为什么扩展现有 UIRouterSkill 而非新建 DataExportSkill？**  
数据导出/可视化是监控查询的自然延伸（查数据 → 看数据 → 导出数据），与 UIRouterSkill 职责天然耦合。新建 Skill 会导致两个 Skill 调用相同工具，增加调度复杂度。若后续导出逻辑超过 200 行，可拆分为独立 Skill。

**为什么用独立 `DataCard` 模型而非扩展 UIAction？**  
UIAction 的 `route` 字段对数据卡片无意义。DataCard 有自己的结构化字段（columns/rows/chart），混入 UIAction 会破坏简洁性。两者通过独立 SSE 事件下发，前端分别处理。

**数据来源**:  
不直连数据库。所有数据通过 Java 后端 REST API 获取（`fetch_energy_range` → Java `/energy/range`）。Agent 侧已预留 Mock fallback，Java 后端未就绪时不影响开发。

---

## Java 后端需配合提供的 API

| 接口 | 方法 | 说明 | 优先级 |
|------|------|------|--------|
| `/energy/range` | GET | 多日能耗汇总，参数 `site_id`, `start_date`, `end_date` | 高 |
| `/alarms/history` | GET | 历史报警列表，参数 `site_id`, `start_date`, `end_date` | 中 |

---

## 关键文件
- `src/schemas/data_card.py` — DataCard / TableData / ChartConfig Pydantic 模型
- `src/tools/export_data.py` — 数据导出 + CSV 生成工具
- `src/tools/java_backend.py` — 新增范围查询工具
- `src/skills/ui_router_skill.py` — infer_data_card 推断逻辑
- `src/services/api.py` — SSE data_card 事件 + /export 下载端点

## Skills 融合说明
- T4 扩展 `UIRouterSkill.tools` 列表和新增 `infer_data_card()` 方法
- 不新建 Skill，保持 `SKILL_REGISTRY` 精简
- 若后续导出逻辑复杂化（多格式/定时/权限），可拆分为 `DataExportSkill`
- 详见 `docs/plan_skills_refactor.md`
