# 青山 V3 多模态调度 Agent — 项目上下文

## 项目状态
**当前阶段**: Phase 1 完成 ✅ | Phase 2 待开始  
**最后更新**: 2026-05-21  
**项目性质**: 企业级落地方案，南京福加智能科技有限公司内部项目  
**GitHub**: https://github.com/Webr1ng/EnerGraph.git  
**GitLab**: git@172.16.3.160:ai-group/energraph.git  
**Python 环境**: conda `energraph` / Python 3.11（LangGraph 要求 ≥3.10）

---

## 1. 项目背景与定位

### 1.1 公司背景

**南京福加智能科技有限公司**是一家专注于暖通控制系统的企业，主要产品为能碳管理平台（已在福加本厂部署）。平台覆盖：冷水机房监控、光储协同、负荷预测、主动寻优（强化学习）、数据公信（区块链上链）等模块。

本项目是福加能碳管理平台的 **AI Agent 层**，最终目标是为福加负责建设的各类厂区、地铁站、商业建筑提供智能化暖通调度与能源管理服务。

### 1.2 Agent 定位：V3 第 0 层认知交互层

本项目是青山大模型 V3（QingShan-TimeDiT + PhysicsAI）五层架构的**第 0 层**。Agent 不参与热力学运算，而是作为：

| 角色 | 职责 |
|------|------|
| **业务意图翻译官** | 自然语言 / ERP JSON → 物理约束矩阵 |
| **引擎调度员** | 触发 PhysicsAI / TimeDiT / AIDC 工具 |
| **决策解说员** | 物理残差 / SOC 曲线 → Markdown 报告 |

### 1.3 最终目标

```
当前（Phase 1）: HVAC 专家问答 + ReAct 循环演示
      ↓
Phase 2: 暴露 FastAPI，供福加平台前端调用
      ↓
Phase 3: RAG 质量优化，减少幻觉
      ↓
Phase 4: 接入真实预测算法（TimeDiT 负荷预测、PhysicsAI 物理验证、AIDC 液冷）
      ↓
Phase 5: 语音助手（语音输入 + 语音输出）
      ↓
长期: 多站点管理（福加本厂 → 各厂区 / 地铁站 / 商业建筑）
```

---

## 2. 技术架构

### 2.1 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 核心框架 | LangGraph 1.2 | ReAct 状态图，支持 token 级流式 |
| LLM | DeepSeek V4 / OpenAI / Claude | `LLM_PROVIDER` 环境变量一键切换 |
| Embedding | ChromaDB ONNX（all-MiniLM-L6-v2） | 本地模型，零外部 API 依赖 |
| 向量库 | ChromaDB（本地持久化） | `data/hvac_knowledge/`，5613 条 HVAC 语料 |
| 数据验证 | Pydantic 2.x | Tool I/O 强类型；AgentState 用 TypedDict |
| 可观测性 | LangSmith | 执行链路追踪（`LANGCHAIN_TRACING_V2=true`） |
| 前端（演示） | Streamlit 1.39 | token 级流式展示 ReAct 思考过程 |
| 配置 | python-dotenv + PyYAML | Prompt 外部化，环境隔离 |
| Python | 3.11 | |

### 2.2 LangGraph ReAct 状态图

```
用户输入
    │
    ▼
┌─────────────────────┐
│  cognitive_parser   │  LLM 分析意图 → 选择工具（streaming=True）
└──────────┬──────────┘
           │
    有 tool_calls?
    ┌──YES──┴──NO──┐
    ▼              ▼
┌──────────────┐  ┌──────────────────────┐
│v3_engine_    │  │ interpreter_generator│ → END
│router        │  │ 生成 Markdown 报告    │
│（执行工具）   │  └──────────────────────┘
└──────┬───────┘
       │
       └──→ cognitive_parser（循环，最多 max_iterations 次）
```

**流式输出**: `graph.stream(stream_mode=["updates","messages"])` 逐 token 推送，前端实时展示思考过程。

### 2.3 LLM 供应商切换

`.env` 中设置 `LLM_PROVIDER`，无需改代码：

```ini
LLM_PROVIDER=deepseek   # deepseek-v4-pro / deepseek-v4-flash
# LLM_PROVIDER=openai   # gpt-4o
# LLM_PROVIDER=anthropic # claude-sonnet-4-6
```

DeepSeek V4 注意：`thinking` 模式已禁用（`extra_body={"thinking":{"type":"disabled"}}`），避免 tool calling 时 `reasoning_content` 报错。

---

## 3. 目录结构

```
EnerGraph/
├── CLAUDE.md                  # 协作规范（每次 session 自动加载，优先级最高）
├── AI_CONTEXT.md              # 本文件（项目单点真相）
├── .env.example               # 环境变量模板
├── requirements.txt
├── config/
│   └── agent_config.yaml      # 默认配置（.env 优先覆盖）
├── docs/                      # 各阶段开发 plan（每个 session 只读对应 plan）
│   ├── plan_phase2_api.md     # FastAPI REST API
│   ├── plan_phase3_rag.md     # RAG 质量优化
│   ├── plan_phase4_realapi.md # 真实 API 对接
│   └── plan_phase5_voice.md   # 语音助手
└── src/
    ├── config/
    │   ├── settings.py        # 配置加载（LLM_PROVIDER / DEEPSEEK_MODEL 等）
    │   └── prompts.yaml       # System Prompt 模板（外部化，禁止硬编码）
    ├── schemas/
    │   └── v3_engine.py       # Pydantic 模型：ConstraintMatrix / TimeDiTForecast /
    │                          #   PhysicsResidual / AIDCCoolingStatus / HVACKnowledgeResult
    ├── tools/                 # V3 引擎工具（Mock + RAG）
    │   ├── __init__.py        # TOOL_REGISTRY + TOOL_SCHEMAS（LLM function calling 用）
    │   ├── parse_intent.py    # 意图解析 → ConstraintMatrix
    │   ├── query_timedit.py   # TimeDiT 时序预测（Mock）
    │   ├── verify_physics.py  # PhysicsAI 物理验证（Mock）
    │   ├── fetch_aidc_cooling.py # AIDC 液冷状态（Mock）
    │   └── query_hvac_knowledge.py # HVAC RAG 检索（真实，ChromaDB）
    ├── graph/
    │   ├── state.py           # AgentState（TypedDict + Annotated add_messages）
    │   ├── nodes.py           # 三个节点函数
    │   ├── edges.py           # should_continue 条件路由
    │   └── builder.py         # 图编译，graph 全局单例
    ├── pipelines/
    │   └── rag_ingest.py      # HVAC 语料入库（5613 条，ONNX Embedding）
    ├── services/
    │   └── api.py             # 【Phase 2】FastAPI 占位
    ├── frontend/
    │   └── app.py             # Streamlit 演示前端（token 级流式）
    └── tests/
        ├── test_tools.py
        └── test_graph.py
```

---

## 4. 工具注册表

| 工具名 | 状态 | 对接引擎 | 输出模型 |
|--------|------|----------|----------|
| `parse_business_intent` | Mock | N/A（纯 LLM） | `ConstraintMatrix` |
| `query_timedit_forecast` | Mock | QingShan-TimeDiT | `TimeDiTForecast` |
| `verify_physics_consistency` | Mock | PhysicsAI | `PhysicsResidual` |
| `fetch_aidc_cooling_status` | Mock | AIDC 智算中心 | `AIDCCoolingStatus` |
| `query_hvac_knowledge` | **真实** | ChromaDB RAG | `HVACKnowledgeResult` |

**HVAC 知识库**: 5613 条语料，覆盖规范查询、能效计算、故障诊断、节能优化，含地铁站/商业项目专项。

---

## 5. 开发阶段与工作顺序

| 阶段 | 内容 | 状态 | Plan |
|------|------|------|------|
| Phase 1 | ReAct 循环 + HVAC RAG + DeepSeek V4 + 流式前端 | ✅ 完成 | — |
| Phase 2 | FastAPI REST API（/invoke + /stream SSE） | 待开始 | `docs/plan_phase2_api.md` |
| Phase 3 | RAG 质量优化（相关度阈值 + 拒答 + 引用来源） | 待开始 | `docs/plan_phase3_rag.md` |
| Phase 4 | Mock → 真实预测 API（TimeDiT / PhysicsAI / AIDC） | 待开始 | `docs/plan_phase4_realapi.md` |
| Phase 5 | 语音助手（Whisper STT + TTS） | 待开始 | `docs/plan_phase5_voice.md` |

**阶段顺序可以调整**，plan 文件相互独立。Phase 4 依赖算法团队 API 就绪，可与 Phase 3 并行。Phase 5 只依赖 Phase 2（API 层）。

**每个 session 开发流程**:
```
读 CLAUDE.md（自动）+ AI_CONTEXT.md + docs/plan_phaseX.md
→ 执行一个子任务（T1/T2/...）
→ commit
→ session 结束
```

---

## 6. 变更日志（近期）

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-05-21 | 规划 Phase 2-5，创建 docs/plan_*.md，精简并重写 AI_CONTEXT | 魏博源 |
| 2026-05-21 | token 级流式前端（stream_mode=messages），streaming=True | 魏博源 |
| 2026-05-18 | LLM_PROVIDER 切换、DeepSeek V4 适配、ONNX Embedding | 魏博源 |
| 2026-05-18 | HVAC RAG 集成（5613 条）、ReAct 循环、对话前端 | 魏博源 |
| 2026-05-14 | Phase 1 重构：V3 架构全量实现 | 魏博源 |

> 完整历史见 `git log`。

---

**下一步**: 开始 Phase 2 → 读 `docs/plan_phase2_api.md`
