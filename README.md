# EnerGraph — 青山 V3 多模态调度 Agent

基于青山大模型 V3（QingShan-TimeDiT + PhysicsAI）的多模态认知交互 Agent，定位为 V3 五层架构的**第 0 层（认知交互层）**。

## 项目定位

Agent 不参与热力学运算，而是作为：
- **业务意图翻译官**：将自然语言 / ERP/MES 输入转化为物理约束矩阵
- **基座引擎调度员**：触发 TimeDiT / PhysicsAI / AIDC_Cooling 工具进行沙盘推演
- **物理决策解说员**：将物理残差、SOC 曲线转化为多维 Markdown 报告

## 项目结构

```
EnerGraph/
├── src/
│   ├── config/
│   │   ├── settings.py            # 统一配置加载
│   │   └── prompts.yaml           # Prompt 模板（外部化）
│   ├── schemas/
│   │   └── v3_engine.py           # ConstraintMatrix / TimeDiTForecast / PhysicsResidual / AIDCCoolingStatus
│   ├── tools/                     # V3 引擎 Mock 工具
│   │   ├── parse_intent.py
│   │   ├── query_timedit.py
│   │   ├── verify_physics.py
│   │   └── fetch_aidc_cooling.py
│   ├── graph/                     # LangGraph 状态机
│   │   ├── state.py               # AgentState (TypedDict + Annotated)
│   │   ├── nodes.py               # cognitive_parser / v3_engine_router / interpreter_generator
│   │   ├── edges.py               # 条件路由
│   │   └── builder.py             # 图编译，graph 全局单例
│   └── frontend/
│       └── app.py                 # Streamlit 交互界面
├── CLAUDE.md                      # 协作准则
└── AI_CONTEXT.md                  # 项目单点真相
```

## 快速开始

### 1. 环境准备

```bash
git clone https://github.com/Webr1ng/EnerGraph.git
cd EnerGraph

conda create -n energraph python=3.11 -y
conda activate energraph
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 API Key：
# OPENAI_API_KEY=your_key   或   ANTHROPIC_API_KEY=your_key
# LANGCHAIN_TRACING_V2=true（可选，启用 LangSmith 追踪）
# LANGCHAIN_API_KEY=your_langsmith_key
```

### 3. 启动前端

```bash
streamlit run src/frontend/app.py
# 浏览器打开 http://localhost:8501
```

在侧边栏输入业务意图（如"明天产线全开，评估能耗风险"），点击**运行 Agent**，即可看到 V3 引擎分析报告。

## 技术栈

| 类别 | 技术 |
|------|------|
| 核心框架 | LangGraph 0.2.x |
| 大模型 | LangChain + OpenAI / Claude |
| 数据验证 | Pydantic 2.x（Tool I/O）|
| 可观测性 | LangSmith |
| 前端 | Streamlit 1.39 |
| Python | 3.11 |

## 开发规范

详见 [CLAUDE.md](CLAUDE.md)。核心原则：
- Agent **禁止**手写能源计算，所有计算通过 Tools 调用
- Prompt 外部化至 `src/config/prompts.yaml`
- `AgentState` 用 `TypedDict + Annotated`，Tool I/O 用 Pydantic BaseModel

## 后续规划

- [ ] 端到端测试（填入真实 API Key）
- [ ] Phase 2：Mock Tools → 真实 gRPC/HTTP 调用
- [ ] Phase 2：接入企业 RAG 知识库
- [ ] Phase 3：eFlex 平台集成与闭环监控看板
