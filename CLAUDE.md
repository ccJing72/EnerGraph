# CLAUDE.md — EnerGraph（青山大模型）自演化智能能源 Agent 项目协作准则

> **本文是项目固定策略与行为规范。** Claude 每次会话自动加载此文件。人类协作者也需遵循同等标准。

---

## 项目宗旨

构建青山大模型 V3.0 五层架构中 **决策层 + 自演化引擎层** 的 Agent 实现（项目代号 EnerGraph）。Agent 作为系统的"编排大脑"，**自身不做数值计算**，而是：

- **意图理解**：解析用户自然语言 / ERP JSON 中的业务意图，拆解为结构化任务
- **工具调度**：通过 **MCP 协议**调用算法模型层的计算引擎（预测/诊断/优化），通过 REST API 查询福加运营数据
- **决策解释**：将算法模型返回的数值结果转化为用户可理解的 Markdown 报告（能耗收益、碳排下降、设备安全边界）

**业务身份**：EnerGraph 的第一个落地身份是 **PowerAI 储能调度智能体**（光伏预测 + 负荷预测 → 综合决策 → 充放电策略）。未来通过不同 Skill 配置可扩展为能效诊断、碳管理等其他智能体。

**性质**：企业级落地方案，不公开。

---

## 架构红线（Architectural Constraints）

1. **Agent 定位**：Agent 只是"编排大脑"，**绝对禁止**在 Python/LangGraph 代码中手写任何能源计算、峰谷套利公式、热力学推导、预测算法。所有计算必须通过 `Tools`（MCP Server 或 REST API）获取结果。
2. **MCP 优先**：算法模型层的计算引擎（预测/诊断/优化模型）必须通过 MCP 协议调用，Agent 不得直接依赖算法模型的内部实现。福加运营数据工具保持 REST API 方式。
3. **解耦设计**：Prompt 必须外部化（存入 YAML/Markdown），配置与代码严格分离。
4. **类型严格**：`AgentState` 使用 `TypedDict` + `Annotated` reducer 定义（LangGraph 官方规范）；Tool Inputs/Outputs 使用 Pydantic BaseModel 定义，禁止裸 dict 作为工具参数。

---

## 状态同步铁律（State Sync Protocol）

- 每次执行文件修改、重构模块后，**必须主动更新** `CHANGELOG.md`（完整变更记录）和 `AI_CONTEXT.md` 的进度表（§5）；`AI_CONTEXT.md` §6 仅保留最近 5 条摘要。
- 每次回答架构问题前，**必须先读取** `AI_CONTEXT.md` 全文了解当前项目状态。

---

## 代码规范

### 文件头注释（强制）
每个 `.py` 文件第一行必须是模块 docstring：

```python
"""<模块名> — <一句话说明职责>

所属层：<config / schemas / tools / graph / frontend / utils / pipelines / skills / services / memory / tests>
依赖：<列出主要依赖>
对接算法层：<光伏预测 / 电负荷预测 / 冷负荷预测 / 电价预测 / 设备健康诊断 / 机房能效诊断 / 制冷寻优 / 储能调度优化 / 碳排预测，若无则填 N/A>
"""
```

### 函数注释
- 所有 `public` 函数必须有 **Type Hints** + **Docstring**（Args / Returns / Raises）
- 行内注释只在"为什么这样做"不明显时写，不写"做了什么"

### 导入规范
- 统一**绝对导入**：`from src.config import settings`，禁止相对导入
- 分组顺序：标准库 → 第三方库 → 本项目模块，组间空一行

### 命名规范
- 文件/函数/变量：`snake_case`
- 类：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`

### 错误处理
Tool 函数必须 `try-except`，异常统一返回 `{"error": "工具名: 错误信息"}`，防止底层引擎超时导致 Agent 崩溃。

---

## Git 规范

### 分支策略
- **main**：保护分支，始终保持可运行，不直接在此开发
- **feature/<name>**：功能分支（如 `feature/v3-tools`）
- **fix/<name>**：Bug 修复分支（如 `fix/graph-routing`）
- 工作流：`feature/xxx → PR → merge main`
- 紧急修复可直接推 main，但必须在修改日志注明"hotfix"

### 提交格式
```
[模块] 简短动词短语描述变更内容
```

| 标签 | 范围 |
|------|------|
| `[tools]` | `src/tools/` |
| `[graph]` | `src/graph/` |
| `[schemas]` | `src/schemas/` |
| `[config]` | `src/config/`, `config/` |
| `[frontend]` | `src/frontend/` |
| `[utils]` | `src/utils/` |
| `[docs]` | `AI_CONTEXT.md`, `CHANGELOG.md`, `README.md`, `docs/` |
| `[refactor]` | 跨模块重构 |
| `[fix]` | Bug 修复 |
| `[test]` | `src/tests/` |

### 推送流程
```bash
git add <具体文件>           # 禁止 git add .（防止误提交 .env）
git commit -m "[模块] 描述"
git pull --rebase origin main
git push origin main
```

### .env 保护
`.env` 包含 API Key，**绝对禁止提交到 Git**。`.gitignore` 已包含。误提交后立即联系负责人轮换 Key。

---

## 测试规范

- 文件位置：`src/tests/test_<模块名>.py`，运行：`pytest src/tests/`
- **新增 Tool 函数必须写测试**：正常输入、边界值、非法输入
- **修 Bug 先写复现测试，再修复**
- Tool 层测试纯计算/Mock，不依赖 LLM / API Key

---

## 文档维护规则

### 修改 AI_CONTEXT.md 的时机
| 变更类型 | 更新章节 |
|----------|----------|
| 新增/修改 Tool | §4 + `CHANGELOG.md` |
| 新增/修改 Graph 节点或边 | §2 + `CHANGELOG.md` |
| 新增/修改 Pydantic 数据模型 | §4 + `CHANGELOG.md` |
| 新增/删除文件或目录 | §3 + `CHANGELOG.md` |
| 修改依赖 | §2.1 + `README.md` + `CHANGELOG.md` |
| 完成 Phase | §5 + `CHANGELOG.md` |

### 变更日志规则
- **完整记录**写入 `CHANGELOG.md`（每次变更必记）
- **摘要**同步至 `AI_CONTEXT.md` §6（仅保留最近 5 条，超出则移除最早条目）
- 完成有意义的功能模块或阶段后记录
- 多次小修改积累后统一记录一条
- 重要架构变更或 Bug 修复后立即记录

格式：`| YYYY-MM-DD | 简短描述 | 真实姓名 |`

### AI 助手行为准则
1. **先读完 `AI_CONTEXT.md` 全文**再动手
2. 读相关模块的文件头注释，了解各层职责及对接的算法模型
3. 完成工作后**必须更新 `CHANGELOG.md`** + 同步 `AI_CONTEXT.md` §6 摘要（保留最近 5 条）+ 更新 `AI_CONTEXT.md` 对应章节（如 §2/§3/§4/§5）
4. 不确定架构决策时，在 `CHANGELOG.md` 注明"待确认"，等人类审查

---

## 扩展原则

### 新增 Skill（业务技能）
1. `src/skills/` 下新建文件，文件头注明 SOP 流程、调用的 Tools、Prompt keys
2. 在 `src/skills/__init__.py` 的 `SKILL_REGISTRY` + `SKILL_DESCRIPTIONS` 注册
3. Skill 内部只编排 Tools，不直接调用 LLM（LLM 调用在 Graph 节点层）
4. 更新 `AI_CONTEXT.md` §3 + §4

### 新增 Tool（算法模型 MCP 工具 / 运营数据 API 工具）
1. `src/tools/` 下新建文件，文件头注明对接的算法模型（MCP）或福加 API（REST）
2. 在 `src/tools/__init__.py` 的 `TOOL_REGISTRY` + `TOOL_SCHEMAS` 注册
3. 返回 Pydantic 模型（定义在 `src/schemas/`），禁止裸 dict
4. **算法模型工具**：通过 MCP Client 调用算法团队的 MCP Server，Agent 不直接实现算法逻辑
5. **运营数据工具**：直接调用福加 Java 后端 REST API，参数解析和 Token 刷新在 Tool 代码内处理
6. 更新 `AI_CONTEXT.md` §4

### 新增 Graph 节点
1. 在 `src/graph/nodes.py` 添加节点函数
2. 在 `src/graph/builder.py` 注册到状态图
3. 更新 `AI_CONTEXT.md` §2

### Prompt 管理规范（强制集中管理 + 版本控制）

**原则**: 所有大模型 Prompt 统一收拢至 `src/config/prompts.yaml` 集中管理，任何节点代码不得硬编码 Prompt 字符串。

**存放规则**:
- **唯一入口**: `src/config/prompts.yaml` 是 System Prompt / 模板的**唯一存放位置**。禁止将 Prompt 分散到 Python 代码、`.env`、Markdown 或其他 YAML 文件中
- **加载方式**: 通过 `src/config/settings.py` → `settings.prompts` 统一加载，Graph 节点只引用 key，不自行读文件
- **命名规范**: Prompt key 使用 `snake_case`，按节点/场景命名（如 `cognitive_parser`, `interpreter_generator`, `hvac_expert`, `action_agent_nav_hint`）
- **动态数据注入**: 动态配置数据（路由表、工具列表、站点参数等）应独立成 YAML 配置文件（如 `config/routes.yaml`、`config/site_mapping.yaml`），在运行时通过 `settings` 加载并动态注入到 system prompt 中，不直接写入 `prompts.yaml`。**原则：静态推理规则放 prompts.yaml，动态配置数据放独立 config 文件**

**版本控制要求**:
- 每次修改 `prompts.yaml` 必须以 `[config]` 标签单独 commit，commit message 写明修改的 prompt key 和改动目的
- 禁止将 Prompt 调优和代码改动混在同一个 commit 中——Prompt 迭代与代码变更独立溯源
- 多人协作时，prompts.yaml 的修改冲突需人工确认，禁止自动合并

**代码审查红线**:
- PR diff 中出现任何硬编码的 Prompt 字符串（含 `system=`、`SystemMessage(content=` 等），审查人必须拒绝合并
- 例外：单元测试中 mock LLM 调用时可使用占位字符串，但需加注释 `# mock prompt, 不从 prompts.yaml 加载`

### RAG 扩展
- 入库：`src/pipelines/rag_ingest.py`
- 检索：在 Graph 节点中调用，写入 `AgentState.context`

---

> **本文优先级**：当本文与 `AI_CONTEXT.md` 有冲突时，以本文为准。本文变更需同步更新 `CHANGELOG.md`。
