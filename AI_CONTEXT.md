# EnerGraph — 家庭能源 AI 调度解释 Agent

## 项目状态
**当前阶段**: Phase 3 — 架构重构中  
**最后更新**: 2026-05-08  
**项目性质**: 企业级落地方案（支持上云 / 本地部署）  
**GitHub**: https://github.com/Webr1ng/EnerGraph.git  
**Python 环境**: conda `energraph` / Python 3.11（LangGraph 官方要求 ≥3.10）  
**Anaconda 路径**: `D:\Anaconda`（已确认安装）

---

## 1. 项目概览

### 1.1 业务目标
构建一个基于 LangGraph 的家庭能源 AI 调度解释 Agent。核心功能：
- 接收家庭负载、光伏、电价等模拟数据
- 通过 **ReAct（Thought → Action → Observation）循环** 驱动大模型进行策略归因分析
- 调用工具函数获取量化指标
- 输出包含"调度安排""收益对比""总结建议"的结构化报告

### 1.2 核心业务流
```
用户输入 → LLM Thought（分析需求）→ Action（调用工具）→ Observation（解读结果）
                ↑                                                       ↓
                └──────────── 循环直至信息充足 ←────────────────────────┘
                                                    ↓
                                            Final Answer（报告输出）
```

---

## 2. 技术架构

### 2.1 技术栈
| 类别 | 技术 | 用途 |
|------|------|------|
| 核心框架 | LangGraph 0.2.x | ReAct 状态图编排 |
| 大模型 | LangChain + OpenAI/Claude | 思考与决策 |
| 数据验证 | Pydantic 2.x | 输入输出模型 |
| 前端 | Streamlit 1.39 | 可视化交互 |
| 配置 | python-dotenv + PyYAML | 环境隔离 |
| Python | 3.10+ | 运行环境 |

### 2.2 ReAct 循环架构
```
       ┌─────────────┐
       │ agent_node  │ ← LLM Thought：分析数据，决定动作
       │  (Decision) │
       └──────┬──────┘
              │
        ┌─────┴─────┐
        │ condition  │ ← 路由判断
        └─────┬─────┘
       ┌──────┴──────┐
       ↓              ↓
┌──────────┐   ┌────────────┐
│tool_node │   │report_node │ → Final Answer → END
│(Action)  │   │(Final)     │
└────┬─────┘   └────────────┘
     │
     └──→ 回到 agent_node (Observation)
```

---

## 3. 项目目录结构

> **2026-05-08 中场架构审查后更新**：扩展为多 Agent 可扩展结构，支持未来 RAG / SFT 数据管道。

```
EnerGraph/
├── AI_CONTEXT.md                  # 本文件 — 项目单点真相
├── README.md                      # 快速启动指南
├── .gitignore
├── .env.example
├── requirements.txt               # Python ≥3.11
│
├── config/
│   └── agent_config.yaml
│
└── src/
    ├── config/                    # ✅ 配置加载（已完成）
    │   └── settings.py
    ├── schemas/                   # ✅ 数据模型（已完成）
    │   ├── input_schemas.py
    │   ├── output_schemas.py
    │   └── agent_state.py
    ├── tools/                     # ✅ 工具注册表（已完成）
    │   ├── __init__.py            # TOOL_REGISTRY
    │   ├── compute_metrics.py
    │   ├── compare_price.py
    │   └── calc_benefit.py
    ├── agents/                    # 🔄 多 Agent 目录（原 agent/ 重命名）
    │   ├── base.py                # Agent 基类（统一接口）
    │   └── energy/                # 调度解释 Agent
    │       ├── graph.py
    │       ├── nodes.py
    │       └── prompts.py         # ✅ 已完成
    ├── pipelines/                 # 【预留】数据处理流水线
    │   ├── rag_ingest.py          # RAG 文档入库
    │   └── sft_export.py          # SFT 数据清洗导出
    ├── memory/                    # 【预留】记忆管理
    │   └── checkpointer.py
    ├── services/                  # 【预留】FastAPI 服务层
    │   └── api.py
    ├── utils/
    │   └── report_builder.py
    ├── frontend/
    │   └── app.py
    └── tests/
        ├── test_tools.py
        └── test_agents.py
```

---

## 4. 核心接口与数据字典

### 4.1 输入模型 (input_schemas.py)

```python
ForecastData:
  load: List[float]         # 24h 负载 (kWh), len=24
  solar: List[float]        # 24h 光伏 (kWh), len=24
  grid_price: List[float]   # 24h 电价 (元/kWh), len=24

SystemState:
  soc: float (0-1)          # 当前 SOC
  soc_max: float (0-1)      # 最大 SOC, 默认 0.9
  soc_min: float (0-1)      # 最小 SOC, 默认 0.2
  max_power: float (>0)     # 最大充放电功率 (kW)
  user_pref: str            # "cost_priority" | "eco_priority" | "backup_priority"

BasicInfo:
  timezone: str             # 默认 "UTC+8"
  currency: str             # 默认 "CNY"
  query: str                # 用户查询
```

### 4.2 工具输出模型 (output_schemas.py)

```python
MetricsResult:
  total_load_kwh: float
  total_solar_kwh: float
  solar_utilization_pct: float
  valley_load_kwh: float
  peak_load_kwh: float
  avg_price: float

PriceCompareResult:
  min_price: float
  max_price: float
  min_price_hour: int
  max_price_hour: int
  price_diff: float
  arbitrage_potential_pct: float

BenefitResult:
  baseline_cost: float
  optimized_cost: float
  savings: float
  savings_pct: float
```

### 4.3 Agent 状态 (agent_state.py)

```python
AgentState (TypedDict):
  # 输入
  load, solar, grid_price: List[float]
  soc, max_power: float
  user_pref, query: str

  # 工具结果
  metrics: MetricsResult | None
  price_analysis: PriceCompareResult | None
  benefit: BenefitResult | None

  # 控制流
  next_action: str           # "call_tool" | "generate_report" | "end"
  tool_to_call: str | None   # 当前要调用的工具名
  iteration: int

  # 扩展（RAG 预留）
  context: str | None
  history: List[Dict] | None

  # 输出
  report: str
  error: str | None
```

---

## 5. 开发进度

### 已完成
- [x] 项目目录初始化 + Git 仓库
- [x] 基础 Mock 工具实现（初版）
- [x] Streamlit 前端 Demo（初版）
- [x] 基础文档（README, API_INTERFACE）

### 重构中（当前阶段）
- [x] Step 1: 创建 `src/config/settings.py` 统一配置加载 ✅
- [x] Step 2: 重构 `src/schemas/` 合并数据模型 ✅
- [x] Step 3: 重构 `src/tools/` 添加错误处理与注册表 ✅
- [x] Step 4: 新增 `src/agent/prompts.py` 提取 Prompt ✅
- [x] Step 5: 新增 `src/agents/energy/nodes.py` 实现真正 ReAct ✅
- [x] Step 6: 新增 `src/agents/energy/graph.py` 添加条件路由 ✅
- [x] Step 7: 新增 `src/utils/report_builder.py` 提取报告逻辑 ✅
- [x] Step 8: 重构 `src/frontend/app.py` 匹配新 API ✅

### 待办
- [ ] 替换 Mock 工具为真实调度算法
- [ ] 集成 RAG 知识库
- [ ] 多语言支持
- [ ] CI/CD 配置

---

## 6. 修改日志 (Changelog)

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-05-08 | 中场架构审查：扩展为多 Agent 结构，新增 pipelines/memory/services 预留层 | 魏博源 |
| 2026-05-08 | Phase 3 启动：Step 1-4 完成（config/schemas/tools/prompts） | 魏博源 |
| 2026-05-08 | Phase 2 启动：全面架构重构计划制定，AI_CONTEXT.md 重写 | 魏博源 |
| 2026-05-05 | 初版完成：基础 ReAct 框架 + Mock 工具 + Streamlit | 魏博源 |
| 2026-05-05 | Git 初始化 + GitHub 仓库创建 | 魏博源 |

---

## 7. 协作规范

### 7.1 环境配置（新成员入职）
```bash
git clone https://github.com/Webr1ng/EnerGraph.git
cd EnerGraph
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 填入 API Key
streamlit run src/frontend/app.py
```

### 7.2 代码规范
- **PEP 8** 严格遵循，所有函数必须有 Type Hints + Docstrings
- **绝对导入**：`from src.config import settings` 而非相对导入
- **错误处理**：工具函数必须 try-except 并返回结构化错误
- **提交格式**：`[模块] 简短描述`，如 `[tools] add input validation to calc_benefit`

### 7.3 文档维护规则
- `AI_CONTEXT.md` 是项目"单点真相"，任何架构变更必须同步更新
- `API_INTERFACE.md` 反映前后端契约，接口变更必须同步更新
- `README.md` 保持新成员 3 分钟可运行的准确性

### 7.4 扩展原则
- 新增工具：在 `src/tools/` 添加文件 → 在 `TOOL_REGISTRY` 注册 → 工具自动可用
- 新增节点：在 `src/agent/nodes.py` 添加函数 → 在 `graph.py` 注册节点和边
- RAG 扩展：利用 `AgentState.context` 字段注入检索结果

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

**最后更新**: 2026-05-08  
**下一里程碑**: Phase 3 — 逐步重构执行
