# EnerGraph 7 天面试突击学习计划

> 目标：在 7 天内掌握 EnerGraph 项目涉及的核心技术名词、技术栈、架构边界和面试表达。  
> 范围：除 Python 语言本身外，聚焦 LangGraph Agent、RAG、MCP、FastAPI SSE、前端对接、企业 API 集成、多智能体演进等内容。

---

## 总体目标

面试时你要做到三件事：

1. 能用 2-3 分钟清楚介绍 EnerGraph 是什么。
2. 能解释每个核心技术为什么被用在这个项目里。
3. 面对追问时能说出当前实现状态、架构边界和后续演进方向。

最重要的总纲：

> EnerGraph 是青山大模型 V3.0 的决策层 Agent，面向企业能源管理场景。它不直接做能源数值计算，而是通过 LangGraph 编排 LLM、Tools 和 Skills：先理解用户意图，再调用 REST API 或未来 MCP 工具获取数据，最后生成用户可理解的 Markdown 报告，并通过 FastAPI SSE 流式返回给前端。

---

## 第 1 天：项目全局架构与业务边界

### 学习目标

今天要能讲清：

1. EnerGraph 是什么。
2. 它在青山大模型 V3.0 五层架构里的位置。
3. 为什么 Agent 不做能源计算。
4. 当前已完成什么，未来要做什么。

### 重点知识点

- 青山大模型 V3.0 五层架构
- 决策层 Agent
- 自演化 Agent 引擎层
- PowerAI 储能调度智能体
- 意图理解、工具调度、决策解释
- 算法模型层 vs Agent 决策层
- REST API vs MCP
- 企业级落地边界

### 建议阅读

- `README.md`
- `AI_CONTEXT.md`
- `PRD.md`

### 必须掌握的一句话

> EnerGraph 不是能源计算模型，而是企业能源场景下的 Agent 编排层。它负责理解用户意图、调度外部工具和算法模型、解释结果，不直接实现预测、诊断、优化等数值计算。

### 架构图

```text
用户 / 前端
   ↓
FastAPI SSE
   ↓
LangGraph Agent 决策层
   ↓
Tools / Skills
   ↓
REST API 查询运营数据
MCP 调用算法模型层
   ↓
Markdown 报告 + UIAction
```

### 模拟面试

#### Q1：请你介绍一下这个项目。

答：

EnerGraph 是青山大模型 V3.0 中决策层和未来自演化引擎层的 Agent 实现，面向能源管理场景。它的核心定位是“编排大脑”，不是计算引擎。用户可以用自然语言查询 COP、能耗、报警、光伏、HVAC 专业知识。Agent 通过 LangGraph 编排流程，调用 Tools 获取真实数据或知识库检索结果，最后生成 Markdown 报告，并通过 FastAPI SSE 流式返回给前端。项目当前第一个业务身份是 PowerAI 储能调度智能体，未来会通过 MCP 接入光伏预测、负荷预测、储能优化等算法模型。

#### Q2：为什么说 Agent 不能自己做能源计算？

答：

这是项目的架构红线。Agent 层负责意图理解、任务拆解、工具调度和结果解释。如果在 Agent 代码里手写 COP、峰谷套利、碳排或预测算法，会导致职责混乱，也不利于算法模型独立迭代。能源计算应该由算法模型层或后端系统提供，Agent 只通过 MCP 或 REST API 获取结果。

#### Q3：这个项目当前完成到什么程度？

答：

已完成 HVAC RAG 问答、FastAPI SSE 接口、页面跳转 UIAction、福加运营数据 REST API 对接、多意图识别、Tools/Skills 分层，以及多智能体 Subgraph 基础设施。PowerAI 储能调度核心还在建设中，主要依赖后续算法团队提供 MCP 模型接口。

#### Q4：你怎么理解“决策层”？

答：

决策层不是做底层数值计算，而是把用户需求转成可执行任务，选择合适工具，融合工具返回结果，再生成可理解的业务报告。例如用户问“今天能耗和报警情况”，决策层会识别这是能耗查询和报警查询两个意图，分别调用对应工具，然后输出分段分析。

#### Q5：这个项目和普通聊天机器人有什么区别？

答：

普通聊天机器人主要依赖模型自身生成答案，而 EnerGraph 是面向企业业务系统的 Agent。它需要调用真实后端 API、遵守能源计算边界、下发前端 UI 动作、对接未来算法模型层，并且有 RAG 低置信拒答、Pydantic 强类型数据契约、SSE 流式协议和企业鉴权等工程约束。

---

## 第 2 天：LangGraph、ReAct 与 Agent 状态机

### 学习目标

今天要能讲清 EnerGraph 的主执行链路。

### 重点知识点

- LangGraph
- StateGraph
- AgentState
- Node
- Edge
- Conditional Edge
- ReAct 循环
- tool calling
- TypedDict
- Annotated reducer
- add_messages
- pending_actions

### 建议阅读

- `src/graph/state.py`
- `src/graph/builder.py`
- `src/graph/nodes.py`
- `src/graph/edges.py`

### 核心流程

```text
cognitive_parser
  ↓
判断是否有 tool_calls
  ↓                  ↓
v3_engine_router     interpreter_generator
  ↓                  ↓
回到 parser          END
```

### 三个核心节点

| 节点 | 职责 |
|---|---|
| `cognitive_parser` | LLM 理解用户意图，决定是否调用工具 |
| `v3_engine_router` | 执行工具，调用匹配的 Skill 做业务后处理 |
| `interpreter_generator` | 根据工具结果生成 Markdown 报告 |

### 必须掌握的一句话

> LangGraph 在这里的作用是把 LLM、工具调用、状态流转和报告生成组织成一个可控的状态图，而不是简单的一次性 prompt 调用。

### 模拟面试

#### Q1：为什么用 LangGraph，而不是普通 LangChain Chain？

答：

因为这个项目不是单轮问答，而是有状态、有分支、有工具调用、有循环的 Agent。LangGraph 可以把流程显式建模成状态图，包括意图解析、工具执行、报告生成，以及是否继续调用工具的条件路由。相比普通 Chain，它更适合复杂业务编排，也方便后续接入多 Agent、持久化和 Human-in-the-Loop。

#### Q2：这个项目的 ReAct 是怎么体现的？

答：

LLM 先在 `cognitive_parser` 中分析用户意图并产生 tool calls，相当于 Reason 和 Act 的决策。`v3_engine_router` 执行工具并把结果写回状态，相当于 Observation。然后图再回到 `cognitive_parser`，LLM 可以根据工具结果决定继续调用工具还是结束，最后由 `interpreter_generator` 输出报告。

#### Q3：AgentState 里为什么要用 reducer？

答：

因为状态图中某些字段不是简单覆盖，而是需要累积。例如 `messages` 要保留历史消息，所以使用 `add_messages` reducer；`pending_actions` 需要累积多个 UI 动作，所以用 `operator.add` 合并。这样可以保证状态在多节点流转时语义清晰。

#### Q4：`cognitive_parser` 和 `interpreter_generator` 都调用 LLM，它们有什么区别？

答：

`cognitive_parser` 负责理解用户意图和选择工具，绑定了 tool schemas；`interpreter_generator` 负责把工具返回的结构化数据转成用户可读的 Markdown 报告，一般不绑定工具。前者偏调度，后者偏解释。

#### Q5：如果 LLM 没有生成 tool_calls，会发生什么？

答：

条件路由会直接进入 `interpreter_generator` 或结束报告生成。如果最后一条 AI 消息本身已经是文本回答，`interpreter_generator` 可以直接把它作为 `final_report` 返回。

#### Q6：LangGraph 状态图对测试和维护有什么好处？

答：

状态图让节点职责清晰，可以单独测试状态输入和输出。比如可以 mock LLM 返回 tool calls，然后验证 `v3_engine_router` 是否执行所有工具；也可以测试 `interpreter_generator` 在多意图状态下是否生成分段报告。

---

## 第 3 天：Tools、Skills、Pydantic 与工具调用体系

### 学习目标

今天要能讲清项目为什么要拆成 Tools 和 Skills。

### 重点知识点

- Tool 原子执行层
- Skill 业务推理层
- `TOOL_REGISTRY`
- `TOOL_SCHEMAS`
- `SKILL_REGISTRY`
- BaseSkill
- Pydantic BaseModel
- JSON Schema
- function calling / tool calling
- Mock fallback
- 强类型输入输出

### 建议阅读

- `src/tools/__init__.py`
- `src/skills/__init__.py`
- `src/skills/base_skill.py`
- `src/schemas/v3_engine.py`
- `src/schemas/action_agent.py`

### Tools vs Skills

| 层 | 作用 | 示例 |
|---|---|---|
| Tools | 原子执行，不含 Prompt，负责查数据或检索知识 | `fetch_cop_data`, `query_hvac_knowledge` |
| Skills | 业务流程编排，封装 SOP、Prompt hint、后处理 | `hvac_expert`, `ui_router`, `energy_dispatch` |
| Graph Nodes | 调度 Tools 和 Skills | `v3_engine_router_node` |

### 必须掌握的一句话

> Tools 解决“怎么拿数据”，Skills 解决“拿到数据后按业务规则怎么组织”，Graph 解决“什么时候调用谁”。

### 模拟面试

#### Q1：Tools 和 Skills 有什么区别？

答：

Tools 是原子执行层，通常是确定性函数，不包含 Prompt，只负责查询数据、检索知识库或下发 UI 动作。Skills 是业务推理层，会封装某个领域的 SOP、Prompt hint 和多个工具结果的后处理。比如 `query_hvac_knowledge` 是 Tool，而 `HVACExpertSkill` 会根据检索结果判断低置信度拒答、整理引用来源等。

#### Q2：为什么工具输入输出要用 Pydantic？

答：

企业项目里工具调用结果需要稳定、可校验、可序列化。Pydantic 可以定义字段类型、默认值和描述，既方便运行时校验，也方便生成 JSON Schema 给 LLM tool calling 使用。这样可以减少裸 dict 带来的字段不一致问题。

#### Q3：`TOOL_SCHEMAS` 是干什么的？

答：

`TOOL_SCHEMAS` 是给 LLM 的工具说明，包括工具名、描述、参数类型和必填字段。LLM 根据这些 schema 判断用户问题应该调用哪个工具，并生成结构化 tool call。

#### Q4：工具执行失败怎么办？

答：

项目规范要求 Tool 函数捕获异常，并返回 `{"error": "工具名: 错误信息"}`，避免底层 API 超时或报错导致整个 Agent 崩溃。`v3_engine_router` 也会捕获工具调用异常，把错误写入工具结果。

#### Q5：为什么需要 Mock fallback？

答：

因为算法模型或真实 API 在开发、演示、测试环境中可能不可用。Mock fallback 可以保证 Agent 流程可跑通，但返回结果中应该标注 fallback 或演示数据，避免用户误以为是真实决策数据。

#### Q6：如果新增一个 Tool，应该做哪些事？

答：

需要新增 Tool 函数，定义 Pydantic 输入/输出模型或至少稳定返回结构，在 `TOOL_REGISTRY` 和 `TOOL_SCHEMAS` 注册，补充测试，必要时更新相关 Skill、Prompt、`AI_CONTEXT.md` 和 `CHANGELOG.md`。如果是算法模型工具，应通过 MCP Client 调用算法层，不能在 Agent 内部实现算法。

---

## 第 4 天：RAG、Embedding 与 HVAC 知识库

### 学习目标

今天要能讲清 RAG 如何降低幻觉。

### 重点知识点

- RAG
- Embedding
- SentenceTransformers
- BAAI/bge-small-zh-v1.5
- ChromaDB
- PersistentClient
- collection
- top_k
- distance
- confidence threshold
- low confidence
- MMR 去重
- cosine similarity
- source snippets
- 引用来源
- 拒答机制

### 建议阅读

- `src/tools/query_hvac_knowledge.py`
- `src/pipelines/rag_ingest.py`
- `src/tests/test_hvac_quality.py`

### RAG 流程

```text
用户 HVAC 问题
  ↓
Embedding 向量化
  ↓
ChromaDB 检索 Top-K
  ↓
distance 阈值判断
  ↓
MMR / cosine similarity 去重
  ↓
返回结果 + low_confidence + source_snippets
  ↓
Skill 决定回答或拒答
```

### 必须掌握的一句话

> 这个项目的 RAG 不只是“搜几条资料给 LLM”，还加了置信度阈值、低置信拒答、重复片段去重和引用来源，目的是让 HVAC 专业问答更可信。

### 模拟面试

#### Q1：这个项目的 RAG 是怎么做的？

答：

项目把 5605 条 HVAC 语料用 `BAAI/bge-small-zh-v1.5` 转成 embedding，存入本地 ChromaDB。用户提问时，`query_hvac_knowledge` 会检索 top_k 相关片段，同时返回距离、系统类型和来源摘要。然后根据 top-1 distance 判断是否低置信度，如果超过阈值就触发拒答，避免 LLM 编造。

#### Q2：为什么要做 low_confidence 拒答？

答：

HVAC 是专业领域，如果知识库没有相关内容，让 LLM 自己猜会带来错误建议，甚至影响设备安全。因此当检索结果距离过大、相关度不足时，系统应该明确说明知识库暂无相关信息，而不是生成看似专业但不可靠的答案。

#### Q3：MMR 去重解决什么问题？

答：

向量检索经常会返回多个高度相似的片段。如果直接把这些片段都给 LLM，会浪费上下文，也可能让回答重复。项目用余弦相似度判断候选片段之间是否过于相似，超过阈值就剔除重复项，保留多样化来源。

#### Q4：ChromaDB 在这里的作用是什么？

答：

ChromaDB 是本地持久化向量数据库，用来存储 HVAC 语料的 embedding 和 metadata。查询时它负责根据用户问题的 embedding 找出最相近的知识片段。

#### Q5：Embedding 模型为什么选 bge-small-zh-v1.5？

答：

它是中文优化的 embedding 模型，适合中文 HVAC 专业问答场景。本地模型也便于企业内网部署，减少外部依赖。后续规划升级到 BGE-M3、BM25 混合检索和 reranker，提高召回和排序质量。

#### Q6：RAG 和微调有什么区别？

答：

RAG 是运行时检索外部知识，把相关内容提供给模型生成答案；微调是把知识或行为模式训练进模型参数。这个项目的 HVAC 知识需要可更新、可引用、可拒答，所以 RAG 更合适。未来如果要提升固定任务风格或意图识别能力，可以再考虑 SFT。

---

## 第 5 天：FastAPI、SSE 与前端对接

### 学习目标

今天要能讲清后端如何把 Agent 输出流式推给前端。

### 重点知识点

- FastAPI
- uvicorn
- `/health`
- `/invoke`
- `/stream`
- SSE
- StreamingResponse
- text/event-stream
- CORS
- Bearer Token
- HTTPBearer
- JSONResponse
- Vue3
- Vite
- TypeScript
- Vue Router
- fetch + ReadableStream
- Markdown 渲染
- UIAction

### 建议阅读

- `src/services/api.py`
- `docs/frontend_integration_guide.md`
- `src/frontend/app.py`

### SSE 事件类型

| 事件 | 作用 |
|---|---|
| `thinking` | Agent 思考过程 |
| `tool_call` | 工具调用信息 |
| `tool_result` | 工具返回结果 |
| `rag_sources` | RAG 引用来源 |
| `text` | 最终回答文本 |
| `intent_plan` | 多意图计划 |
| `action` | UI 跳转动作 |
| `error` | 错误 |
| `done` | 结束 |

### 必须掌握的一句话

> `/invoke` 适合同步返回完整结果，`/stream` 通过 SSE 按事件推送 Agent 的思考、工具调用、最终文本和 UI 动作，用户体验更好，也方便前端展示过程。

### 模拟面试

#### Q1：为什么项目要用 SSE？

答：

LLM 生成内容和工具调用可能耗时，如果等全部完成再返回，用户体验会比较差。SSE 可以把思考过程、工具调用、最终文本逐步推给前端，实现类似打字机效果。同时它比 WebSocket 简单，适合服务端单向推送场景。

#### Q2：为什么前端不用 EventSource？

答：

浏览器原生 EventSource 只支持 GET，而项目的 `/stream` 需要 POST 请求体传入 `user_input` 和 `page_context`。所以前端用 `fetch + ReadableStream` 读取 `text/event-stream`。

#### Q3：`/invoke` 和 `/stream` 有什么区别？

答：

`/invoke` 是同步接口，执行完整个 graph 后返回 `{report, actions}`。`/stream` 是流式接口，边执行边推送 SSE 事件，包括 `thinking`、`tool_call`、`tool_result`、`text`、`action` 等。生产场景推荐 `/stream`。

#### Q4：UIAction 是什么？

答：

UIAction 是 Agent 下发给前端的结构化动作，目前主要是页面跳转。比如用户问“查看报警”，Agent 查询报警数据后可以返回一个 `action` 事件，内容是 `{type: "navigate", route: "/alarm/realtime", params: {...}}`，前端可以渲染为按钮或自动跳转。

#### Q5：CORS 和 Bearer Token 在这里有什么作用？

答：

CORS 用于允许前端域名访问 FastAPI 服务。Bearer Token 是可选 API 鉴权机制，生产环境配置 `API_KEY` 后，前端请求需要带 `Authorization: Bearer <key>`，避免接口裸露。

#### Q6：为什么要把 `thinking`、`tool_call`、`text` 分成不同事件？

答：

这样前端可以做差异化展示。最终回答必须展示，工具调用和思考过程可以折叠或丢弃，RAG 来源可以作为引用展示，UIAction 可以渲染成跳转按钮。事件粒度越清晰，前端体验越可控。

---

## 第 6 天：MCP、REST API 与企业系统集成

### 学习目标

今天要能讲清“哪些走 MCP，哪些走 REST”。

### 重点知识点

- MCP
- MCP Server
- MCP Client
- JSON Schema
- HTTP + SSE
- REST API
- 福加 Java 后端
- httpx
- Token 自动刷新
- RSA
- PKCS1_v1_5
- tenant_id
- 401 retry
- `.env`
- site_mapping
- 12-Factor 配置

### 建议阅读

- `MCP_INTERFACE_SPEC.md`
- `src/tools/java_backend.py`
- `src/utils/fuca_token_refresher.py`
- `config/site_mapping.yaml`

### MCP 与 REST 边界

| 类型 | 接入方式 | 示例 |
|---|---|---|
| 算法模型 | MCP | 光伏预测、电负荷预测、储能调度优化 |
| 运营数据 | REST API | COP、能耗、报警、碳排、光伏、设备排名 |

### MCP 规划中的 9 个模型

- `predict_load`
- `predict_solar`
- `predict_electricity_price`
- `predict_cooling_load`
- `predict_carbon`
- `diagnose_equipment`
- `diagnose_room_efficiency`
- `optimize_cooling`
- `optimize_dispatch`

### 必须掌握的一句话

> MCP 用来标准化接入算法模型层，REST API 用来复用已有 Java 运营数据接口；两者都被封装成 Tools，对上层 Agent 保持统一调用方式。

### 模拟面试

#### Q1：MCP 在这个项目中解决什么问题？

答：

MCP 用来解耦 Agent 决策层和算法模型层。算法团队可以把预测、诊断、优化模型封装为 MCP Server，并用 JSON Schema 暴露工具接口。Agent 通过 MCP Client 调用，不需要依赖算法模型内部实现。这样模型可以独立部署、升级和热插拔。

#### Q2：为什么福加运营数据不用 MCP，而是 REST API？

答：

因为福加已有 Java 后端监控系统，COP、能耗、报警、光伏等运营数据已经通过 REST API 暴露。对这类已有业务系统，直接 REST 对接更现实。MCP 主要用于未来算法模型层的标准化工具调用。

#### Q3：Token 自动刷新怎么做？

答：

福加 API 如果返回 401，工具层会用线程锁保护刷新流程，调用 `fuca_token_refresher` 重新登录获取 Token。登录前会用福加前端 RSA 公钥对密码做 PKCS1v15 加密，然后调用认证接口获取新 Token，并更新进程缓存和 `.env`。

#### Q4：`site_mapping.yaml` 是干什么的？

答：

它把 Agent 层的通用 `site_id` 映射成 Java 后端真实接口所需的设备 ID、设备 code、点位名称、分类编码等参数。这样用户只需要传站点 ID，工具内部负责转换具体后端参数。

#### Q5：为什么 API 地址和密钥放在 `.env`？

答：

这些是部署环境相关配置，不应该写死在代码或提交到仓库。通过 `.env` 和环境变量覆盖 YAML 配置，更符合 12-Factor App 原则，也降低泄露生产地址和密钥的风险。

#### Q6：MCP 接口失败时 Agent 应该怎么处理？

答：

应该按错误码区分处理。例如 `model_unavailable` 提示算法模型暂未接入，`insufficient_data` 提示需要更多数据，`timeout` 可以重试一次，`invalid_input` 提示用户修正输入。不能自己补算结果，也不能编造算法输出。

---

## 第 7 天：多智能体演进、可观测性、测试与面试整合

### 学习目标

最后一天要把项目讲成“可演进的企业 Agent 平台”，而不是一堆功能点。

### 重点知识点

- 多智能体 Subgraph
- BaseAgent
- AGENT_REGISTRY
- Agent Dispatcher
- PowerAI
- HVAC Expert Agent
- UI Router Agent
- Prompt 多文件管理
- LangSmith
- pytest
- pytest-asyncio
- ASGITransport
- Mock 测试
- PostgresSaver
- Human-in-the-Loop
- BGE-M3
- BM25
- Reranker
- Milvus
- Neo4j
- GraphRAG
- Redis
- A2A
- NeMo Guardrails

### 建议阅读

- `docs/REFACTORING_SUMMARY.md`
- `TEAM_COLLABORATION_GUIDE.md`
- `src/graph/agents/base_agent.py`
- `src/graph/agents/__init__.py`

### 当前真实状态

| 能力 | 状态 |
|---|---|
| Skill 调度 | 当前活跃主流程 |
| Agent Subgraph | 基础设施完成 |
| HVAC/UI Router/PowerAI 子图 | 已有骨架 |
| 主图 Agent Dispatcher | 尚未完全接入 |
| PowerAI MCP 调度 | 待算法模型接口就绪 |

### 必须掌握的一句话

> 项目当前处在从 Skill 调度向多 Agent Subgraph 架构演进的阶段，基础设施已完成，但主图还没有完全切到 Agent Dispatcher；这个状态说明项目考虑了未来多人协作和业务扩展。

### 模拟面试

#### Q1：这个项目的多智能体架构做到哪一步了？

答：

当前已经完成多智能体 Subgraph 的基础设施，包括 `BaseAgent`、`AGENT_REGISTRY`，以及 HVAC、UI Router、PowerAI 三个 Agent 子图骨架。但主图当前仍主要通过 Skill 调度执行，Agent Dispatcher 还没有完全接入。也就是说，多 Agent 架构已经具备扩展基础，但还处在迁移阶段。

#### Q2：为什么要从 Skill 演进到 Agent Subgraph？

答：

Skill 适合封装相对简单的业务流程，比如一个工具链加后处理。但当某个领域需要独立状态、多步骤流转、独立 ReAct 循环，或者多人并行开发时，Agent Subgraph 更合适。每个 Agent 有自己的目录、状态、Prompt 和测试，能降低协作冲突。

#### Q3：Prompt 为什么要拆成多个 YAML 文件？

答：

单文件 Prompt 容易在多人协作时冲突，也不利于按业务域维护。拆成 `_shared.yaml`、`main_graph.yaml`、`hvac_expert.yaml`、`ui_router.yaml`、`powerai.yaml` 后，每个 Agent 可以独立调优 Prompt，同时共享回答原则和跳转规则。

#### Q4：LangSmith 在项目里有什么价值？

答：

LangSmith 用于追踪 LLM 调用、工具调用、状态流转和错误，帮助定位 Agent 为什么选择某个工具、哪个节点耗时、哪里出现幻觉或失败。对企业级 Agent 来说，可观测性很重要，否则线上问题很难复盘。

#### Q5：项目测试策略是什么？

答：

Tool 层测试应该 mock 外部 API，不依赖真实 Key 或真实服务。Skill 测试关注工具结果后处理。API 测试可以用 ASGITransport 测 FastAPI 端点。新增 Tool 要覆盖正常输入、边界值和非法输入；修 bug 要先写复现测试。

#### Q6：如果让你继续推进这个项目，你会先做什么？

答：

我会优先做三件事：第一，和算法团队确认 MCP 接口字段，接入 PowerAI 的 `predict_load`、`predict_solar`、`optimize_dispatch`；第二，把主图从 Skill 调度逐步升级为 Agent Dispatcher；第三，补齐 LangGraph 持久化和 LangSmith 追踪，方便后续 Human-in-the-Loop 和生产排障。

---

## 最终 2 分钟面试总答案

可以背这个版本：

> EnerGraph 是青山大模型 V3.0 的决策层 Agent，面向企业能源管理场景。它基于 LangGraph 实现 ReAct 状态图，主流程是 `cognitive_parser → v3_engine_router → interpreter_generator`。用户输入后，LLM 先理解意图并选择工具，工具层通过 REST API 查询福加运营数据，未来通过 MCP 调用算法模型层，最后由解释节点生成 Markdown 报告，并通过 FastAPI SSE 流式返回给 Vue 前端。
>
> 项目里比较关键的设计是 Tools 和 Skills 分层：Tools 是原子执行，不含 Prompt；Skills 负责业务 SOP 和工具结果后处理。HVAC 问答使用 BGE embedding 和 ChromaDB 做 RAG，并通过 distance 阈值、低置信拒答、MMR 去重和引用来源控制幻觉。当前项目还完成了多意图识别、UIAction 页面跳转、福加 REST API 和 Token 自动刷新。
>
> 架构上，项目正在从 Skill 调度演进到多智能体 Subgraph，已经有 BaseAgent 和 AGENT_REGISTRY，HVAC、UI Router、PowerAI 都有子图骨架，但主图 Agent Dispatcher 还在后续建设中。整体原则是 Agent 不做能源数值计算，只做意图理解、工具调度和决策解释。

---

## 3 天应急压缩版

如果时间不够，按这个顺序背：

### 第 1 天

- 项目定位
- 五层架构
- Agent 不做能源计算
- LangGraph 主流程

### 第 2 天

- Tools vs Skills
- RAG 流程
- FastAPI SSE
- 前端 UIAction

### 第 3 天

- MCP vs REST
- Token 自动刷新
- 多 Agent 演进
- 最终 2 分钟总答案

---

## 面试前检查清单

- 能否 2 分钟讲清项目？
- 能否画出 `cognitive_parser → v3_engine_router → interpreter_generator`？
- 能否解释 Agent 为什么不能手写能源计算？
- 能否说明 Tools 和 Skills 的区别？
- 能否讲清 RAG 的低置信拒答和 MMR 去重？
- 能否解释 `/invoke` 和 `/stream` 的区别？
- 能否说明为什么 POST SSE 要用 `fetch + ReadableStream`？
- 能否解释 MCP 和 REST API 的边界？
- 能否说出当前多 Agent 架构的真实状态？
- 能否给出后续推进优先级？
