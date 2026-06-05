# EnerGraph — 青山 V3 多模态调度 Agent

基于 LangGraph 的企业级能源管理 AI Agent，定位为青山大模型 V3（QingShan-TimeDiT + PhysicsAI）五层架构的**第 0 层认知交互层**。集成 HVAC 专业知识库，支持自然语言问答、能源调度分析，并通过 FastAPI SSE 接口向福加监控平台前端下发页面跳转控制信号。

## 功能

- **HVAC 专家问答**：5605 条暖通空调专业语料（规范查询、能效计算、故障诊断、节能优化），RAG 检索驱动，低置信度自动拒答，引用来源标注
- **RAG 质量优化**：distance 阈值过滤 + 余弦相似度 MMR 去重（0.98 阈值）+ source_snippets 引用来源
- **多意图识别**：单输入多意图自动拆分，cognitive_parser 并行/串行调度，interpreter 分段报告输出
- **Action Agent**：理解自然语言意图 → 调用 Java 后端监控 API → 流式返回文字总结 + 页面跳转信号
- **Skills 分层架构**：BaseSkill 抽象基类统一接口，Skills（业务推理层）与 Tools（原子执行层）分离，v3_engine_router 通过统一调度分发
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
│   ├── agent_config.yaml          # 默认配置（.env 优先覆盖）
│   └── routes.yaml                # 前端路由注册表（24 可访问 + 10 受限）
├── scripts/
│   └── fix_qa_mismatch.py         # 数据修复工具
├── docs/                          # 各阶段开发规划
│   ├── plan_skills_refactor.md    # Skills 架构重组方案
│   ├── plan_skills_base_class.md  # BaseSkill 基类方案
│   ├── plan_phase2_action_agent.md
│   ├── plan_phase3_rag.md
│   ├── plan_phase4_realapi.md
│   ├── plan_phase5_voice.md
│   ├── plan_phase6_visualization_export.md
│   ├── plan_phase7_multi_intent.md
│   ├── plan_fix_navigation_routes.md   # 路由修复计划
│   ├── frontend_backend_alignment.md   # 前后端对接文档
│   └── sync_server.md                  # 服务器同步指南
├── src/
│   ├── config/
│   │   ├── settings.py            # 统一配置加载（LLM_PROVIDER 切换）
│   │   └── prompts.yaml           # 所有 System Prompt 集中管理
│   ├── schemas/
│   │   ├── v3_engine.py           # Pydantic 模型（Tool I/O + IntentItem）
│   │   └── action_agent.py        # PageContext / UIAction / COPData 等
│   ├── skills/                    # 业务技能层（Prompt + SOP + Tools 编排）
│   │   ├── base_skill.py          # BaseSkill 抽象基类（execute/生命周期钩子）
│   │   ├── hvac_expert_skill.py   # HVAC 专家问答（置信度判断/拒答/引用）
│   │   ├── energy_dispatch_skill.py
│   │   ├── ui_router_skill.py     # 页面跳转控制（RouteRegistry 路由匹配）
│   │   └── v3_interpreter_skill.py
│   ├── tools/                     # 原子执行层（确定性函数，不含 Prompt）
│   │   ├── query_hvac_knowledge.py # HVAC RAG 检索（ChromaDB + 去重 + 阈值）
│   │   ├── parse_intent.py        # 意图解析 → ConstraintMatrix
│   │   ├── navigate_to_page.py    # 页面跳转 → UIAction
│   │   └── java_backend.py        # Java 后端工具 Mock（COP/能耗/报警）
│   ├── graph/                     # LangGraph 状态机
│   │   ├── state.py               # AgentState TypedDict
│   │   ├── nodes.py               # 三个节点函数
│   │   ├── edges.py               # 条件路由
│   │   └── builder.py             # graph 全局单例
│   ├── services/
│   │   └── api.py                 # FastAPI SSE（/invoke + /stream）
│   ├── pipelines/
│   │   │   └── rag_ingest.py          # HVAC 语料入库（bge-small-zh-v1.5）
│   ├── frontend/
│   │   └── app.py                 # Streamlit 演示前端
│   └── tests/
│       ├── test_action_agent.py   # /stream 集成测试（3 tests）
│       ├── test_base_skill.py     # BaseSkill 基类契约测试（15 tests）
│       ├── test_hvac_quality.py   # RAG 质量测试（19 tests）
│       ├── test_multi_intent.py      # 多意图识别测试（16 passed）
│       └── test_ui_router_skill.py   # 路由匹配单元测试（4 passed）
├── data/hvac_knowledge/           # ChromaDB 向量库（rag_ingest 后生成）
├── CLAUDE.md                      # AI 协作规范（每次 session 自动加载）
└── AI_CONTEXT.md                  # 项目单点真相
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 核心框架 | LangGraph 1.2，ReAct 状态图 |
| LLM | DeepSeek V4 / OpenAI / Claude（`LLM_PROVIDER` 切换） |
| Embedding | BAAI/bge-small-zh-v1.5（SentenceTransformers，中文优化，本地模型） |
| 向量库 | ChromaDB 本地持久化，5605 条 HVAC 语料 |
| API 层 | FastAPI + SSE 流式（Phase 2） |
| 前端对接 | Vue3 + Vite + TypeScript（福加监控平台） |
| 演示前端 | Streamlit 1.39 |
| 可观测性 | LangSmith（`LANGCHAIN_TRACING_V2=true`） |
| Python | 3.11 |

## 开发阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | ReAct 循环 + HVAC RAG + DeepSeek V4 + 流式前端 | ✅ 完成 |
| Phase 2 | Action Agent：FastAPI SSE + UIAction 跳转信号 + Java 后端工具 | ✅ 完成 |
| Phase 3 | RAG 质量优化（置信度阈值 + MMR 去重 + 拒答 + 引用来源） | ✅ 完成 |
| Phase 4 | Mock → 真实预测 API（TimeDiT / PhysicsAI / AIDC） | 待开始 |
| Phase 5 | 语音助手（Whisper STT + TTS） | 待开始 |
| Phase 6 | 数据可视化 + 报表导出（表格/图表/CSV 下载） | 待开始 |
| Phase 7 | 多意图识别与拆分执行（IntentItem + 分段报告 + SSE） | ✅ 完成 |

## 开发规范

详见 [CLAUDE.md](CLAUDE.md)。核心原则：

- Agent **禁止**手写能源计算，所有计算通过 Tools 调用
- Skills 封装业务推理（Prompt + SOP），Tools 封装原子执行，Graph Nodes 只负责调度
- `AgentState` 用 `TypedDict + Annotated`，Tool I/O 用 Pydantic BaseModel
- Prompt 集中管理至 `src/config/prompts.yaml`，禁止硬编码
- 每个 `.py` 文件必须有模块 docstring（层 / 依赖 / 对接引擎）
- 提交格式：`[模块] 动词短语`，禁止 `git add .`

## 许可

内部项目，未公开授权。© 2026 南京福加智能科技有限公司
