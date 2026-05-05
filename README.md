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
├── AI_CONTEXT.md              # 动态项目状态文档
├── README.md                  # 本文件
├── .gitignore                 # Git 忽略规则
├── .env.example               # 环境变量模板
├── requirements.txt           # Python 依赖
├── config/
│   └── agent_config.yaml      # Agent 配置
├── src/
│   ├── agent/                 # Agent 核心逻辑
│   │   ├── graph.py           # LangGraph 状态图
│   │   ├── nodes.py           # ReAct 节点
│   │   └── state.py           # 状态模型
│   ├── tools/                 # Mock 工具函数
│   │   ├── compute_metrics.py # 统计指标
│   │   ├── compete_price.py   # 电价对比
│   │   └── calc_benefit.py    # 收益计算
│   ├── models/
│   │   └── data_models.py     # 数据模型
│   └── frontend/
│       └── app.py             # Streamlit 界面
├── docs/
│   └── API_INTERFACE.md       # 接口规范
└── tests/                     # 测试（预留）
```

## 技术栈

- **核心框架**: LangGraph 0.2.16
- **大模型**: OpenAI GPT-4 / Claude (可配置)
- **数据验证**: Pydantic 2.9.0
- **前端**: Streamlit 1.39.0
- **配置管理**: PyYAML + python-dotenv
- **Python 版本**: 3.9+

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd EnerGraph

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

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
| `compete_price` | 识别峰谷套利机会 | grid_price | 价格对比结果 |
| `calc_benefit` | 计算调度收益 | load, solar, grid_price, soc, max_power | 收益计算结果 |

## 开发指南

### 多人协作

1. **新成员入职**：先阅读 `AI_CONTEXT.md` 了解项目状态
2. **代码提交**：提交信息格式 `[模块] 简短描述`
3. **环境配置**：每人维护自己的 `.env` 文件（不提交到 Git）
4. **接口规范**：参考 `docs/API_INTERFACE.md`

### 注意事项

- ⚠️ **敏感信息**：绝不提交 `.env` 文件到 Git
- ⚠️ **依赖版本**：修改依赖后更新 `requirements.txt`
- ⚠️ **文档同步**：架构变更后更新 `AI_CONTEXT.md`

## 后续规划

- [ ] 集成真实的大模型 API 调用
- [ ] 替换 Mock 工具为实际调度算法
- [ ] 添加单元测试
- [ ] 支持多语言输出（中英文）
- [ ] 优化前端交互体验

## 许可证

内部项目，未公开

## 联系方式

如有问题请联系项目负责人
