# EnerGraph — Skills 架构重组方案

**目标**: 将业务推理逻辑从 Graph 节点中解耦，沉淀为可复用的 Skill 模块，防止 Phase 3-5 代码膨胀与 AI 幻觉失控。  
**影响范围**: 不新增 Phase，不延误里程碑，Skills 作为各 Phase 内部重构任务融合执行。  
**完成标志**: `src/skills/` 下 4 个 Skill 骨架建立，各 Phase plan 更新融合说明。

---

## 核心分工

```
Tools（原子执行层）
  = 确定性函数，强类型 I/O，不含 Prompt
  = fetch_cop_data(), query_hvac_knowledge(), navigate_to_page() ...

Skills（业务推理层）
  = 专属 Prompt + SOP 流程 + Tools 编排
  = HVACExpertSkill, UIRouterSkill, EnergyDispatchSkill ...

Graph Nodes（调度层）
  = cognitive_parser 识别技能 → 激活对应 Skill → Skill 编排 Tools
  = 节点代码保持精简，不含业务逻辑
```

---

## Skills 目录结构

```
src/skills/
├── __init__.py              # SKILL_REGISTRY + SKILL_DESCRIPTIONS
├── hvac_expert_skill.py     # HVAC 专家问答（Phase 3 完善）
├── energy_dispatch_skill.py # 能源调度分析（Phase 4 完善）
├── ui_router_skill.py       # 页面跳转控制（Phase 2 完善）
└── v3_interpreter_skill.py  # V3 数据解读报告（Phase 2-4 逐步迁移）
```

---

## 各 Skill 说明

### UIRouterSkill（Phase 2 核心）
- **职责**: 监控数据查询 + 页面跳转信号下发
- **Tools**: `navigate_to_page`, `fetch_cop_data`, `fetch_energy_summary`, `fetch_active_alarms`
- **Prompt keys**: `action_agent_nav_hint`（路由表 + 跳转时机）
- **SOP**: 识别查询意图 → Java 工具取数 → 文字总结 → UIAction 跳转信号

### HVACExpertSkill（Phase 3 完善）
- **职责**: HVAC 专业问答，含置信度判断与拒答
- **Tools**: `query_hvac_knowledge`
- **Prompt keys**: `hvac_expert`, `hvac_refusal`, `hvac_citation_format`
- **SOP**: 检索 → 置信度判断 → 拒答 / 引用来源回答

### EnergyDispatchSkill（Phase 4 完善）
- **职责**: 能源调度全链路分析
- **Tools**: `parse_business_intent`, `query_timedit_forecast`, `verify_physics_consistency`, `fetch_aidc_cooling_status`
- **Prompt keys**: `energy_dispatch_intent`, `interpreter_generator`
- **SOP**: 意图解析 → 引擎调度 → 物理验证 → 报告生成

### V3InterpreterSkill（贯穿 Phase 2-4）
- **职责**: 将任意工具结果转化为 Markdown 报告
- **Tools**: 无（纯 LLM 推理）
- **Prompt keys**: `interpreter_generator`
- **SOP**: 接收工具结果 → 按数据类型选模板 → 生成三维报告

---

## 与 Phase 2-5 的融合计划

| Phase | Task | Skills 融合方式 |
|-------|------|----------------|
| Phase 2 | T1 Schemas | `src/skills/` 骨架已建立（本次完成） |
| Phase 2 | T2 导航工具 | 导航逻辑实现在 `ui_router_skill.py`，不写入 nodes.py |
| Phase 2 | T3 Java 工具 | Java 工具注册后，`UIRouterSkill.tools` 列表已预置 |
| Phase 3 | T1-T3 RAG 质量 | 置信度/拒答/引用逻辑实现在 `hvac_expert_skill.py` |
| Phase 4 | T2-T4 真实 API | 各引擎工具替换实现，`EnergyDispatchSkill` 无需改动 |
| Phase 5 | T1-T2 语音 | 新增 `voice_skill.py`，完全独立 |

---

## 痛点预警（不引入 Skills 的后果）

| 阶段 | 风险 |
|------|------|
| Phase 3 | 低置信度/拒答/引用逻辑无处安放，只能塞进 prompts.yaml 或节点代码 |
| Phase 4 | `_field_map` 超过 10 行，`nodes.py` 超过 200 行，新对话 AI 读不完 |
| Phase 5 | 语音流程与 HVAC 问答混在同一 cognitive_parser，意图识别准确率下降 |

---

## 关键文件
- `src/skills/__init__.py` — 技能注册表
- `src/skills/ui_router_skill.py` — Phase 2 核心
- `src/skills/hvac_expert_skill.py` — Phase 3 核心
- `src/skills/energy_dispatch_skill.py` — Phase 4 核心
- `src/config/prompts.yaml` — 所有 Skill 专属 Prompt 的唯一存放位置
