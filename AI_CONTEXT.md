# 青山 V3 多模态调度 Agent — 项目上下文

## 项目状态
**当前阶段**: Phase 1 完成 ✅ | Phase 2 待开始  
**最后更新**: 2026-05-21  
**GitHub**: https://github.com/Webr1ng/EnerGraph.git | **GitLab**: git@172.16.3.160:ai-group/energraph.git  
**Python 环境**: conda `energraph` / Python 3.11

---

## 1. 定位

V3 五层架构的**第 0 层（认知交互层）**。Agent 不做计算，只做：
- **输入端**：自然语言 → 物理约束矩阵
- **调度端**：触发 PhysicsAI / TimeDiT / AIDC 工具
- **输出端**：物理数据 → Markdown 报告

---

## 2. 技术栈

| 类别 | 技术 |
|------|------|
| 核心框架 | LangGraph 1.2 |
| LLM | DeepSeek V4 / OpenAI / Claude（`LLM_PROVIDER` 切换） |
| Embedding | ChromaDB ONNX 本地模型（零 API 依赖） |
| 数据验证 | Pydantic 2.x（Tool I/O）+ TypedDict（AgentState） |
| 前端 | Streamlit（演示用，后续替换为 FastAPI） |
| Python | 3.11 |

**LangGraph 状态图**:
```
cognitive_parser → (有工具调用) → v3_engine_router → cognitive_parser (循环)
                → (无工具调用) → interpreter_generator → END
```

---

## 3. 目录结构

```
EnerGraph/
├── CLAUDE.md                  # 协作规范（每次 session 自动加载）
├── AI_CONTEXT.md              # 本文件
├── config/agent_config.yaml   # 默认配置（.env 优先覆盖）
├── docs/                      # 各阶段开发 plan（每个 session 只读对应 plan）
│   ├── plan_phase2_api.md
│   ├── plan_phase3_rag.md
│   ├── plan_phase4_realapi.md
│   └── plan_phase5_voice.md
└── src/
    ├── config/settings.py     # 配置加载（LLM_PROVIDER / DEEPSEEK_MODEL 等）
    ├── config/prompts.yaml    # System Prompt 模板
    ├── schemas/v3_engine.py   # Pydantic 模型（见文件）
    ├── tools/                 # 5 个工具（4 个 Mock + 1 个 RAG）
    ├── graph/                 # LangGraph 节点/边/状态/builder
    ├── pipelines/rag_ingest.py
    ├── services/api.py        # 【Phase 2】FastAPI 占位
    ├── frontend/app.py        # Streamlit 演示前端
    └── tests/
```

---

## 4. 工具注册表

| 工具名 | 状态 | 对接 |
|--------|------|------|
| `parse_business_intent` | Mock | N/A |
| `query_timedit_forecast` | Mock | QingShan-TimeDiT |
| `verify_physics_consistency` | Mock | PhysicsAI |
| `fetch_aidc_cooling_status` | Mock | AIDC 智算中心 |
| `query_hvac_knowledge` | **真实** | ChromaDB RAG（5613 条） |

数据模型详见 `src/schemas/v3_engine.py`。

---

## 5. 开发阶段

| 阶段 | 内容 | 状态 | Plan 文件 |
|------|------|------|-----------|
| Phase 1 | ReAct 循环 + HVAC RAG + DeepSeek V4 | ✅ 完成 | — |
| Phase 2 | FastAPI REST API（/invoke + /stream） | 待开始 | `docs/plan_phase2_api.md` |
| Phase 3 | RAG 质量优化 + 减少幻觉 | 待开始 | `docs/plan_phase3_rag.md` |
| Phase 4 | Mock 工具 → 真实 API 对接 | 待开始 | `docs/plan_phase4_realapi.md` |
| Phase 5 | 语音助手（STT/TTS） | 待开始 | `docs/plan_phase5_voice.md` |

**每个 session 开发流程**：读 `CLAUDE.md` + `AI_CONTEXT.md` + 对应 plan → 执行一个子任务 → commit → 结束

---

## 6. 变更日志（近期）

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-05-21 | 规划 Phase 2-5，创建 docs/plan_*.md，精简 AI_CONTEXT | 魏博源 |
| 2026-05-18 | LLM_PROVIDER 切换、DeepSeek V4 适配、ONNX Embedding、token 级流式前端 | 魏博源 |
| 2026-05-18 | HVAC RAG 集成（5613 条）、ReAct 循环、对话前端 | 魏博源 |
| 2026-05-14 | Phase 1 重构：V3 架构全量实现 | 魏博源 |

> 完整历史见 git log。

---

**下一步**: 开始 Phase 2 → 读 `docs/plan_phase2_api.md`
