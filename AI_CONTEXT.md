# EnerGraph - 家庭能源 AI 调度解释 Agent

## 项目状态
**当前阶段**: Phase 4 - Demo 开发完成  
**最后更新**: 2026-05-05  
**开发模式**: 敏捷开发 MVP/Demo

---

## 项目概述
构建一个基于 LangGraph 的家庭能源 AI 调度解释 Agent 原型，通过 ReAct 循环为用户提供可理解、可溯源的能源调度策略解读。

**核心目标**: 快速打通 ReAct 循环，实现基本交互展示，避免过度设计。

---

## 技术架构

### 技术栈
- **核心框架**: LangGraph (ReAct 循环)
- **大模型**: OpenAI/Claude API (可配置)
- **数据验证**: Pydantic
- **前端**: Streamlit
- **配置管理**: YAML + python-dotenv
- **Python 版本**: 3.9+

### 架构模式
采用 **ReAct (Thought-Action-Observation)** 循环：
1. **Thought**: 大模型分析输入数据，规划工具调用
2. **Action**: 调用预设工具（compute_metrics, compete_price, calc_benefit）
3. **Observation**: 接收工具返回数据，完成归因分析
4. **Memory**: 存储上下文，支持多轮交互
5. **Final Answer**: 生成结构化报告

---

## 项目结构
```
EnerGraph/
├── AI_CONTEXT.md              # 本文件 - 动态项目状态
├── README.md                  # 项目说明
├── .gitignore                 # Git 忽略规则
├── .env.example               # 环境变量模板
├── requirements.txt           # 依赖清单
├── config/
│   └── agent_config.yaml      # Agent 配置
├── src/
│   ├── agent/                 # Agent 核心逻辑
│   │   ├── graph.py           # LangGraph 状态图
│   │   ├── nodes.py           # ReAct 节点
│   │   └── state.py           # 状态模型
│   ├── tools/                 # Mock 工具函数
│   │   ├── compute_metrics.py
│   │   ├── compete_price.py
│   │   └── calc_benefit.py
│   ├── models/
│   │   └── data_models.py     # 数据模型
│   └── frontend/
│       └── app.py             # Streamlit 界面
├── docs/
│   └── API_INTERFACE.md       # 接口规范
└── tests/                     # 测试（预留）
```

---

## 核心代码约束

### 1. 代码风格
- 最小化实现：只写必需代码，避免过度抽象
- 函数命名：清晰的英文命名，遵循 PEP 8
- 类型注解：关键函数必须添加类型提示
- 注释：仅在非显而易见的逻辑处添加

### 2. 数据流规范
- **输入**: 通过 Pydantic 模型验证（forecast_data, system_state, basic_info）
- **工具调用**: 返回结构化 JSON 数据
- **输出**: Markdown 格式报告，支持中英文

### 3. 配置管理
- 敏感信息（API Key）存储在 `.env`，不提交到 Git
- 业务配置（模型选择、工具列表）存储在 `config/agent_config.yaml`
- 环境变量通过 `python-dotenv` 加载

### 4. Git 协作规范
- 提交前检查 `.gitignore` 是否覆盖敏感文件
- 提交信息格式：`[模块] 简短描述`（如：`[agent] 实现 ReAct 节点逻辑`）
- 新成员入职前阅读本文档和 `README.md`

---

## 已完成进度
- [x] Phase 1: 目录结构规划
- [x] Phase 2: 初始化文件生成
  - [x] AI_CONTEXT.md
  - [x] .gitignore
  - [x] .env.example
  - [x] requirements.txt
- [x] Phase 3: 核心逻辑开发
  - [x] 定义数据模型 (`src/models/data_models.py`)
  - [x] 实现 3 个 Mock 工具 (`src/tools/*.py`)
  - [x] 定义 Agent 状态 (`src/agent/state.py`)
  - [x] 实现 ReAct 节点 (`src/agent/nodes.py`)
  - [x] 构建 LangGraph 状态图 (`src/agent/graph.py`)
  - [x] 生成配置文件 (`config/agent_config.yaml`)
  - [x] 开发 Streamlit 前端 (`src/frontend/app.py`)
- [x] Phase 4: 文档收尾
  - [x] 生成 `README.md`
  - [x] 生成 `docs/API_INTERFACE.md`
  - [x] 最终更新本文档

---

## 下一步 TODO
- [ ] 测试运行 Demo
- [ ] 集成真实大模型 API
- [ ] 优化工具函数逻辑
- [ ] 添加单元测试
- [ ] 多语言支持

---

## 最新改动记录 (2026-05-05)

### 架构优化
1. **ReAct 模式增强**:
   - 重命名 `call_tools_node` → `agent_node`，明确 ReAct 决策职责
   - 添加 `next_action` 字段，预留 LLM 决策扩展点
   - 在代码注释中标注 TODO，便于后续集成真正的 LLM Thought 循环

2. **RAG 扩展支持**:
   - `AgentState` 新增 `context` 字段（存储 RAG 检索结果）
   - `AgentState` 新增 `history` 字段（支持多轮对话）
   - 架构设计便于后续集成向量数据库和知识库

3. **Git 仓库**:
   - GitHub 仓库: https://github.com/Webr1ng/EnerGraph.git
   - 分支: main
   - 状态: 已推送初始版本

---

## 注意事项
1. **敏感信息**: 绝不提交 `.env` 文件到 Git
2. **依赖版本**: `requirements.txt` 锁定版本号，避免环境差异
3. **文档同步**: 每次架构调整后立即更新本文档
4. **轻量原则**: Demo 阶段优先功能打通，避免过度工程化
5. **ReAct 升级路径**: 当前为简化实现，集成 LLM 后可实现完整 ReAct 循环
