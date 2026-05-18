# EnerGraph — 青山 V3 多模态调度 Agent

基于青山大模型 V3（QingShan-TimeDiT + PhysicsAI）的多模态认知交互 Agent，集成 HVAC 专业知识库，支持暖通空调专家问答与能源调度分析。

## 功能

- **HVAC 专家问答**：5613 条暖通空调专业语料（规范查询、能效计算、故障诊断、节能优化），RAG 检索驱动
- **能源调度分析**：自然语言输入 → 约束矩阵 → TimeDiT 预测 + PhysicsAI 验证 → Markdown 报告
- **对话式交互**：多轮对话，历史记录保留
- **V3 第 0 层定位**：Agent 不参与计算，所有结果通过 Tools 获取

## 快速开始

### 1. 环境准备

```bash
git clone https://github.com/Webr1ng/EnerGraph.git
cd EnerGraph
conda create -n energraph python=3.11 -y
conda activate energraph
pip install -r requirements.txt
pip install chromadb  # RAG 向量库
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入：
# OPENAI_API_KEY=your_key   或   ANTHROPIC_API_KEY=your_key
# LANGCHAIN_TRACING_V2=true（可选，LangSmith 追踪）
```

### 3. 初始化 HVAC 知识库（首次运行）

```bash
python -m src.pipelines.rag_ingest
# 将 5613 条 HVAC 语料入库，约 2-5 分钟
```

### 4. 启动前端

```bash
streamlit run src/frontend/app.py
# 浏览器打开 http://localhost:8501
```

## 项目结构

```
EnerGraph/
├── src/
│   ├── config/
│   │   ├── settings.py            # 统一配置加载
│   │   └── prompts.yaml           # Prompt 模板（外部化）
│   ├── schemas/
│   │   └── v3_engine.py           # Pydantic 模型（含 HVACKnowledgeResult）
│   ├── tools/                     # V3 引擎 Mock 工具 + HVAC RAG
│   │   ├── query_hvac_knowledge.py  # HVAC 知识库检索
│   │   ├── parse_intent.py
│   │   ├── query_timedit.py
│   │   ├── verify_physics.py
│   │   └── fetch_aidc_cooling.py
│   ├── graph/                     # LangGraph 状态机
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── edges.py
│   │   └── builder.py
│   ├── pipelines/
│   │   └── rag_ingest.py          # HVAC 语料库入库（5613 条）
│   └── frontend/
│       └── app.py                 # Streamlit 对话界面
├── data/hvac_knowledge/           # ChromaDB 向量库（运行 rag_ingest 后生成）
├── CLAUDE.md                      # 协作准则
└── AI_CONTEXT.md                  # 项目单点真相
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 核心框架 | LangGraph 0.2.x |
| 大模型 | LangChain + OpenAI / Claude |
| 向量库 | ChromaDB（本地） |
| Embedding | OpenAI text-embedding-3-small |
| 可观测性 | LangSmith |
| 前端 | Streamlit 1.39 |
| Python | 3.11 |

## 开发规范

详见 [CLAUDE.md](CLAUDE.md)。核心原则：
- Agent **禁止**手写能源计算，所有计算通过 Tools 调用
- `AgentState` 用 `TypedDict + Annotated`，Tool I/O 用 Pydantic BaseModel
- Prompt 外部化至 `src/config/prompts.yaml`

## 后续规划

- [ ] 端到端测试（填入真实 API Key + 运行 rag_ingest）
- [ ] Phase 2：Mock Tools → 真实 gRPC/HTTP 调用（待 AI 研究院 V3 算法上线）
- [ ] Phase 2：扩充 HVAC 语料库，加入更多规范文档
- [ ] Phase 3：eFlex 平台集成与闭环监控看板
