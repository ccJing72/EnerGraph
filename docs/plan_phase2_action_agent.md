# EnerGraph — Phase 2: Action Agent（FastAPI + 页面控制信号）

**目标**: 将 LangGraph Agent 暴露为 FastAPI SSE 服务，向上接收前端页面上下文并返回跳转控制信号，向下通过 Tools 对接 Java 后端真实监控数据。  
**前置条件**: Phase 1 完成（ReAct 循环可运行）  
**完成标志**: `/stream` 端点可同时流式输出文本 token 和 `UIAction` 跳转信号，Vue3 前端可解析

---

## 业务场景

用户在福加监控平台首页问："冷水机房现在 COP 多少？"

Agent 应：
1. 调用 Java 后端工具获取实时 COP 数据
2. 流式返回文字总结："冷水机房#1 瞬时 COP 为 6.90，累计 COP 7.20，运行正常。"
3. 同时下发跳转信号：`{type: "navigate", route: "/chiller-room", params: {site_id: "xxx"}}`

前端收到跳转信号后自动路由到冷水机房详情页。

---

## SSE 协议规范（前端对接契约）

```
event: text
data: {"token": "冷水机房#1 瞬时 COP 为 6.90，"}

event: action
data: {"type": "navigate", "route": "/chiller-room", "params": {"site_id": "SH-01"}}

event: done
data: {}

event: error
data: {"message": "错误描述"}
```

- `event: text` — 每个 LLM token 一条，前端追加到对话气泡
- `event: action` — UIAction 信号，前端调用 `router.push(route, params)`
- `event: done` — 流结束，前端关闭 SSE 连接
- `event: error` — 异常，前端显示错误提示

**Vue3 消费示例（供前端团队参考）**:
```typescript
const es = new EventSource('/stream', { method: 'POST', body: JSON.stringify(input) })
// 注意：标准 EventSource 不支持 POST，需用 fetch + ReadableStream 或 @microsoft/fetch-event-source
es.addEventListener('text', e => appendToken(JSON.parse(e.data).token))
es.addEventListener('action', e => handleAction(JSON.parse(e.data)))
es.addEventListener('done', () => es.close())
```

---

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/schemas/action_agent.py` | `PageContext` / `ActionAgentInput` / `UIAction` Pydantic 模型 |
| `src/tools/navigate_to_page.py` | 纯状态变更工具，将 UIAction 写入 `pending_actions` |
| `src/tools/java_backend.py` | Java HTTP 工具（COP / 能耗 / 报警），无配置时 Mock fallback |

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `src/graph/state.py` | 新增 `page_context: Optional[PageContext]`、`pending_actions: Annotated[List[UIAction], operator.add]` |
| `src/graph/nodes.py` | `v3_engine_router` 中为 `navigate_to_page` 工具添加 list-append 分支 |
| `src/tools/__init__.py` | 注册 `navigate_to_page` + 3 个 Java 工具 |
| `src/config/prompts.yaml` | 新增 `action_agent_nav_hint`：告知 LLM 可用路由表和何时调用跳转工具 |
| `src/services/api.py` | 实现 FastAPI app（当前为空占位） |

---

## 子任务（每个子任务 = 一个 commit）

### T1: Schemas + AgentState 扩展
- **文件**: `src/schemas/action_agent.py`, `src/graph/state.py`
- **改动**:
  - 新建 `action_agent.py`，定义 `PageContext`、`ActionAgentInput`、`UIAction`
  - `state.py` 新增 `page_context` 和 `pending_actions` 字段
- **验收**: `python -c "from src.schemas.action_agent import UIAction; print(UIAction(type='navigate', route='/test', params={}))"` 无报错

### T2: 导航工具 + Prompt
- **文件**: `src/tools/navigate_to_page.py`, `src/tools/__init__.py`, `src/config/prompts.yaml`
- **改动**:
  - 新建 `navigate_to_page(route, params)` 工具，返回 `UIAction` dict
  - 注册到 `TOOL_REGISTRY` + `TOOL_SCHEMAS`
  - `nodes.py` 中 `v3_engine_router` 添加 `navigate_to_page` → `pending_actions` append 逻辑
  - `prompts.yaml` 新增路由表提示（`/chiller-room`, `/energy-monitor`, `/pv-storage` 等）
- **验收**: 单元测试验证工具调用后 `pending_actions` 有一条 UIAction

### T3: Java 后端工具（Mock fallback）
- **文件**: `src/tools/java_backend.py`, `src/tools/__init__.py`
- **改动**:
  - `fetch_cop_data(site_id, time_range)` → `COPData`
  - `fetch_energy_summary(site_id, date)` → `EnergySummary`
  - `fetch_active_alarms(site_id)` → `AlarmList`
  - 检查 `JAVA_API_BASE_URL` 环境变量；未配置时返回 Mock 数据（与 Phase 4 模式一致）
  - Pydantic I/O 模型定义在 `src/schemas/action_agent.py`
- **验收**: 未设置 `JAVA_API_BASE_URL` 时工具正常返回 Mock 数据

### T4: FastAPI 骨架 + /invoke
- **文件**: `src/services/api.py`
- **改动**:
  - FastAPI app，`GET /health`
  - `POST /invoke`：同步运行 graph，返回 `{"report": str, "actions": List[UIAction]}`
  - 接收 `ActionAgentInput`（含可选 `page_context`）
- **验收**: `curl -X POST localhost:8000/invoke -d '{"user_input":"冷水机房COP多少"}'` 返回报告

### T5: SSE 流式端点 /stream
- **文件**: `src/services/api.py`
- **改动**:
  - `POST /stream`，`StreamingResponse(media_type="text/event-stream")`
  - 使用 `graph.astream_events()` 遍历事件
  - `AIMessageChunk` → `event: text`
  - `pending_actions` 新增项 → `event: action`
  - 图结束 → `event: done`
- **验收**: `curl -N -X POST localhost:8000/stream -d '{"user_input":"..."}' -H "Content-Type: application/json"` 可见分行 SSE 输出

### T6: 页面上下文注入 + 集成测试
- **文件**: `src/services/api.py`, `src/graph/nodes.py`, `src/tests/test_action_agent.py`
- **改动**:
  - 将 `page_context` 从请求体注入初始 `AgentState`
  - `cognitive_parser` 系统 prompt 中格式化注入当前路由和 site_id
  - 集成测试：mock graph，验证 `/stream` 端点输出包含 `event: action`
- **验收**: `pytest src/tests/test_action_agent.py` 通过

---

## 关键架构决策

**为什么 `pending_actions` 放在 AgentState 而非旁路队列？**  
保持图的可序列化性，支持 LangGraph checkpointer（Phase 3 记忆功能前置条件）。

**为什么用专用工具而非解析 LLM 自由文本？**  
结构化 tool call 比正则解析路由名更可靠，LLM 决定"何时跳转"，工具强制 schema。

**为什么 POST /stream 而非 GET /stream？**  
`page_context` 和 `user_input` 在请求体，GET 用 query param 会泄露到日志且有长度限制。

**与 Phase 4 的关系**:  
Phase 4 只需替换 `java_backend.py` 内部实现（Mock → 真实 HTTP），工具签名、schema、图接线不变。

---

## 依赖安装
```bash
pip install fastapi uvicorn[standard] httpx
```

## 关键文件
- `src/services/api.py` — FastAPI 主实现
- `src/schemas/action_agent.py` — Action Agent 数据模型
- `src/tools/navigate_to_page.py` — 跳转工具
- `src/tools/java_backend.py` — Java 后端工具（Mock fallback）
- `src/graph/state.py` — AgentState 扩展

## Skills 融合说明
- T1 完成后同步建立 `src/skills/` 骨架（已完成）
- T2 导航工具的业务逻辑实现在 `src/skills/ui_router_skill.py`，不写入 nodes.py
- T3 Java 工具注册后，`UIRouterSkill.tools` 列表已预置，无需改 Skill 文件
- 详见 `docs/plan_skills_refactor.md`

## 前端对接说明
- 推荐使用 `@microsoft/fetch-event-source` 库（支持 POST + SSE）
- 监听 `event: action` 后调用 `router.push(data.route, { query: data.params })`
- `page_context` 字段由前端在每次请求时注入当前路由和 site_id
