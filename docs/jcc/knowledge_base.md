# 项目知识库

## 2026-06-16：项目介绍文档梳理方法

面向对外介绍类文档，应先以 `AI_CONTEXT.md`、`README.md`、`PRD.md`、`MCP_INTERFACE_SPEC.md` 和核心源码为事实基线，再区分“已实现能力”“基础设施已具备”“规划中能力”。尤其要明确 EnerGraph 当前是青山大模型 V3.0 第 3 层决策层，主流程以 LangGraph 三节点 ReAct 循环和 BaseSkill 调度为主；PowerAI / MCP 算法模型、语音助手、可视化报表、Agent 子图主流程接入仍属于演进方向，不能写成已上线能力。
