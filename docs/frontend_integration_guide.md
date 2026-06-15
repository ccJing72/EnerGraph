# EnerGraph Agent API — 前端对接指南

> 本文档面向前端开发人员，包含接口定义、Vue.js 代码示例和 TypeScript 类型定义。

---

## 目录

1. [快速开始](#1-快速开始)
2. [接口总览](#2-接口总览)
3. [请求体定义](#3-请求体定义)
4. [/invoke 同步接口](#4-invoke-同步接口)
5. [/stream 流式接口（SSE）](#5-stream-流式接口sse)
6. [TypeScript 类型定义](#6-typescript-类型定义)
7. [Vue 组件示例](#7-vue-组件示例)
8. [页面跳转处理](#8-页面跳转处理)
9. [错误处理](#9-错误处理)
10. [常见问题](#10-常见问题)

---

## 1. 快速开始

### 1.1 环境准备

```bash
# Python 环境（conda）
conda activate energraph

# 启动 API 服务
python run.py
```

启动后访问 `http://localhost:8000/docs` 可查看 Swagger 交互文档。

### 1.2 验证连通

```bash
curl http://localhost:8000/health
# 返回: {"status": "ok"}
```

### 1.3 鉴权

如果后端配置了 `API_KEY`，所有请求需携带 Bearer Token：

```
Authorization: Bearer <api_key>
```

`/health` 端点不需要鉴权。

---

## 2. 接口总览

| 端点 | 方法 | 说明 | 鉴权 |
|------|------|------|------|
| `/health` | GET | 健康检查 | ❌ |
| `/invoke` | POST | 同步调用，返回完整报告 | ✅ |
| `/stream` | POST | SSE 流式调用，逐 token 推送 | ✅ |

**Base URL**: 开发环境 `http://localhost:8000`，生产环境由后端配置。

**推荐**: 生产环境使用 `/stream` 接口，用户体验更好（实时打字效果）。

---

## 3. 请求体定义

### 3.1 POST Body（`/invoke` 和 `/stream` 共用）

```json
{
  "user_input": "查看冷站COP",
  "page_context": {
    "current_route": "/chiller-room",
    "site_id": "FJJB000001",
    "params": {},
    "meta": {}
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_input` | `string` | ✅ | 用户输入文本 |
| `page_context` | `object` | ❌ | 当前页面上下文 |
| `page_context.current_route` | `string` | ❌ | 当前页面路由，默认 `/` |
| `page_context.site_id` | `string` | ❌ | 当前选中站点 ID |
| `page_context.params` | `object` | ❌ | 页面级参数（筛选条件、选中设备等） |
| `page_context.meta` | `object` | ❌ | 扩展元数据 |

> **提示**: `page_context` 帮助 Agent 理解用户当前所在的页面，从而给出更精准的导航建议。建议每次请求都传入。

---

## 4. /invoke 同步接口

### 4.1 请求

```
POST /invoke
Content-Type: application/json
```

### 4.2 响应

```json
{
  "report": "## 冷站 COP 分析\n\n当前冷站瞬时 COP 为 **4.2**...",
  "actions": [
    {
      "type": "navigate",
      "route": "/chiller-room/detail",
      "params": { "chiller_id": "CW-01" },
      "meta": {}
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `report` | `string` | Markdown 格式的分析报告 |
| `actions` | `UIAction[]` | Agent 建议的 UI 动作列表（页面跳转等） |

### 4.3 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 401 | API Key 无效 |
| 500 | Agent 执行失败（`detail` 字段包含错误信息） |

---

## 5. /stream 流式接口（SSE）

### 5.1 请求

```
POST /stream
Content-Type: application/json
```

### 5.2 SSE 事件类型

流式接口返回 `text/event-stream`，包含以下事件类型：

| 事件类型 | 说明 | 前端建议 |
|----------|------|----------|
| `thinking` | Agent 思考过程（工具调用前的推理） | 可折叠/丢弃 |
| `tool_call` | 工具调用（name + args） | 可折叠/丢弃 |
| `tool_result` | 工具返回结果（name + result） | 可折叠/丢弃 |
| `rag_sources` | RAG 知识库检索来源 | 可折叠/展示为引用 |
| `text` | 最终回答文本（流式） | **主体内容，必须展示** |
| `intent_plan` | 多意图识别计划 | 可折叠 |
| `action` | UI 动作（页面跳转等） | 渲染为按钮或自动执行 |
| `error` | 错误信息 | 展示给用户 |
| `done` | 流结束标志 | 停止加载状态 |

#### `thinking` — Agent 思考过程

```
event: thinking
data: {"text": "用户问的是机房COP，我需要调用"}
```

工具调用前 cognitive_parser 的推理文本。前端可选择折叠或丢弃。

#### `tool_call` — 工具调用

```
event: tool_call
data: {"name": "fetch_cop_data", "args": {"site_id": "FJJB000001", "chiller_id": "CH-01"}}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 工具名称 |
| `args` | `object` | 工具参数 |

#### `tool_result` — 工具返回结果

```
event: tool_result
data: {"name": "fetch_cop_data", "result": {"cumulative_cop": 7.0, "instant_cop": 7.4, ...}}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `string` | 工具名称 |
| `result` | `object` | 工具返回的 JSON 数据 |

#### `rag_sources` — RAG 知识库检索来源

```
event: rag_sources
data: {"query": "含湿量与相对湿度的区别", "results": ["问题：...\n回答：...", ...]}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | `string` | 检索查询 |
| `results` | `string[]` | 检索到的知识片段列表 |

前端可展示为"参考来源"或引用标注。

#### `text` — 最终回答文本

```
event: text
data: {"text": "当前冷站的"}
```

前端应将每个 `text` 事件的内容追加到报告文本中，实现打字机效果。**这是主体回答内容，必须展示。**

#### `intent_plan` — 多意图识别计划

```
event: intent_plan
data: {
  "intents": [
    {"id": 1, "description": "查看冷站COP", "category": "monitor", "depends_on": [], "status": "pending"},
    {"id": 2, "description": "检查报警信息", "category": "alarm", "depends_on": [], "status": "pending"}
  ]
}
```

| IntentItem 字段 | 类型 | 说明 |
|-----------------|------|------|
| `id` | `number` | 意图序号 |
| `description` | `string` | 意图描述 |
| `category` | `string` | 类别：`hvac` / `monitor` / `energy` / `alarm` / `export` / `general` |
| `depends_on` | `number[]` | 依赖的意图 ID |
| `status` | `string` | 状态：`pending` / `running` / `done` / `failed` |

#### `action` — UI 动作

```
event: action
data: {"type": "navigate", "route": "/chiller-room", "params": {"site_id": "FJJB000001"}, "meta": {}}
```

#### `error` — 错误

```
event: error
data: {"error": "Agent 执行超时"}
```

#### `done` — 流结束

```
event: done
data: {}
```

收到 `done` 事件后，流式传输完成。

---

## 6. TypeScript 类型定义

将以下类型定义放入项目的 `types/agent.d.ts`：

```typescript
// ── 请求 ──────────────────────────────────────────────

/** 页面上下文 */
interface PageContext {
  current_route: string;
  site_id?: string | null;
  params: Record<string, unknown>;
  meta: Record<string, unknown>;
}

/** 请求体 */
interface AgentRequest {
  user_input: string;
  page_context?: PageContext;
}

// ── 响应 ──────────────────────────────────────────────

/** UI 动作 */
interface UIAction {
  type: string;        // "navigate" | "highlight" | "open_panel"（后续扩展）
  route: string;       // 目标路由
  params: Record<string, unknown>;
  meta: Record<string, unknown>;
}

/** /invoke 响应 */
interface AgentInvokeResponse {
  report: string;      // Markdown 格式报告
  actions: UIAction[]; // UI 动作列表
}

/** 多意图项 */
interface IntentItem {
  id: number;
  description: string;
  category: 'hvac' | 'monitor' | 'energy' | 'alarm' | 'export' | 'general';
  depends_on: number[];
  status: 'pending' | 'running' | 'done' | 'failed';
}

// ── SSE 事件 ──────────────────────────────────────────

/** thinking 事件（思考过程） */
interface SSEThinkingEvent {
  text: string;
}

/** tool_call 事件（工具调用） */
interface SSEToolCallEvent {
  name: string;
  args: Record<string, unknown>;
}

/** tool_result 事件（工具结果） */
interface SSEToolResultEvent {
  name: string;
  result: Record<string, unknown> | string;
}

/** rag_sources 事件（RAG 来源） */
interface SSERagSourcesEvent {
  query: string;
  results: string[];
}

/** text 事件（最终回答） */
interface SSETextEvent {
  text: string;
}

/** intent_plan 事件 */
interface SSEIntentPlanEvent {
  intents: IntentItem[];
}

/** error 事件 */
interface SSEErrorEvent {
  error: string;
}
```

---

## 7. Vue 组件示例

### 7.1 流式对话组件（推荐）

使用 `fetch` + `ReadableStream` 处理 POST SSE（浏览器原生 `EventSource` 只支持 GET）。

```vue
<template>
  <div class="agent-chat">
    <!-- 意图计划展示 -->
    <div v-if="intentPlan.length" class="intent-plan">
      <div v-for="intent in intentPlan" :key="intent.id" class="intent-item">
        <span class="intent-badge">{{ categoryEmoji(intent.category) }}</span>
        {{ intent.description }}
        <span :class="intent.status">{{ intent.status }}</span>
      </div>
    </div>

    <!-- 流式报告展示 -->
    <div class="report" v-html="renderedReport"></div>

    <!-- 导航动作 -->
    <div v-if="actions.length" class="actions">
      <button
        v-for="(action, i) in actions"
        :key="i"
        @click="handleAction(action)"
      >
        前往: {{ action.route }}
      </button>
    </div>

    <!-- 输入 -->
    <div class="input-area">
      <input
        v-model="userInput"
        @keyup.enter="sendMessage"
        :disabled="isStreaming"
        placeholder="输入问题..."
      />
      <button @click="sendMessage" :disabled="isStreaming || !userInput.trim()">
        {{ isStreaming ? '生成中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { marked } from 'marked';

const router = useRouter();

// ── 配置 ──────────────────────────────────────────
const API_BASE = import.meta.env.VITE_AGENT_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_AGENT_API_KEY || '';

// ── 状态 ──────────────────────────────────────────
const userInput = ref('');
const report = ref('');
const intentPlan = ref<IntentItem[]>([]);
const actions = ref<UIAction[]>([]);
const isStreaming = ref(false);

const renderedReport = computed(() => marked(report.value));

// ── 页面上下文（根据当前路由动态构建） ──────────────
function getPageContext(): PageContext {
  return {
    current_route: router.currentRoute.value.path,
    site_id: 'FJJB000001', // 从全局状态或 store 获取
    params: router.currentRoute.value.params as Record<string, unknown>,
    meta: {},
  };
}

// ── 意图类别 emoji 映射 ────────────────────────────
function categoryEmoji(category: string): string {
  const map: Record<string, string> = {
    monitor: '📡',
    hvac: '❄️',
    energy: '⚡',
    alarm: '🚨',
    export: '📊',
    general: '💬',
  };
  return map[category] || '💬';
}

// ── 发送消息（SSE 流式） ──────────────────────────
async function sendMessage() {
  if (!userInput.value.trim() || isStreaming.value) return;

  const input = userInput.value.trim();
  userInput.value = '';
  report.value = '';
  intentPlan.value = [];
  actions.value = [];
  isStreaming.value = true;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }

  try {
    const response = await fetch(`${API_BASE}/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        user_input: input,
        page_context: getPageContext(),
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // 按双换行分割 SSE 事件
      const events = buffer.split('\n\n');
      buffer = events.pop() || ''; // 最后一个可能不完整，保留

      for (const rawEvent of events) {
        if (!rawEvent.trim()) continue;

        const eventMatch = rawEvent.match(/^event: (\w+)/m);
        const dataMatch = rawEvent.match(/^data: (.+)$/m);

        if (!eventMatch || !dataMatch) continue;

        const eventType = eventMatch[1];
        const data = JSON.parse(dataMatch[1]);

        switch (eventType) {
          case 'thinking':
            // 思考过程（可选：折叠展示或丢弃）
            // thinkingText.value += data.text;
            break;
          case 'tool_call':
            // 工具调用（可选：展示调用过程）
            // toolCalls.value.push(data);
            break;
          case 'tool_result':
            // 工具结果（可选：展示原始数据）
            // toolResults.value.push(data);
            break;
          case 'rag_sources':
            // RAG 来源（可选：展示为引用）
            // ragSources.value = data;
            break;
          case 'text':
            // 最终回答（必须展示）
            report.value += data.text;
            break;
          case 'intent_plan':
            intentPlan.value = data.intents;
            break;
          case 'action':
            actions.value.push(data);
            break;
          case 'error':
            console.error('[Agent Error]', data.error);
            report.value += `\n\n❌ **错误**: ${data.error}`;
            break;
          case 'done':
            // 流结束
            break;
        }
      }
    }
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : '未知错误';
    report.value = `❌ 请求失败: ${msg}`;
  } finally {
    isStreaming.value = false;
  }
}

// ── 处理 UI 动作（页面跳转） ──────────────────────
function handleAction(action: UIAction) {
  if (action.type === 'navigate') {
    // 方式 1: Vue Router 内部跳转
    router.push({ path: action.route, query: action.params as Record<string, string> });

    // 方式 2: 如果是外部链接（福加平台路由），直接跳转
    // window.location.href = `https://aiot-fuca.com${action.route}`;
  }
}
</script>
```

### 7.2 同步调用（简单场景）

如果不需要流式效果，可使用 `/invoke`：

```typescript
async function invokeAgent(input: string): Promise<AgentInvokeResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }

  const res = await fetch(`${API_BASE}/invoke`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      user_input: input,
      page_context: {
        current_route: router.currentRoute.value.path,
        site_id: 'FJJB000001',
        params: {},
        meta: {},
      },
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
```

---

## 8. 页面跳转处理

Agent 返回的 `action` 中，`type: "navigate"` 表示建议前端跳转到某个页面。

### 8.1 UIAction 结构

```json
{
  "type": "navigate",
  "route": "/chiller-room/detail",
  "params": { "site_id": "FJJB000001", "chiller_id": "CW-01" },
  "meta": {}
}
```

### 8.2 前端处理策略

| 场景 | 处理方式 |
|------|----------|
| 内部路由 | `router.push({ path: action.route, query: action.params })` |
| 福加平台路由 | `window.location.href = \`https://aiot-fuca.com${action.route}\`` |
| 需要用户确认 | 渲染为可点击按钮，用户点击后执行跳转 |

### 8.3 已知路由列表

Agent 能识别的路由定义在 `config/routes.yaml` 中。前端无需关心路由是否合法——Agent 只会返回已注册的路由。

---

## 9. 错误处理

### 9.1 HTTP 状态码

| 状态码 | 场景 | 前端处理 |
|--------|------|----------|
| 200 | 成功 | 正常渲染 |
| 401 | API Key 无效 | 提示用户联系管理员 |
| 422 | 请求参数错误 | 检查请求体格式 |
| 500 | Agent 执行失败 | 展示 `detail` 错误信息，允许用户重试 |

### 9.2 SSE 流中的错误

流式传输过程中可能出现 `error` 事件：

```
event: error
data: {"error": "Agent 执行超时"}
```

前端应捕获此事件并向用户展示错误信息。

### 9.3 网络错误

```typescript
try {
  const response = await fetch(`${API_BASE}/stream`, { ... });
} catch (error) {
  // 网络不可达、CORS 错误、DNS 解析失败等
  showToast('无法连接 AI 服务，请检查网络');
}
```

---

## 10. 常见问题

### Q: 为什么不用 EventSource？

浏览器原生 `EventSource` 只支持 GET 请求。我们的 `/stream` 需要 POST 发送请求体，因此使用 `fetch` + `ReadableStream` 方案。

### Q: 如何处理 Markdown 渲染？

报告是标准 Markdown 格式，推荐使用 `marked` 或 `markdown-it` 库渲染：

```bash
npm install marked
```

### Q: `page_context` 可以不传吗？

可以。但不传的话 Agent 无法感知用户当前所在页面，导航建议可能不够精准。建议始终传入。

### Q: 支持对话历史吗？

当前版本每次请求是独立的，不支持多轮对话。如需对话历史，需前端维护 `messages` 数组并在 `user_input` 中拼接上下文。后续版本会原生支持。

### Q: 如何区分"Agent 建议跳转"和"直接跳转"？

`action` 事件是 Agent 的**建议**，前端可以选择：
- **自动跳转**: 收到 action 后立即执行
- **用户确认**: 渲染为按钮，用户点击后执行（推荐）
- **忽略**: 仅展示报告，不处理 action
