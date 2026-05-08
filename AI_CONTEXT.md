# EnerGraph — 家庭能源 AI 调度解释 Agent

## 项目状态
**当前阶段**: Phase 3 — 重构完成，待 Phase 4 收尾  
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

### 重构完成 ✅
- [x] Step 1: `src/config/settings.py` — 统一配置加载
- [x] Step 2: `src/schemas/` — Pydantic 模型 + AgentState
- [x] Step 3: `src/tools/` — 错误处理 + TOOL_REGISTRY
- [x] Step 4: `src/agents/energy/prompts.py` — Prompt 模板
- [x] Step 5: `src/agents/energy/nodes.py` — 真正 ReAct 节点
- [x] Step 6: `src/agents/energy/graph.py` — 条件路由图
- [x] Step 7: `src/utils/report_builder.py` — 报告生成
- [x] Step 8: `src/frontend/app.py` — Streamlit 界面

### Phase 4 待办（下一阶段）
- [ ] 清理旧文件（`src/agent/`、`src/models/`）
- [ ] 更新 `README.md`（新成员 3 分钟可运行）
- [ ] 更新 `docs/API_INTERFACE.md`
- [ ] 配置 `.env` 填入 API Key，端到端测试
- [ ] 替换 Mock 工具为真实调度算法（业务方负责）
- [ ] 集成 RAG 知识库（`src/pipelines/rag_ingest.py`）
- [ ] CI/CD 配置

---

## 6. 修改日志 (Changelog)

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-05-08 | 协作规范全面扩充：新增 AI 助手协作说明、文档强制更新规则、代码文件头注释规范、Git 提交规范表格 | 魏博源 |
| 2026-05-08 | Phase 3 全部完成：Step 5-8（nodes/graph/report_builder/frontend）+ Python 3.11 环境 | 魏博源 |
| 2026-05-08 | 中场架构审查：扩展为多 Agent 结构，新增 pipelines/memory/services 预留层 | 魏博源 |
| 2026-05-08 | Phase 3 启动：Step 1-4 完成（config/schemas/tools/prompts） | 魏博源 |
| 2026-05-08 | Phase 2 启动：全面架构重构计划制定，AI_CONTEXT.md 重写 | 魏博源 |
| 2026-05-05 | 初版完成：基础 ReAct 框架 + Mock 工具 + Streamlit | 魏博源 |
| 2026-05-05 | Git 初始化 + GitHub 仓库创建 | 魏博源 |

---

## 7. 协作规范

> **写给所有协作者（含 AI 助手）**：本节是你接手工作前必读的行为准则。无论你是人类开发者还是 AI，每次完成一个工作单元后，都必须按照本节规范更新文档和日志，再提交代码。

---

### 7.1 环境配置（新成员入职）

**第一步：克隆仓库**
```bash
git clone https://github.com/Webr1ng/EnerGraph.git
cd EnerGraph
```

**第二步：创建 Python 环境（必须用 conda，Python 3.11）**
```bash
# Windows，Anaconda 安装在 D:\Anaconda
D:\Anaconda\Scripts\conda.exe create -n energraph python=3.11 -y
D:\Anaconda\Scripts\conda.exe activate energraph
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

### 7.2 代码规范

#### 每个文件开头必须有模块简述注释
每个 `.py` 文件的第一行（模块 docstring）必须说明：**这个文件是什么、做什么、属于哪个层**。格式：

```python
"""<模块名> — <一句话说明职责>

所属层：<tools / agents / schemas / config / utils / frontend>
依赖：<列出主要依赖，如 src.schemas.output_schemas>
"""
```

示例（`src/tools/calc_benefit.py`）：
```python
"""收益计算工具 — 对比基准方案与峰谷套利方案的成本差异

所属层：tools
依赖：无（纯计算，不依赖其他 src 模块）
"""
```

#### 函数注释规范
- 所有 `public` 函数必须有 **Type Hints** + **Docstring**（Args / Returns / Raises）
- 函数内部只在"为什么这样做"不明显时写行内注释，不写"做了什么"的废话注释
- 工具函数必须 `try-except`，异常统一返回 `{"error": "工具名: 错误信息"}`

#### 导入规范
- 统一使用**绝对导入**：`from src.config import settings`，禁止相对导入
- 标准库 → 第三方库 → 本项目模块，三组之间空一行

#### 命名规范
- 文件名、函数名、变量名：`snake_case`
- 类名：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`（如 `TOOL_REGISTRY`）

---

### 7.3 Git 提交规范

#### 提交格式
```
[模块] 简短动词短语描述变更内容
```

| 模块标签 | 适用范围 |
|----------|----------|
| `[tools]` | `src/tools/` |
| `[agents]` | `src/agents/` |
| `[schemas]` | `src/schemas/` |
| `[config]` | `src/config/`, `config/` |
| `[frontend]` | `src/frontend/` |
| `[utils]` | `src/utils/` |
| `[docs]` | `AI_CONTEXT.md`, `README.md`, `docs/` |
| `[refactor]` | 跨模块重构 |
| `[fix]` | Bug 修复 |
| `[test]` | `src/tests/` |

示例：
```
[tools] add input validation to calc_benefit
[docs] update Phase 4 progress in AI_CONTEXT.md
[fix] handle empty solar array in compute_metrics
```

#### 推送流程
```bash
git add <具体文件>        # 不要 git add .，避免提交 .env 等敏感文件
git commit -m "[模块] 描述"
git pull --rebase origin main   # 先同步远端，避免冲突
git push origin main
```

---

### 7.4 文档维护规则（强制）

> **每次完成一个工作单元（无论大小），必须在提交代码前完成以下文档更新。**

#### 必须更新的文档

| 变更类型 | 必须更新的文档 |
|----------|----------------|
| 新增 / 修改工具函数 | `AI_CONTEXT.md` §4（接口字典）+ 修改日志 |
| 新增 / 修改 Agent 节点或图结构 | `AI_CONTEXT.md` §2（架构图）+ 修改日志 |
| 新增 / 修改数据模型（schemas） | `AI_CONTEXT.md` §4 + `docs/API_INTERFACE.md` + 修改日志 |
| 新增文件或目录 | `AI_CONTEXT.md` §3（目录结构）+ 修改日志 |
| 删除文件或目录 | `AI_CONTEXT.md` §3 + 修改日志 |
| 修改环境依赖（requirements.txt） | `AI_CONTEXT.md` §2.1（技术栈）+ `README.md` + 修改日志 |
| 完成一个 Phase 阶段 | `AI_CONTEXT.md` §5（进度）+ 修改日志 |

#### 修改日志格式（§6）
每次提交必须在 `AI_CONTEXT.md` 的修改日志表格中追加一行：

```markdown
| YYYY-MM-DD | 简短描述变更内容 | 你的姓名 |
```

- 日期用实际操作日期
- 描述控制在一行内，说清楚"做了什么"
- **姓名填写真实姓名**，AI 协作完成的工作也标注操作者姓名（不写 AI 名）

#### AI 助手协作说明
如果你是 AI 助手接手此项目：
1. 先读完本文件（`AI_CONTEXT.md`）再动手
2. 读 `src/` 下相关模块的文件头注释，了解各层职责
3. 完成工作后，**必须**更新 `AI_CONTEXT.md` 对应章节 + 修改日志
4. 不确定架构决策时，在修改日志中注明"待确认"，等人类审查

---

### 7.5 扩展原则

#### 新增工具
1. 在 `src/tools/` 新建 `<tool_name>.py`，文件头写模块简述
2. 在 `src/tools/__init__.py` 的 `TOOL_REGISTRY` 和 `TOOL_SCHEMAS` 中注册
3. 工具自动对 Agent 可用，无需修改 Agent 代码
4. 更新 `AI_CONTEXT.md` §4.2（工具输出模型）

#### 新增 Agent 节点
1. 在 `src/agents/energy/nodes.py` 添加节点函数
2. 在 `src/agents/energy/graph.py` 注册节点和边
3. 更新 `AI_CONTEXT.md` §2.2（架构图）

#### RAG 扩展
- 利用 `AgentState.context` 字段注入检索结果
- 入库逻辑写在 `src/pipelines/rag_ingest.py`（已预留）
- 检索逻辑在 `agent_node` 中调用，结果写入 `state["context"]`

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
