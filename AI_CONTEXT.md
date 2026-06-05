# 青山 V3 多模态调度 Agent — 项目上下文

## 项目状态
**当前阶段**: Phase 1 完成 ✅ | Phase 2 完成 ✅ | Phase 3 完成 ✅ | Phase 7 完成 ✅ | Skills 基类完成 ✅  
**最后更新**: 2026-06-04  
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
Phase 6: 数据可视化 + 报表导出（表格/图表/CSV 下载）
      ↓
Phase 7: 多意图识别与拆分执行（单输入多意图拆分 + 分段报告）
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
| 配置 | python-dotenv + PyYAML | Prompt 集中管理（prompts.yaml）、版本控制、环境隔离 |
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

### 2.4 Tools vs Skills 分工

```
Tools（原子执行层）= 确定性函数，强类型 I/O，不含 Prompt
  → src/tools/：fetch_cop_data, query_hvac_knowledge, navigate_to_page ...

Skills（业务推理层）= 专属 Prompt + SOP 流程 + Tools 编排
  → src/skills/：HVACExpertSkill, UIRouterSkill, EnergyDispatchSkill ...

Graph Nodes（调度层）= cognitive_parser 识别技能 → Skill 编排 Tools
  → 节点代码保持精简，不含业务逻辑
```



```
EnerGraph/
├── CLAUDE.md                  # 协作规范（每次 session 自动加载，优先级最高）
├── AI_CONTEXT.md              # 本文件（项目单点真相）
├── .env.example               # 环境变量模板
├── requirements.txt
├── config/
│   └── agent_config.yaml      # 默认配置（.env 优先覆盖）
├── docs/                      # 各阶段开发 plan（每个 session 只读对应 plan）
│   ├── plan_skills_refactor.md      # Skills 架构重组方案（跨 Phase 基础设施）
│   ├── plan_skills_base_class.md    # Skills 基类升级（BaseSkill + 生命周期管理）
│   ├── plan_phase2_action_agent.md  # Action Agent：FastAPI SSE + UIAction + Java 工具
│   ├── plan_phase3_rag.md           # RAG 质量优化
│   ├── plan_phase4_realapi.md       # 真实 API 对接
│   ├── plan_phase5_voice.md         # 语音助手
│   ├── plan_phase6_visualization_export.md  # 数据可视化 + 报表导出
│   └── plan_phase7_multi_intent.md         # 多意图识别与拆分执行
└── src/
    ├── config/
    │   ├── settings.py        # 配置加载（LLM_PROVIDER / DEEPSEEK_MODEL 等）
    │   └── prompts.yaml       # 【唯一入口】所有 System Prompt 集中管理 + 版本控制
    ├── schemas/
    │   ├── v3_engine.py       # Pydantic 模型：ConstraintMatrix / TimeDiTForecast /
    │   │                      #   PhysicsResidual / AIDCCoolingStatus / HVACKnowledgeResult /
    │   │                      #   IntentItem（Phase 7）
    │   └── action_agent.py    # PageContext / ActionAgentInput / UIAction（Phase 2）
    ├── skills/                # 业务技能层（Prompt + SOP + Tools 编排，均继承 BaseSkill）
    │   ├── __init__.py        # SKILL_REGISTRY + SKILL_DESCRIPTIONS + get_skill() + get_matched_skills()
    │   ├── base_skill.py      # BaseSkill 抽象基类（execute / before / after 钩子）
    │   ├── hvac_expert_skill.py     # HVAC 专家问答（Phase 3 完善）
    │   ├── energy_dispatch_skill.py # 能源调度分析（Phase 4 完善）
    │   ├── ui_router_skill.py       # 页面跳转 + 数据可视化/导出（Phase 2）
    │   └── v3_interpreter_skill.py  # V3 数据解读报告
    ├── tools/                 # V3 引擎工具（原子执行层，Mock + RAG）
    │   ├── __init__.py        # TOOL_REGISTRY + TOOL_SCHEMAS（LLM function calling 用）
    │   ├── parse_intent.py    # 意图解析 → ConstraintMatrix
    │   ├── query_timedit.py   # TimeDiT 时序预测（Mock）
    │   ├── verify_physics.py  # PhysicsAI 物理验证（Mock）
    │   ├── fetch_aidc_cooling.py # AIDC 液冷状态（Mock）
    │   ├── query_hvac_knowledge.py # HVAC RAG 检索（真实，ChromaDB）
    │   ├── navigate_to_page.py   # 页面跳转 → UIAction（Phase 2）
    │   └── java_backend.py       # Java 后端工具：COP/能耗/报警查询 Mock（Phase 2）
    ├── graph/
    │   ├── state.py           # AgentState（TypedDict + Annotated，含 page_context/pending_actions）
    │   ├── nodes.py           # 三个节点函数（v3_engine_router 含 Skill 调度分发）
    │   ├── edges.py           # should_continue 条件路由
    │   └── builder.py         # 图编译，graph 全局单例
    ├── pipelines/
    │   ├── rag_ingest.py      # HVAC 语料入库（5613 条，ONNX Embedding）
    │   └── sft_export.py      # SFT 数据清洗导出占位
    ├── services/
    │   └── api.py             # FastAPI：GET /health + POST /invoke + POST /stream (SSE)
    ├── frontend/
    │   └── app.py             # Streamlit 演示前端（token 级流式）
    └── tests/
        ├── __init__.py        # 测试包初始化
        ├── test_action_agent.py  # /stream 端点集成测试（Phase 2 T6，3 passed）
        ├── test_base_skill.py    # BaseSkill 基类契约测试（Skills 基类，15 passed）
        ├── test_hvac_quality.py  # RAG 质量测试（Phase 3 T5，19 passed）
        └── test_multi_intent.py  # 多意图识别测试（Phase 7 T5，16 passed）
---

## 4. 工具注册表（Tools）与技能注册表（Skills）

### 4.1 Tools — 原子执行层

| 工具名 | 状态 | 对接引擎 | 输出模型 |
|--------|------|----------|----------|
| `parse_business_intent` | Mock | N/A（纯 LLM） | `ConstraintMatrix` |
| `query_timedit_forecast` | Mock | QingShan-TimeDiT | `TimeDiTForecast` |
| `verify_physics_consistency` | Mock | PhysicsAI | `PhysicsResidual` |
| `fetch_aidc_cooling_status` | Mock | AIDC 智算中心 | `AIDCCoolingStatus` |
| `query_hvac_knowledge` | **真实** | ChromaDB RAG | `HVACKnowledgeResult` |
| `navigate_to_page` | ✅ 已实现 | N/A（状态变更） | `UIAction`（Phase 2） |
| `fetch_cop_data` | Mock | Java 后端 | `COPData`（Phase 2） |
| `fetch_energy_summary` | Mock | Java 后端 | `EnergySummary`（Phase 2） |
| `fetch_active_alarms` | Mock | Java 后端 | `AlarmList`（Phase 2） |
| `fetch_energy_range` | Mock | Java 后端 | `List[EnergySummary]`（Phase 6） |
| `fetch_alarm_history` | Mock | Java 后端 | `AlarmList`（Phase 6） |
| `export_data_table` | ❗ 待实现（Phase 6） | N/A（本地文件） | `DataCard`（Phase 6） |

### 4.2 Skills — 业务推理层

| 技能名 | 状态 | 调用 Tools | 完善阶段 |
|--------|------|-----------|---------|
| `ui_router` | ✅ SOP 已实现 | navigate_to_page, fetch_cop/energy/alarms, export_data_table, fetch_energy_range/alarm_history | Phase 2 → Phase 6 扩展 |
| `hvac_expert` | ✅ 已实现 | query_hvac_knowledge | Phase 3 ✅ |
| `energy_dispatch` | 骨架 | parse_intent, timedit, physics, aidc | Phase 4 |
| `v3_interpreter` | 骨架 | 无（纯 LLM） | Phase 2-4 逐步迁移 |

**HVAC 知识库**: 5613 条语料，覆盖规范查询、能效计算、故障诊断、节能优化，含地铁站/商业项目专项。

---

## 5. 开发阶段与工作顺序

| 阶段 | 内容 | 状态 | Plan |
|------|------|------|------|
| Phase 1 | ReAct 循环 + HVAC RAG + DeepSeek V4 + 流式前端 | ✅ 完成 | — |
| Phase 2 | Action Agent：FastAPI SSE + UIAction 跳转信号 + Java 后端工具 | ✅ 完成 | `docs/plan_phase2_action_agent.md` |
| Skills 基类 | BaseSkill 抽象基类 + 生命周期钩子 + 统一调度 | ✅ 完成 | `docs/plan_skills_base_class.md` |
| Phase 3 | RAG 质量优化（相关度阈值 + 拒答 + 引用来源） | ✅ 完成 | `docs/plan_phase3_rag.md` |
| Phase 4 | Mock → 真实预测 API（TimeDiT / PhysicsAI / AIDC）+ Java 后端真实对接 | 待开始 | `docs/plan_phase4_realapi.md` |
| Phase 5 | 语音助手（Whisper STT + TTS） | 待开始 | `docs/plan_phase5_voice.md` |
| Phase 6 | 数据可视化 + 报表导出（表格/图表/CSV 下载） | 待开始 | `docs/plan_phase6_visualization_export.md` |
| Phase 7 | 多意图识别与拆分执行（单输入多意图 + 分段报告） | ✅ 完成 | `docs/plan_phase7_multi_intent.md` |

**阶段顺序可以调整**，plan 文件相互独立。Phase 4 依赖算法团队 API 就绪，可与 Phase 3 并行。Phase 5 只依赖 Phase 2（API 层）。Phase 6 依赖 Phase 2，可与 Phase 3-5 并行。Phase 7 依赖 Phase 2，可与 Phase 3-6 并行。Skills 基类方案建议在 Phase 3 之前完成。  

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
| 2026-06-05 | Agent 导航功能修复：创建 config/routes.yaml（24个可访问+10个受限真实路由）、更新 prompts.yaml 路由表、重构 ui_router_skill.py（RouteRegistry类+模糊匹配）、新增单元测试（4个测试通过）、settings.py 扩展支持 prompts/routes 加载 | 魏博源 |
| 2026-06-04 | 代码规范审计修复：11 个 __init__.py 补充标准 docstring、graph/nodes.py 和 services/api.py 补充返回值类型标注和 Args/Returns docstring、CLAUDE.md 补充 skills/services/memory/tests 层名枚举 | 魏博源 |
| 2026-06-04 | Skills 基类完成：BaseSkill 抽象基类 + 4 个 Skill 迁移 + 统一调度 + get_skill/get_matched_skills 工厂函数 + 15 测试通过（总 53） | 魏博源 |
| 2026-06-04 | Phase 7 完成：多意图识别与拆分执行（IntentItem + intent_plan + 分段报告 + SSE intent_plan + 16 测试通过） | 魏博源 |
| 2026-06-04 | Phase 3 完成：RAG 质量优化（置信度阈值过滤 + MMR 去重 + 拒答 + 引用来源 + 19 测试通过） | 魏博源 |
| 2026-06-04 | 新增 Phase 7：多意图识别与拆分执行，创建 plan_phase7_multi_intent.md，更新 AI_CONTEXT.md | 魏博源 |
| 2026-06-04 | 全面完善 Phase 3/4/5/6 规划文档（补充业务场景/架构决策/详细改动），新建 plan_skills_base_class.md（BaseSkill 基类方案），更新 AI_CONTEXT.md | 魏博源 |
| 2026-06-04 | 规划 Phase 6：数据可视化 + 报表导出，创建 plan_phase6_visualization_export.md，更新 AI_CONTEXT.md（§1.3/§3/§4/§5/§6） | 魏博源 |
| 2026-05-26 | Phase 2 T6：page_context 注入 cognitive_parser system prompt（current_route + site_id），新建 test_action_agent.py 集成测试（2 passed） | 魏博源 |
| 2026-05-26 | Phase 2 T2（重构）：导航工具 navigate_to_page + UIRouterSkill.infer_navigation SOP，v3_engine_router 改为 Skill 调度分发（不写业务逻辑），prompts.yaml 新增 action_agent_nav_hint 路由表 | 魏博源 |
| 2026-05-26 | Phase 2 T3：Java 后端工具（fetch_cop_data/energy_summary/active_alarms），Mock fallback，注册到 TOOL_REGISTRY | 魏博源 |
| 2026-05-26 | Phase 2 T5：POST /stream SSE 端点，astream_events 推送 text/action/done 事件 | 魏博源 |
| 2026-05-26 | Phase 2 T4：FastAPI 骨架 + /invoke 端点，接收 ActionAgentInput，同步运行 graph 返回 report + actions | 魏博源 |
| 2026-05-26 | Phase 2 T1：新建 action_agent.py（PageContext/ActionAgentInput/UIAction），AgentState 扩展 page_context + pending_actions | 魏博源 |
| 2026-05-22 | Skills 架构重组：建立 src/skills/ 骨架（4个Skill），更新 CLAUDE.md/AI_CONTEXT.md，新增 plan_skills_refactor.md | 魏博源 |
| 2026-05-21 | 工程规范升级：Prompt 强制集中管理 + 版本控制（CLAUDE.md/AI_CONTEXT.md 同步更新） | 魏博源 |
| 2026-05-21 | Phase 2 升级为 Action Agent：UIAction 跳转信号 + Java 后端工具层，创建 plan_phase2_action_agent.md | 魏博源 |
| 2026-05-21 | 规划 Phase 2-5，创建 docs/plan_*.md，精简并重写 AI_CONTEXT | 魏博源 |
| 2026-05-21 | token 级流式前端（stream_mode=messages），streaming=True | 魏博源 |
| 2026-05-18 | LLM_PROVIDER 切换、DeepSeek V4 适配、ONNX Embedding | 魏博源 |
| 2026-05-18 | HVAC RAG 集成（5613 条）、ReAct 循环、对话前端 | 魏博源 |
| 2026-05-14 | Phase 1 重构：V3 架构全量实现 | 魏博源 |

> 完整历史见 `git log`。

---

**下一步**: 可按任意顺序执行 Phase 4/5/6（均可并行）
