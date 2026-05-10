# EnerGraph - 家庭能源 AI 调度解释 Agent

基于 LangGraph 的家庭能源调度策略解释系统 Demo

## 项目简介

本项目是一个轻量级的 MVP 原型，旨在通过 ReAct (Thought-Action-Observation) 循环，为用户提供可理解、可溯源的家庭能源调度策略解读。

**核心功能**：
- 基于光伏、储能、电网购售电数据进行调度策略分析
- 通过 Mock 工具函数模拟指标统计、电价对比、收益计算
- 生成结构化的 Markdown 格式报告
- 提供 Streamlit 可视化交互界面

## 项目结构

```
EnerGraph/
├── CLAUDE.md                      # 协作准则（Claude 自动加载）
├── AI_CONTEXT.md                  # 项目知识库（单点真相）
├── config/
│   └── agent_config.yaml          # Agent 配置
├── src/
│   ├── config/
│   │   └── settings.py            # 统一配置加载
│   ├── schemas/                   # Pydantic 数据模型
│   │   ├── input_schemas.py
│   │   ├── output_schemas.py
│   │   └── agent_state.py
│   ├── tools/                     # 工具函数 + TOOL_REGISTRY
│   │   ├── compute_metrics.py     # 统计指标
│   │   ├── compare_price.py       # 电价对比
│   │   └── calc_benefit.py        # 收益计算
│   ├── agents/                    # 多 Agent 目录
│   │   ├── base.py                # Agent 基类
│   │   └── energy/                # 调度解释 Agent
│   │       ├── graph.py           # LangGraph 状态图
│   │       ├── nodes.py           # ReAct 节点
│   │       └── prompts.py         # Prompt 模板
│   ├── pipelines/                 # 数据处理流水线（预留）
│   ├── memory/                    # 记忆管理（预留）
│   ├── services/                  # FastAPI 服务层（预留）
│   ├── utils/
│   │   └── report_builder.py      # 报告生成
│   └── frontend/
│       └── app.py                 # Streamlit 界面
├── docs/
│   └── API_INTERFACE.md           # 接口规范
└── src/tests/                     # 测试
```

## 技术栈

- **核心框架**: LangGraph 0.2.x
- **大模型**: LangChain + OpenAI/Claude（可配置）
- **数据验证**: Pydantic 2.x
- **前端**: Streamlit 1.39
- **配置管理**: PyYAML + python-dotenv
- **Python 版本**: ≥3.11

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/Webr1ng/EnerGraph.git
cd EnerGraph

# 创建 conda 环境（Python 3.11）
conda create -n energraph python=3.11 -y
conda activate energraph

# 安装依赖
pip install -r requirements.txt
```

> Windows 用户若 `conda` 不在 PATH，需先运行 Anaconda Prompt。详见 `AI_CONTEXT.md` §7.1。

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# OPENAI_API_KEY=your_key_here
```

### 3. 运行 Streamlit 前端

```bash
streamlit run src/frontend/app.py
```

浏览器会自动打开 `http://localhost:8501`

### 4. 使用示例

1. 在侧边栏勾选"使用示例数据"
2. 点击"🚀 运行 Agent"按钮
3. 查看生成的调度策略报告
4. 展开"工具调用详情"查看中间结果

## 核心架构

### ReAct 循环流程

```
输入数据 → call_tools_node → generate_report_node → 输出报告
            (调用3个工具)      (生成Markdown报告)
```

### 工具函数说明

| 工具 | 功能 | 输入 | 输出 |
|-----|------|-----|------|
| `compute_metrics` | 统计负载、光伏、电价指标 | load, solar, grid_price | 统计结果字典 |
| `compare_price` | 识别峰谷套利机会 | grid_price | 价格对比结果 |
| `calc_benefit` | 计算调度收益 | load, solar, grid_price, soc, max_power | 收益计算结果 |

## 开发指南

### 多人协作

1. **新成员入职**：先阅读 `AI_CONTEXT.md` 了解项目全貌，再读 `CLAUDE.md` 了解协作准则
2. **代码规范**：严格遵循 `CLAUDE.md` 中的编码/Git/测试/文档规范
3. **环境配置**：每人维护自己的 `.env` 文件（不提交到 Git）
4. **接口规范**：参考 `docs/API_INTERFACE.md`
5. **文档同步**：完成后必须更新 `AI_CONTEXT.md` 对应章节 + 修改日志

### 注意事项

- ⚠️ **敏感信息**：绝不提交 `.env` 文件到 Git
- ⚠️ **依赖版本**：修改依赖后更新 `requirements.txt`
- ⚠️ **文档同步**：架构变更后更新 `AI_CONTEXT.md`

## 后续规划

- [ ] 端到端测试（配置真实 API Key）
- [ ] 替换 Mock 工具为实际调度算法（业务方负责）
- [ ] 集成 RAG 知识库
- [ ] 支持多语言输出（中英文）
- [ ] CI/CD 配置
