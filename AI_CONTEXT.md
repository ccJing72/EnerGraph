# 青山 V3 多模态调度 Agent — 项目上下文

## 项目状态
**当前阶段**: Phase 1 完成 — HVAC 知识库集成 + 对话 Agent 可运行  
**最后更新**: 2026-05-18  
**项目性质**: 企业级落地方案，不公开  
**GitHub**: https://github.com/Webr1ng/EnerGraph.git  
**GitLab**: git@172.16.3.160:ai-group/energraph.git  
**Python 环境**: conda `energraph` / Python 3.11（LangGraph 官方要求 ≥3.10）

---

## 1. 项目概览

### 1.1 定位：V3 第 0 层认知交互 Agent

本项目是青山大模型 V3（QingShan-TimeDiT + PhysicsAI）五层架构的**第 0 层（认知交互层）**。Agent 不参与热力学运算或时序特征生成，而是作为：

| 角色 | 职责 |
|------|------|
| **业务意图翻译官**（输入端） | 将 ERP/MES 及人类自然语言输入转化为物理约束矩阵 |
| **基座引擎调度员**（执行端） | 通过内部 API 触发 PhysicsAI / TimeDiT 进行沙盘推演 |
| **物理决策解说员**（输出端） | 将生涩的物理残差、SOC 曲线转化为多语言 Markdown 报告 |

### 1.2 核心数据流

```
多模态输入（自然语言 / ERP JSON / 语音）
        │
        ▼
┌──────────────────────────┐
│ 1. Intent Parsing        │  LLM 解析业务意图 → 约束矩阵 (ConstraintMatrix)
│    (Cognitive_Parser)    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ 2. Engine Invocation     │  并行调用 Mock Tools:
│    (V3_Engine_Router)    │  - Tool_HVAC_RAG (暖通知识库检索) ← 新增
│                          │  - Tool_TimeDiT (时序预测)
│                          │  - Tool_PhysicsAI (物理验证)
│                          │  - Tool_AIDC_Cooling (液冷状态)
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ 3. Report Generation     │  LLM 结合物理残差与策略参数，生成
│    (Interpreter_Generator)│  包含"能耗收益/碳排下降/设备安全"的
│                          │  Markdown 多维解释报告
└──────────────────────────┘
```

---

## 2. 技术架构

### 2.1 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| 核心框架 | LangGraph 0.2.x | ReAct 状态图编排 |
| 大模型 | LangChain + DeepSeek V4 / OpenAI / Claude（LLM_PROVIDER 切换） | 意图解析与报告生成 |
| Embedding | ChromaDB ONNX（all-MiniLM-L6-v2）本地模型 | HVAC 语料向量化，零外部 API 依赖 |
| 数据验证 | Pydantic 2.x | Tool Inputs/Outputs 类型约束（AgentState 用 TypedDict） |
| 可观测性 | LangSmith | Agent 执行链路追踪与调试（需配置 `LANGCHAIN_TRACING_V2=true`） |
| 前端 | Streamlit 1.39 | 多模态交互可视化 |
| 配置 | python-dotenv + PyYAML | Prompt 外部化、环境隔离 |
| Python | 3.11 | 运行环境 |

### 2.2 LangGraph 状态图架构

```
       ┌──────────────────┐
       │ Cognitive_Parser │ ← LLM Thought：分析输入，生成约束矩阵
       │   (意图解析)      │
       └────────┬─────────┘
                │
       ┌────────┴─────────┐
       │ V3_Engine_Router │ ← 并行调用 TimeDiT, PhysicsAI, AIDC_Cooling
       │  (引擎调度路由)   │
       └────────┬─────────┘
                │
       ┌────────┴──────────────┐        ┌─────────────────────┐
       │ Interpreter_Generator │ ──────→ │ Human_Approval      │ (预留)
       │    (报告生成)          │        │ interrupt() 审批节点 │
       └───────────────────────┘        └─────────────────────┘
```

---

## 3. 项目目录结构（目标）

```
EnerGraph/
├── CLAUDE.md                      # 协作准则（Claude 自动加载）
├── AI_CONTEXT.md                  # 本文件 — 项目单点真相
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
│
├── config/
│   └── agent_config.yaml
│
└── src/
    ├── config/                    # ✅ 配置加载 + Prompt 外部化
    │   ├── settings.py
    │   └── prompts.yaml           # V3 System Prompt 模板（外部化）
    ├── schemas/                   # ✅ V3 Pydantic 数据模型
    │   └── v3_engine.py           # ConstraintMatrix, TimeDiTForecast, PhysicsResidual, AIDCCoolingStatus
    ├── tools/                     # ✅ V3 引擎 Mock 工具
    │   ├── __init__.py            # TOOL_REGISTRY + TOOL_SCHEMAS
    │   ├── parse_intent.py        # 意图解析 → ConstraintMatrix
    │   ├── query_timedit.py       # TimeDiT 时序预测
    │   ├── verify_physics.py      # PhysicsAI 物理一致性验证
    │   └── fetch_aidc_cooling.py  # AIDC 液冷状态
    ├── graph/                     # ✅ LangGraph 状态机
    │   ├── state.py               # AgentState (TypedDict + Annotated reducer)
    │   ├── nodes.py               # cognitive_parser / v3_engine_router / interpreter_generator
    │   ├── edges.py               # should_continue 条件路由
    │   └── builder.py             # 图组装与编译，graph 全局单例
    ├── pipelines/                 # ✅ 数据处理流水线
    │   ├── rag_ingest.py          # HVAC 语料库入库 ChromaDB（5613 条）
    │   └── sft_export.py          # SFT 数据清洗导出（预留）
    ├── memory/                    # 【预留】记忆管理
    │   └── checkpointer.py        # Checkpointer 配置，实例在 graph/builder.py 中注入
    ├── services/                  # 【预留】FastAPI 服务层
    │   └── api.py
    ├── utils/
    │   └── report_builder.py
    ├── frontend/
    │   └── app.py                 # ✅ Streamlit 对话式交互（支持 HVAC 问答 + 调度分析）
    └── tests/
        ├── test_tools.py
        └── test_graph.py
```

---

## 4. 核心数据模型与接口

### 4.1 V3 引擎输入模型（v3_engine.py 待创建）

```python
ConstraintMatrix:
  """业务意图解析结果 — LLM 将自然语言转化为底层 DFL 算法可读的约束"""
  load_baseline: str          # 负荷基线变化，如 "+20%", "-10%"
  sla_priority: str           # SLA 优先级: "High" | "Normal" | "Low"
  time_window: str            # 时间窗口，如 "2026-05-15"
  optimization_goal: str      # 优化目标: "cost" | "carbon" | "safety"
  extra_constraints: dict     # 额外约束键值对

TimeDiTForecast:
  """TimeDiT 时序扩散模型预测输出"""
  target_date: str
  load_forecast: List[float]        # 24h 负荷预测 (kWh)
  solar_forecast: List[float]       # 24h 光伏预测 (kWh)
  confidence_interval: List[float]  # 概率分布置信区间

PhysicsResidual:
  """PhysicsAI 物理一致性验证结果"""
  strategy_id: str
  is_physically_valid: bool         # 是否通过热力学热平衡验证
  langevin_residual: float          # Langevin 动力学修正残差
  soc_decay_deviation: float        # SOC 衰减偏差
  heat_balance_error: float         # 热平衡误差
  safety_warnings: List[str]        # 安全边界告警

AIDC_CoolingStatus:
  """智算中心液冷状态"""
  datacenter_id: str
  gpu_queue_depth: int              # GPU 任务队列深度
  liquid_cooling_temp: float        # 液冷温度 (°C)
  pre_cooling_policy: str           # 预冷策略状态
  power_draw_kw: float              # 当前算力功耗 (kW)
```

### 4.2 V3 工具注册表（TOOL_REGISTRY）

| 工具名 | 函数 | 对接 V3 引擎 |
|--------|------|-------------|
| `parse_business_intent` | 意图解析 | N/A（纯 LLM 调用） |
| `query_timedit_forecast` | 时序预测 | QingShan-TimeDiT |
| `verify_physics_consistency` | 物理验证 | PhysicsAI |
| `fetch_aidc_cooling_status` | 液冷状态 | AIDC 智算中心 |
| `query_hvac_knowledge` | HVAC 知识库检索 | ChromaDB RAG（5613 条，ONNX 本地 Embedding） |

### 4.3 Agent 状态（agent_state.py 待重构）

```python
AgentState (TypedDict):
  # 输入
  user_input: str                     # 原始用户输入（自然语言/JSON）
  messages: List[BaseMessage]         # LangGraph 消息流

  # 意图解析
  constraints: ConstraintMatrix | None

  # 引擎调用结果
  timedit_data: TimeDiTForecast | None
  physics_verification: PhysicsResidual | None
  aidc_cooling: AIDC_CoolingStatus | None

  # 扩展（RAG 预留）
  context: str | None

  # 输出
  final_report: str                   # Markdown 解析报告
  error: str | None
```

---

## 5. 开发进度

### Phase 1: 交互流闭环与 API Mock ← 当前阶段
- [x] 改写 CLAUDE.md + AI_CONTEXT.md（V3 架构适配）
- [x] 创建 src/schemas/v3_engine.py（ConstraintMatrix / TimeDiTForecast / PhysicsResidual / AIDCCoolingStatus）
- [x] 创建 src/graph/（state / nodes / edges / builder）
- [x] 创建 4 个 V3 Mock Tools（parse_intent / query_timedit / verify_physics / fetch_aidc_cooling）
- [x] Prompt 外部化至 src/config/prompts.yaml
- [x] 删除旧 src/agents/、旧 schemas、旧 tools
- [x] 适配 src/frontend/app.py 接入新 graph
- [x] 更新 README.md
- [x] 集成 HVAC 知识库 RAG（5613 条语料，ChromaDB + OpenAI Embedding）
- [x] 新增 query_hvac_knowledge 工具 + HVACKnowledgeResult 模型
- [x] 前端升级为对话模式（chat_input + 历史记录）
- [x] 配置 .env 填入 API Key（DeepSeek V4），运行 rag_ingest 入库（5613 条），端到端测试通过
- [x] RAG Embedding 切换为 ChromaDB 内置 ONNX 本地模型（零外部 API Key 依赖）
- [x] 新增 LLM_PROVIDER 显式供应商切换（deepseek/openai/anthropic）
- [x] 前端示例问题精简为纯 HVAC 问答（移除预测/调度类问题）

### Phase 2: 物理/算法插件对接
- [ ] 将 Mock 工具替换为真实内部 gRPC/HTTP 调用

### Phase 3: eFlex 平台集成与闭环监控
- [ ] 配合 eFlex 每 15 分钟滚动优化，上线动态 Agent 看板
- [ ] PhysicsAI 反事实检测 → 预测性维护人话告警推送

---

## 6. 变更日志（Changelog）

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-05-18 | LLM_PROVIDER 显式供应商切换、DeepSeek V4 API 适配、Embedding 切本地 ONNX、前端示例精简 | 魏博源 |
| 2026-05-18 | 集成 HVAC 知识库 RAG：rag_ingest.py、query_hvac_knowledge 工具、HVACKnowledgeResult 模型、前端升级对话模式 | 魏博源 |
| 2026-05-14 | Phase 1 全部完成：frontend/app.py 适配新 graph、README.md 全面更新 | 魏博源 |
| 2026-05-14 | Phase 1 重构：创建 src/graph/(state/nodes/edges/builder)、src/schemas/v3_engine.py、4 个 V3 Mock Tools、prompts.yaml；删除旧 src/agents/、旧 schemas、旧 tools | 魏博源 |
| 2026-05-14 | V3 重构启动：CLAUDE.md 新增架构红线与状态同步铁律，AI_CONTEXT.md 全面重写为青山 V3 项目大脑 | 魏博源 |
| 2026-05-08 | Phase 4 清理启动：删除旧目录(src/agent,src/models,compete_price.py)，readme/api_interface全面更新 | 魏博源 |
| 2026-05-08 | 创建 CLAUDE.md：提取固定策略与行为准则，AI_CONTEXT.md §7 精简为环境配置+速查表 | 魏博源 |
| 2026-05-08 | 协作规范再次扩充：新增分支策略(7.3)、.env保护说明、测试规范(7.6)、创建src/tests/目录 | 魏博源 |
| 2026-05-08 | 协作规范全面扩充：新增 AI 助手协作说明、文档强制更新规则、代码文件头注释规范、Git 提交规范表格 | 魏博源 |
| 2026-05-08 | Phase 3 全部完成：Step 5-8（nodes/graph/report_builder/frontend）+ Python 3.11 环境 | 魏博源 |
| 2026-05-08 | 中场架构审查：扩展为多 Agent 结构，新增 pipelines/memory/services 预留层 | 魏博源 |
| 2026-05-08 | Phase 3 启动：Step 1-4 完成（config/schemas/tools/prompts） | 魏博源 |
| 2026-05-08 | Phase 2 启动：全面架构重构计划制定，AI_CONTEXT.md 重写 | 魏博源 |
| 2026-05-05 | 初版完成：基础 ReAct 框架 + Mock 工具 + Streamlit | 魏博源 |
| 2026-05-05 | Git 初始化 + GitHub 仓库创建 | 魏博源 |

---

## 7. 协作规范

> **代码规范、Git 规范、测试规范、文档维护规则、AI 助手行为准则等固定策略已迁移至 [`CLAUDE.md`](./CLAUDE.md)。**
> Claude 每次会话自动加载该文件，协作者也应先读该文件理解项目准则。
> 当两文件冲突时，以 `CLAUDE.md` 为准。

---

### 7.1 环境配置（新成员入职）

**第一步：克隆仓库**
```bash
git clone https://github.com/Webr1ng/EnerGraph.git
cd EnerGraph
```

**第二步：创建 Python 环境（必须用 conda，Python 3.11）**
```bash
conda create -n energraph python=3.11 -y
conda activate energraph
pip install -r requirements.txt
```

**第三步：配置环境变量**
```bash
cp .env.example .env
# 用编辑器打开 .env，填入你的 API Key（OpenAI 或 Anthropic）
```

**第四步：启动前端验证环境**
```bash
streamlit run src/frontend/app.py
# 浏览器打开 http://localhost:8501，点击"执行 Agent"，能看到报告即为成功
```

---

### 7.2 快速规范索引

以下规范详见 [`CLAUDE.md`](./CLAUDE.md)，此处仅列要点速查：

| 类别 | 速查要点 |
|------|----------|
| **架构红线** | Agent 禁止手写能源计算 / Prompt 外部化 / 强类型 Pydantic |
| **代码规范** | 文件头 docstring（注明对接 V3 引擎）/ Type Hints / 绝对导入 / snake_case / try-except 返回 `{"error": ...}` |
| **分支策略** | main 直接开发（当前阶段），后续按需创建 feature/fix 分支 |
| **提交格式** | `[模块] 动词短语`（标签：tools/graph/schemas/config/frontend/utils/docs） |
| **测试规范** | `src/tests/test_<模块>.py` / 新 Tool 必测 / 修 Bug 先写测试 |
| **文档更新** | 变更后必须更新 `AI_CONTEXT.md` 对应章节 + 变更日志 |
| **.env 保护** | 绝对禁止提交，不用 `git add .` |
| **状态同步** | 文件修改后更新 AI_CONTEXT.md / 架构问题前先读 AI_CONTEXT.md |

---

## 8. 部署说明

### 本地运行
```bash
streamlit run src/frontend/app.py
```

### 云部署（预留）
- 支持 Docker 容器化
- 支持通过环境变量注入配置（12-Factor App）
- 配置文件路径可通过 `CONFIG_PATH` 环境变量覆盖

---

**最后更新**: 2026-05-18  
**下一里程碑**: 配置 API Key → rag_ingest 入库 → 端到端测试
