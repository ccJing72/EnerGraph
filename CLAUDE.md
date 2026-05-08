# CLAUDE.md — EnerGraph 项目协作准则

> **本文是项目固定策略与行为规范。** Claude 每次会话自动加载此文件。人类协作者也需遵循同等标准。

---

## 项目宗旨

构建基于 LangGraph 的家庭能源 AI 调度解释 Agent。以 **ReAct（Thought → Action → Observation）循环** 驱动大模型进行策略归因分析，输出结构化报告。

**性质**：企业级落地方案（支持上云 / 本地部署），不公开。

---

## 代码规范

### 文件头注释（强制）
每个 `.py` 文件第一行必须是模块 docstring：

```python
"""<模块名> — <一句话说明职责>

所属层：<tools / agents / schemas / config / utils / frontend>
依赖：<列出主要依赖>
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
工具函数必须 `try-except`，异常统一返回 `{"error": "工具名: 错误信息"}`。

---

## Git 规范

### 分支策略
- **main**：保护分支，始终保持可运行，不直接在此开发
- **feature/<name>**：功能分支（如 `feature/rag-ingest`）
- **fix/<name>**：Bug 修复分支（如 `fix/calc-benefit-negative`）
- 工作流：`feature/xxx → PR → merge main`
- 紧急修复可直接推 main，但必须在修改日志注明"hotfix"

### 提交格式
```
[模块] 简短动词短语描述变更内容
```

| 标签 | 范围 |
|------|------|
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
- **新增工具函数必须写测试**：正常输入、边界值（全零数组）、非法输入（长度≠24）
- **修 Bug 先写复现测试，再修复**
- 工具层测试纯计算，不依赖 LLM / API Key

---

## 文档维护规则

### 修改 AI_CONTEXT.md 的时机
| 变更类型 | 更新章节 |
|----------|----------|
| 新增/修改工具 | §4 + 修改日志 |
| 新增/修改 Agent 节点或图 | §2 + 修改日志 |
| 新增/修改数据模型 | §4 + `docs/API_INTERFACE.md` + 修改日志 |
| 新增/删除文件或目录 | §3 + 修改日志 |
| 修改依赖 | §2.1 + `README.md` + 修改日志 |
| 完成 Phase | §5 + 修改日志 |

### 修改日志更新时机
- 完成有意义的功能模块或阶段后
- 多次小修改积累后统一记录一条
- 重要架构变更或 Bug 修复后

格式：`| YYYY-MM-DD | 简短描述 | 真实姓名 |`

### AI 助手行为准则
1. **先读完 `AI_CONTEXT.md` 全文**再动手
2. 读相关模块的文件头注释，了解各层职责
3. 完成工作后**必须更新 `AI_CONTEXT.md` 对应章节 + 修改日志**
4. 不确定架构决策时，在修改日志注明"待确认"，等人类审查

---

## 扩展原则

### 新增工具
1. `src/tools/` 下新建文件，文件头写模块简述
2. 在 `src/tools/__init__.py` 的 `TOOL_REGISTRY` + `TOOL_SCHEMAS` 注册
3. 更新 `AI_CONTEXT.md` §4.2

### 新增 Agent 节点
1. 在 `src/agents/energy/nodes.py` 添加节点
2. 在 `src/agents/energy/graph.py` 注册
3. 更新 `AI_CONTEXT.md` §2.2

### RAG 扩展
- 利用 `AgentState.context` 字段
- 入库：`src/pipelines/rag_ingest.py`
- 检索：在 `agent_node` 中调用，写入 `state["context"]`

---

> **本文优先级**：当本文与 `AI_CONTEXT.md` 有冲突时，以本文为准。本文变更需同步更新 `AI_CONTEXT.md` 修改日志。
