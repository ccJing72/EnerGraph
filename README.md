# EnerGraph — 青山 V3 多模态调度 Agent

基于 LangGraph 的企业级能源管理 AI Agent，定位为青山大模型 V3（QingShan-TimeDiT + PhysicsAI）五层架构的**第 0 层认知交互层**。集成 HVAC 专业知识库，支持自然语言问答、能源调度分析，并通过 FastAPI SSE 接口向福加监控平台前端下发页面跳转控制信号。

## 功能

- **HVAC 专家问答**：5613 条暖通空调专业语料（规范查询、能效计算、故障诊断、节能优化），RAG 检索驱动，低置信度自动拒答
- **Action Agent**：理解自然语言意图 → 调用 Java 后端监控 API → 流式返回文字总结 + 页面跳转信号
- **ReAct 循环**：cognitive_parser → v3_engine_router（工具执行）→ interpreter_generator（报告生成），token 级流式输出
- **多 LLM 支持**：DeepSeek V4 / OpenAI / Claude，`LLM_PROVIDER` 环境变量一键切换

## 快速开始

```bash
git clone https://github.com/Webr1ng/EnerGraph.git
cd EnerGraph
conda create -n energraph python=3.11 -y
conda activate energraph
pip install -r requirements.txt
```

配置环境变量：

```bash
cp .env.example .env
# 编辑 .env，至少填入：
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=your_key
```

初始化 HVAC 知识库（首次运行，约 2-5 分钟）：

```bash
python -m src.pipelines.rag_ingest
```

启动演示前端：

```bash
streamlit run src/frontend/app.py --server.headless true
```

启动 API 服务（Phase 2 完成后）：

```bash
uvicorn src.services.api:app --reload
```

## 项目结构

```
EnerGraph/
├── config/
│   └── agent_config.yaml          # 默认配置（.env 优先覆盖）
├── docs/                          # 各阶段开发规划
│   ├── plan_phase2_action_agent.md
│   ├── plan_phase3_rag.md
│   ├── plan_phase4_realapi.md
│   └── plan_phase5_voice.md
├── src/
│   ├── config/
│   │   ├── settings.py            # 统一配置加载（LLM_PROVIDER 切换）
│   │   └── prompts.yaml           # System Prompt 模板（外部化）
│   ├── schemas/
│   │   └── v3_engine.py           # Pydantic 模型（Tool I/O 强类型）
│   ├── tools/                     # V3 引擎工具（Mock + RAG）
│   ├── graph/                     # LangGraph 状态机
│   │   ├── state.py               # AgentState TypedDict
│   │   ├── nodes.py               # 三个节点函数
│   │   ├── edges.py               # 条件路由
│   │   └── builder.py             # graph 全局单例
│   ├── services/
│   │   └── api.py                 # FastAPI（Phase 2 实现中）
│   ├── pipelines/
│   │   └── rag_ingest.py          # HVAC 语料入库
│   └── frontend/
│       └── app.py                 # Streamlit 演示前端
├── data/hvac_knowledge/           # ChromaDB 向量库（rag_ingest 后生成）
├── CLAUDE.md                      # AI 协作规范（每次 session 自动加载）
└── AI_CONTEXT.md                  # 项目单点真相
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 核心框架 | LangGraph 1.2，ReAct 状态图 |
| LLM | DeepSeek V4 / OpenAI / Claude（`LLM_PROVIDER` 切换） |
| Embedding | ChromaDB ONNX（all-MiniLM-L6-v2，本地，零 API 依赖） |
| 向量库 | ChromaDB 本地持久化，5613 条 HVAC 语料 |
| API 层 | FastAPI + SSE 流式（Phase 2） |
| 前端对接 | Vue3 + Vite + TypeScript（福加监控平台） |
| 演示前端 | Streamlit 1.39 |
| 可观测性 | LangSmith（`LANGCHAIN_TRACING_V2=true`） |
| Python | 3.11 |

## 开发阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | ReAct 循环 + HVAC RAG + DeepSeek V4 + 流式前端 | ✅ 完成 |
| Phase 2 | Action Agent：FastAPI SSE + UIAction 跳转信号 + Java 后端工具 | 进行中 |
| Phase 3 | RAG 质量优化（置信度阈值 + 拒答 + 引用来源） | 待开始 |
| Phase 4 | Mock → 真实预测 API（TimeDiT / PhysicsAI / AIDC） | 待开始 |
| Phase 5 | 语音助手（Whisper STT + TTS） | 待开始 |

## 开发规范

详见 [CLAUDE.md](CLAUDE.md)。核心原则：

- Agent **禁止**手写能源计算，所有计算通过 Tools 调用
- `AgentState` 用 `TypedDict + Annotated`，Tool I/O 用 Pydantic BaseModel
- Prompt 外部化至 `src/config/prompts.yaml`，禁止硬编码
- 每个 `.py` 文件必须有模块 docstring（层 / 依赖 / 对接引擎）
- 提交格式：`[模块] 动词短语`，禁止 `git add .`

## 许可

内部项目，未公开授权。© 2026 南京福加智能科技有限公司
