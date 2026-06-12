# EnerGraph 项目与公司V3.0规划对齐分析报告

**分析日期**: 2026-06-12  
**分析依据**: 福加AI赋能产品规划方案V3.0(docx)、research_agent_trends_2026.md、AI_CONTEXT.md、CLAUDE.md

---

## 一、公司规划与调研方向的匹配度分析

### 1.1 高度匹配的方向（双方一致看好）

**MCP协议标准化工具调用** — 公司规划将9个算法模型封装为MCP Server，调研报告也确认MCP已成为2026年工具调用事实标准。完全对齐。

**多Agent协作与A2A协议** — 公司采用A2A+NATS+NSGA-II仲裁，调研覆盖了Google ADK 2.0+A2A协议以及AutoGen对话式协作。方向一致。

**记忆系统** — 公司设计四层记忆（Redis工作记忆+Milvus短期+Neo4j长期+ES反思），调研覆盖了Claude Dreaming、ICML Graph Memory(MAGMA)、ICLR记忆主题。双方都认识到分层记忆的重要性。

**RAG管线** — 公司选择BGE-M3+Milvus混合检索+BGE-Reranker，调研报告覆盖了RAG三代演进并在Embedding选型中同样推荐BGE-M3。方案吻合。

**自演化/闭环学习** — 公司以自演化为核心战略，调研确认AAAI 2026自演化Agent是热门方向。方向完全一致。

**技能标准化** — 公司用L0-L3四级技能树+JSON Schema，调研覆盖了Claude Skills的SKILL.md标准化。理念相通，方法不同。

**联邦学习** — 双方在分布式Agent技能共享中都提到联邦学习。

### 1.2 公司规划有但调研缺失的（调研需补充）

以下概念在公司V3.0方案中占据重要位置，但调研报告中未涉及或覆盖不足：

| 缺失方向 | 重要程度 | 说明 |
|----------|---------|------|
| **棘轮机制**（技能版本不可逆） | 高 | 公司用Git语义版本管理+仿真回测+人工审批确保Agent正向演化 |
| **CART+LLM混合经验提炼** | 高 | 决策树规则提取+LLM归纳+向量嵌入的三阶段管线 |
| **Event Sourcing反馈采集** | 较高 | Kafka事件流+Flink实时处理+PostgreSQL事件存储 |
| **NSGA-II多目标仲裁** | 较高 | 多Agent冲突时的帕累托最优仲裁算法 |
| **贝叶斯偏好学习** | 较高 | Thompson Sampling从交互中学习用户多目标偏好 |
| **边缘-云协同部署** | 较高 | Jetson Orin/RK3588边缘推理+差量LoRA更新+离线推理 |
| **Guardrails安全体系** | 较高 | NeMo Guardrails+行为沙箱+权限分级(L1-L4)+审计日志 |
| **ADWIN概念漂移检测+EWC增量训练** | 中 | 在线学习流水线，防止模型遗忘历史知识 |
| **预测式异常处置** | 中 | 预判15分钟趋势提前干预，而非等到越限后响应 |
| **CI/CD仿真回测** | 中 | GitHub Actions+ArgoCD+仿真回测+A/B测试 |

### 1.3 调研有但公司规划可补充的

以下方向在调研报告中有价值，但公司V3.0方案中未充分涉及：

| 调研方向 | 建议补充到公司规划 |
|----------|------------------|
| **Anthropic Workflow vs Agent区分** | 避免"过度Agent化"——ETL等确定性流程用Workflow，调度决策用Agent |
| **六大Agent设计模式（Plan-and-Execute）** | 明确Agent引擎核心设计模式，Plan-and-Execute可能比纯ReAct更适合能源调度 |
| **LangGraph子图机制与持久化** | 评估LangGraph作为多Agent编排引擎的可行性 |
| **Agentic RAG（第三代）** | 公司RAG停在Advanced层，应引入多跳推理+自纠正+GraphRAG |
| **Claude Dreaming离线经验回溯** | 在记忆中枢中引入低负载时段离线回顾机制 |
| **Human-in-the-Loop interrupt** | 高风险操作（大功率充放电）自动暂停请求人工确认 |
| **ICML 2026 NaviAgent双层规划** | 上层做日/周级能耗规划，下层做实时设备控制 |
| **DRL(SAC/TD3)在能源中的应用** | 与现有模型互补的深度强化学习方案 |

### 1.4 技术路线差异

| 维度 | 公司选择 | 调研覆盖 | 评价 |
|------|---------|---------|------|
| 基座模型 | Qwen3-235B MoE+QLoRA+DPO | 未做横向对比 | 公司选择合理，调研应补充Qwen3 vs DeepSeek-V3 vs GLM-5对比 |
| 向量数据库 | Milvus | ChromaDB/Qdrant/Milvus/PGVector | 双方一致认可Milvus，调研额外覆盖了PGVector选项 |
| 知识图谱 | Neo4j/NebulaGraph+CDC | 未深入图数据库选型 | 公司领先，调研深度不足 |
| Agent编排 | 完全自研调度中枢 | LangGraph/AutoGen/ADK多框架 | **最大差异**——建议公司评估"自研核心+复用框架"混合路线 |
| RAG代际 | Advanced RAG（第二代） | 覆盖到Agentic RAG（第三代） | 公司可升级到Agentic RAG |
| Embedding | BGE-M3 | BGE-M3/GTE-Qwen2 | 一致推荐BGE-M3，GTE-Qwen2作为备选（与Qwen3同生态） |

---

## 二、EnerGraph项目现状与公司V3.0的代差评估

### 2.1 已具备基础的部分

| 能力 | EnerGraph现状 | V3.0目标 | 差距 |
|------|-------------|---------|------|
| Agent编排 | LangGraph ReAct循环✅ | LangGraph StateGraph | 小——框架一致，需引入子图 |
| 工具调用 | 17个Tool（10真实+3Mock） | MCP Server标准化 | 中——需MCP协议封装 |
| 技能层 | 4个BaseSkill+SKILL_REGISTRY | L0-L3技能工厂 | 大——需技能Schema+验证流水线 |
| RAG | ChromaDB+Naive检索 | BGE-M3+Milvus+混合检索+重排序 | 中——需升级Embedding+检索策略 |
| API服务 | FastAPI+SSE+鉴权✅ | LangServe API | 小——FastAPI可直接演进 |
| LLM支持 | DeepSeek V4/OpenAI/Claude | Qwen3-235B | 中——需添加Qwen3支持 |
| 多意图 | Phase 7完成✅ | 交互式调度NLU | 小——已有意图拆分基础 |

### 2.2 需要大幅升级的部分

| 能力 | 现状 | 需要做的 |
|------|------|---------|
| RAG管线 | ChromaDB+单一向量检索 | BGE-M3+BM25混合+Reranker+Agentic RAG |
| 技能系统 | BaseSkill Python类 | JSON Schema标准化+验证流水线+技能树层级 |
| 状态持久化 | 无（内存态） | PostgresSaver/InMemorySaver+checkpoint |
| 可观测性 | LangSmith基础追踪 | 完整Event Sourcing+审计日志 |

### 2.3 完全空白的部分

| 能力 | 说明 | V3.0中的角色 |
|------|------|-------------|
| **记忆系统** | 无任何记忆层 | 四层记忆（Redis+Milvus+Neo4j+ES） |
| **闭环学习** | 无反馈采集/经验提炼 | Event Sourcing+效果评估+CART+LLM提炼+棘轮 |
| **多Agent协作** | 单Agent架构 | A2A+NATS+NSGA-II+联邦学习 |
| **Guardrails安全** | 无安全防护 | NeMo Guardrails+行为沙箱+权限分级 |
| **知识图谱** | 无 | Neo4j动态知识图谱+CDC |
| **边缘部署** | 纯云端 | Jetson Orin/RK3588+差量LoRA |
| **在线学习** | 无 | ADWIN漂移检测+EWC增量训练 |

---

## 三、EnerGraph演进路线图建议

### Phase A（2026年7-8月）：夯实基座 + 完成遗留Phase

**目标**：从"能跑通的原型"升级为"有生产基础的系统"

1. **完成Phase 5（语音助手）和Phase 6（可视化+报表）** — 这些是已规划的功能
2. **RAG管线升级**（2-3周）
   - Embedding从bge-small-zh-v1.5升级为BGE-M3
   - 引入BM25关键词检索+RRF融合排序
   - 添加BGE-Reranker-v2重排序
   - 预期效果：检索召回率提升30-50%
3. **启用LangGraph持久化**（1-2周）
   - PostgresSaver替代默认内存存储
   - 每次执行自动保存checkpoint
   - 支持断点续跑和时间旅行调试
4. **Human-in-the-Loop**（1周）
   - 在关键操作（设备控制类Tool）前添加interrupt_before
   - 与FastAPI SSE结合推送确认请求

### Phase B（2026年9-10月）：MCP标准化 + Skill工厂

**目标**：工具层和技能层与V3.0对齐

1. **MCP协议试点**（3-4周）
   - 选取3个核心算法模型Tool（parse_intent, query_timedit, verify_physics）封装为MCP Server
   - 搭建MCP Client框架
   - 验证热插拔能力
2. **全量MCP迁移**（2-3周）
   - 剩余Tool逐步迁移为MCP Server
   - JSON Schema描述所有工具接口
3. **Skill Schema标准化**（2-3周）
   - 参考V3.0的L0-L3技能树设计
   - 为每个Skill定义JSON Schema（前置条件、执行步骤、预期效果）
   - BaseSkill升级为支持子图的模块化Skill
4. **Plan-and-Execute模式引入**（1-2周）
   - 复杂能源优化任务：先由Planner节点生成计划，再由Executor逐步执行
   - 与现有ReAct循环共存

### Phase C（2026年11月-2027年1月）：记忆 + 闭环学习MVP

**目标**：引入V3.0最核心的自演化能力

1. **两层记忆MVP**（2-3周）
   - 工作记忆：Redis，保存当前对话和执行状态
   - 短期记忆：Milvus，记录近期调度结果和用户反馈
   - （长期记忆Neo4j和反思记忆ES留到Phase D）
2. **闭环学习引擎MVP**（3-4周）
   - 简化版Event Sourcing：记录DecisionEvent+ToolCallEvent+OutcomeEvent
   - 效果评估器：多维加权评估（收益达成率+安全合规率+预测偏差+用户满意度）
   - 简化版经验提炼：LLM归纳高价值执行轨迹
3. **Guardrails基础**（1-2周）
   - 输入过滤：Prompt Injection检测
   - 输出审查：硬约束检查（如SOC下限、需量上限）
   - 权限分级：至少实现L1-L2两级
4. **Reflection模式**（1-2周）
   - 能耗报告生成后，由评估Agent审核并指出问题
   - 与闭环学习引擎联动积累经验

### Phase D（2027年2月+）：高级能力（可能超出实习期）

1. 知识图谱（Neo4j）+GraphRAG
2. 多Agent协作（A2A+NATS）
3. Dreaming式离线经验回溯
4. 完整四层记忆架构
5. 边缘-云协同部署
6. 在线学习（ADWIN+EWC）
7. 完整四级技能验证流水线

---

## 四、具体代码/架构改动建议

### 4.1 需要新增的模块

| 新模块 | 位置 | 优先级 | 说明 |
|--------|------|--------|------|
| MCP Server封装层 | `src/mcp/` | P0 | 将现有Tool封装为MCP Server |
| 记忆层 | `src/memory/` | P1 | Redis工作记忆+Milvus短期记忆 |
| 闭环学习引擎 | `src/learning/` | P1 | Event Sourcing+评估+提炼 |
| Guardrails | `src/guardrails/` | P2 | 输入输出安全过滤 |
| 知识图谱接口 | `src/knowledge_graph/` | P3 | Neo4j客户端+CDC |

### 4.2 需要重构的模块

| 现有模块 | 改动 | 优先级 |
|---------|------|--------|
| `src/tools/` | 从普通函数重构为MCP Server | P0 |
| `src/skills/` | BaseSkill升级为支持子图+JSON Schema | P1 |
| `src/pipelines/rag_ingest.py` | 升级为BGE-M3+混合检索+Reranker | P0 |
| `src/graph/builder.py` | 添加PostgresSaver+interrupt节点 | P0 |
| `src/config/settings.py` | 添加记忆/安全/MCP相关配置 | P1 |
| `src/config/prompts.yaml` | 添加Plan-and-Execute/Reflection相关Prompt | P1 |

### 4.3 需要修改的配置

| 配置文件 | 改动 |
|---------|------|
| `.env` | 添加Redis/Milvus/Neo4j连接信息、Guardrails开关 |
| `requirements.txt` | 添加mcp-server、redis、pymilvus、neo4j-driver、bge-reranker等依赖 |
| `config/agent_config.yaml` | 添加记忆TTL、安全阈值、MCP配置 |

---

## 五、AI_CONTEXT.md和CLAUDE.md更新建议

### AI_CONTEXT.md应新增/更新：

1. **§1.3 最终目标** — 添加V3.0自演化Agent对齐路线图
2. **§2 技术架构** — 新增MCP协议层、记忆层、闭环学习引擎的架构说明
3. **§4 工具注册表** — 标注每个Tool的MCP迁移状态
4. **§5 开发阶段** — 新增Phase A/B/C/D与公司V3.0 Phase 1-6对齐
5. 新增章节：**记忆系统设计**、**闭环学习引擎设计**、**Guardrails安全设计**

### CLAUDE.md应新增/更新：

1. **架构红线** — 新增：MCP协议规范（Tool必须通过MCP Server暴露）、记忆写入规范（每次调度必须写入工作记忆）
2. **测试规范** — 新增：Guardrails规则测试、闭环学习效果验证测试
3. **新增章节** — MCP Server开发规范、记忆管理规范、安全审查规范

---

## 六、短期（1-2个月）最有价值的3件事

### 第1件：RAG管线升级（BGE-M3混合检索+重排序）
**预估时间**：2-3周  
**理由**：RAG是Agent的"知识基座"，改动范围仅限`src/pipelines/`和`src/tools/query_hvac_knowledge.py`，但对回答质量的提升立竿见影（混合检索召回率预计提升30-50%），且直接对齐V3.0明确的技术选型（BGE-M3+混合检索+Reranker）。这是投入产出比最高的改进。

### 第2件：PostgresSaver持久化 + Human-in-the-Loop
**预估时间**：1-2周  
**理由**：代码改动极小（约10-20行配置），但一步到位获得三大能力——对话状态持久化、执行轨迹记录（闭环学习的前置条件）、关键决策人工审批（能源调度场景的信任基础）。这是从"演示系统"到"可部署系统"的分水岭。

### 第3件：MCP协议试点（3个核心工具）
**预估时间**：3-4周  
**理由**：MCP是V3.0的"通用语言"——公司规划中所有算法模型都通过MCP Server暴露。先选3个Tool（如parse_intent、query_timedit、verify_physics）做试点，搭建MCP Client/Server框架，验证热插拔能力。后续渐进式扩展剩余14个Tool，避免一次性全量迁移的风险。

---

## 七、调研改进建议

基于公司V3.0方向，调研报告应在以下方面补充：

### P0（必须补充）
1. **Agent安全与Guardrails** — NeMo Guardrails/行为沙箱/权限分级/审计日志
2. **Agent编排框架横向评测** — LangGraph vs AutoGen vs ADK vs 自研的决策矩阵
3. **Agentic RAG技术方案** — 多跳推理+自纠正+GraphRAG（与公司的Neo4j结合）
4. **边缘-云协同Agent部署** — 模型压缩+差量更新+离线推理

### P1（重要补充）
5. **Agent设计模式深度分析** — 特别是Plan-and-Execute和Reflection在能源调度中的应用
6. **Agent可观测性** — OpenTelemetry for Agent、LangSmith深度使用
7. **基座模型横向评测** — Qwen3 vs DeepSeek-V3 vs GLM-5在能源领域的对比
8. **在线学习/持续演化方法论** — ADWIN/EWC/PackNet/HAT对比

### P2（建议补充）
9. Workflow vs Agent适用边界
10. Human-in-the-Loop实现模式对比
11. Agent CI/CD最佳实践
12. HVAC/能源行业Agent深度案例分析

---

*本报告由AI生成，建议与项目负责人讨论后确认方向。*
