# Claude Code 项目重构 Prompt

> 以下 prompt 用于让 Claude Code 重新认识项目定位并对 EnerGraph 进行全面重构升级。
> 使用方法：将全部内容复制粘贴到 Claude Code 会话的第一条消息中。

---

```
你是 EnerGraph（青山大模型）项目的核心开发助手。在开始任何工作之前，请严格按照以下步骤完成项目认知重建和代码审计。

## 第一步：阅读公司战略规划文档

请先完整阅读以下文件，理解公司 V3.0 五层架构的战略方向：

1. `/Users/webring/Library/CloudStorage/OneDrive-个人/Fuca/福加AI赋能产品规划方案_自演化Agent战略升级版_V3.1_调研增强版.docx`
   - 这是公司最新的青山大模型产品规划，定义了五层架构（数据采集→算法模型→决策层→自演化引擎→应用层）
   - 重点关注：第3层"决策层"的定位、MCP协议工具调用规范、自演化Agent引擎层的五大模块

2. `docs/architecture_v3_overview.html` — 架构全景图（浏览器打开可查看）

## 第二步：阅读项目现状文档

然后完整阅读以下项目文件：

1. `AI_CONTEXT.md` — 项目单点真相（已更新为 V3.0 架构定位）
2. `CLAUDE.md` — 项目协作准则（已更新）
3. `CHANGELOG.md` — 变更历史

## 第三步：核心认知 — 项目定位

你必须清楚以下关键事实：

### EnerGraph 是什么
- EnerGraph 是公司青山大模型 V3.0 五层架构中 **第3层（决策层）+ 第4层（自演化引擎层）** 的 LangGraph Agent 代码实现
- EnerGraph 的第一个业务落地身份是 **PowerAI 储能调度智能体**（光伏预测 + 负荷预测 → 综合决策 → 充放电策略）
- 未来通过不同 Skill 配置可扩展为能效诊断、碳管理等其他智能体

### EnerGraph 不是什么
- 不是老架构中的"第0层认知交互层"（这个概念已废弃）
- 不是底层算法引擎（算法模型在第2层，由算法团队负责）
- 不是前端应用（应用层在第5层，由前端团队负责）

### 决策层的三大核心职责
1. **意图理解**：自然语言 → 结构化任务（cognitive_parser 节点）
2. **工具调度**：通过 MCP 协议调用算法模型 / 通过 REST API 查询福加运营数据（v3_engine_router + Tools）
3. **决策解释**：数值计算结果 → 用户可理解的报告（interpreter_generator 节点）

### 工具接入方式（两类，不可混淆）
1. **算法模型工具** → MCP 协议（计划引入）：光伏预测、电负荷预测、冷负荷预测、储能调度优化等。算法团队封装为 MCP Server，Agent 通过 MCP Client 调用。
2. **运营数据工具** → REST API（当前已有 10 个）：福加 Java 后端的 COP、能耗、报警、碳排、光伏、用电量等监控数据。参数解析和 Token 刷新在 Tool 代码内处理。

## 第四步：代码审计 — 识别需要清理/重构的内容

请扫描整个 `src/` 目录，重点关注以下问题并列出发现：

### 4.1 过时的 Mock 工具（需要清理或重写）

以下 Mock 工具基于老架构（QingShan-TimeDiT + PhysicsAI + AIDC）设计，命名和 Schema 与新 V3.0 架构不匹配：

| 文件 | 老架构命名 | 新架构应对应 | 处理方式 |
|------|-----------|------------|---------|
| `src/tools/query_timedit.py` | TimeDiT 时序预测 | 电负荷预测（算法模型层 MCP） | 重写为 MCP Client 调用骨架，或删除 Mock 代码保留接口定义 |
| `src/tools/verify_physics.py` | PhysicsAI 物理验证 | 设备健康诊断（算法模型层 MCP） | 同上 |
| `src/tools/fetch_aidc_cooling.py` | AIDC 液冷状态 | 制冷寻优（算法模型层 MCP） | 同上 |

**问题**：这些 Mock 工具的函数名、Schema 定义、docstring 都引用了老架构概念（TimeDiT、PhysicsAI、AIDC），需要统一为新架构的算法模型命名。

### 4.2 过时的 Schema 定义

`src/schemas/v3_engine.py` 中的 Pydantic 模型可能引用了老架构概念：
- `TimeDiTForecast` → 应改名为 `LoadForecast`（电负荷预测）或更通用的 `PredictionResult`
- `PhysicsResidual` → 应改名为 `DeviceDiagnosis`（设备健康诊断）
- `AIDCCoolingStatus` → 应改名为 `CoolingOptimization`（制冷寻优）
- `ConstraintMatrix` → 评估是否仍需要，或替换为更贴合 PowerAI 场景的模型

请阅读 `src/schemas/v3_engine.py` 全文，列出所有引用老架构概念的模型，建议新的命名。

### 4.3 过时的 Prompt 内容

`src/config/prompts.yaml` 中可能有引用老架构概念的 Prompt：
- 提及 "TimeDiT"、"PhysicsAI"、"AIDC"、"第0层"、"V3引擎" 等关键词
- 提及"物理约束矩阵"、"物理残差"等老架构术语

请阅读 `src/config/prompts.yaml` 全文，列出所有需要更新的 Prompt key 和具体位置。

### 4.4 过时的文件名和引用

扫描所有 `.py` 文件的文件头注释（docstring），检查是否有引用老架构概念：
- "对接 V3 引擎：PhysicsAI / TimeDiT / AIDC_Cooling"
- "QingShan-TimeDiT"
- "V3 引擎工具"

### 4.5 无用代码检测

扫描 `src/` 目录，识别：
- 未被任何模块 import 的文件
- 空函数/占位函数（只有 pass 或 return Mock 数据且没有 TODO 注释的）
- 重复的功能实现
- `src/pipelines/sft_export.py`（SFT 数据清洗导出占位）— 评估是否仍需要

### 4.6 目录结构评估

评估 `src/tools/` 是否需要按接入方式分子目录：
```
src/tools/
├── mcp/           # 算法模型 MCP 工具（未来）
├── api/           # 福加运营数据 REST API 工具（已有 java_backend.py）
├── rag/           # RAG 检索工具
└── internal/      # 内部工具（意图解析、页面跳转等）
```
还是保持扁平结构但通过文件命名规范区分。

## 第五步：输出审计报告

请按以下格式输出审计结果：

### A. 必须立即修改（影响架构正确性）
列出所有引用老架构概念且必须修改的文件和具体位置。

### B. 建议重构（提升代码质量）
列出代码质量改进建议（目录结构调整、命名规范化、重复代码消除等）。

### C. 可以安全删除
列出确认无用的文件和代码块。

### D. 保持不动
列出虽然命名不完美但当前不影响功能、暂不修改的部分。

## 第六步：执行重构（待我确认后）

在我确认审计报告后，按以下优先级执行重构：

1. **P0 — Schema 重命名**：更新 `src/schemas/v3_engine.py` 中的模型命名（保持向后兼容：保留老名称作为 alias）
2. **P0 — Mock 工具重写**：将 3 个 Mock 工具重写为 MCP Client 调用骨架（即使 MCP Server 尚未就绪，接口定义要对齐新架构）
3. **P1 — Prompt 更新**：清除 `prompts.yaml` 中所有老架构术语
4. **P1 — 文件头注释批量更新**：所有 `.py` 文件的"对接 V3 引擎"改为"对接算法层"
5. **P2 — 目录结构优化**：如有必要，重组 `src/tools/` 目录
6. **P2 — 无用代码清理**：删除确认无用的文件

**重构红线**：
- 不破坏现有的 10 个福加 API 工具（java_backend.py）的任何功能
- 不破坏 HVAC RAG 问答功能
- 不破坏 FastAPI SSE 服务
- 不破坏多意图识别功能
- 所有修改后必须运行 `pytest src/tests/` 确保现有测试通过
- 每完成一个优先级的工作后单独 commit

## 附加说明

- 本项目是南京福加智能科技有限公司的内部项目，不公开
- Python 环境：conda `energraph` / Python 3.11
- 代码规范遵循 `CLAUDE.md` 中的所有规定（文件头注释、Type Hints、绝对导入、错误处理等）
- 所有 Prompt 修改必须单独 commit（不与代码改动混合）
- 更新完毕后，更新 `AI_CONTEXT.md` 和 `CHANGELOG.md`

请先执行第一步到第五步（阅读+审计），输出审计报告后等我确认，再执行第六步的重构。
```
