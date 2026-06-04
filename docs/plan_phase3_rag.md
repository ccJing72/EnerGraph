# EnerGraph — Phase 3: RAG 质量优化 + 减少幻觉

**目标**: 让 HVAC 问答更准确，低置信度时明确说"不知道"而非编造，并在回答中引用检索来源。  
**前置条件**: Phase 2 完成（API 层可用，Skill 基类建议先完成 `plan_skills_base_class.md`）  
**完成标志**: 低相关问题返回置信度标志 + 拒答；回答末尾标注检索来源；pytest 通过

---

## 业务场景

### 场景 1: 精准问答
用户问："冷水机组 COP 偏低如何处理？"

Agent 应：
1. 调用 `query_hvac_knowledge` 检索到相关文档（distance < 0.4）
2. 流式回答，末尾标注来源："依据：GB/T 18430.1 冷水机组性能测试规范..."

### 场景 2: 低置信拒答
用户问："量子力学在空调中的应用？"

Agent 应：
1. 检索结果 distance > 0.6，标记 `low_confidence: true`
2. 明确回答："知识库中暂无相关信息，建议咨询专业研究人员。"
3. 不编造答案

---

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/tests/test_hvac_quality.py` | RAG 质量测试（低置信 / 拒答 / 引用来源） |

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `src/tools/query_hvac_knowledge.py` | distance 阈值过滤 + MMR 去重 |
| `src/skills/hvac_expert_skill.py` | 完善 execute()：置信度判断 + 拒答 + 引用来源 SOP |
| `src/config/prompts.yaml` | 新增 `hvac_refusal` + `hvac_citation_format` Prompt |
| `src/graph/nodes.py` | `interpreter_generator` 识别 low_confidence 标志 |

---

## 子任务（每个子任务 = 一个 commit）

### T1: 相关度阈值过滤
- **文件**: `src/tools/query_hvac_knowledge.py`
- **改动**:
  - 检索结果中若 top-1 distance > `CONFIDENCE_THRESHOLD`（默认 0.6），追加字段 `low_confidence: true`
  - `HVACKnowledgeResult` 新增 `low_confidence: bool = False` 字段
  - 阈值从 `config/agent_config.yaml` 读取，支持运行时调整
- **验收**: 问"量子力学"返回 `low_confidence=true`，问"冷水机组COP"返回 `low_confidence=false`

### T2: 低置信度拒答 Prompt
- **文件**: `src/config/prompts.yaml`, `src/skills/hvac_expert_skill.py`
- **改动**:
  - `prompts.yaml` 新增 `hvac_refusal` Prompt：
    ```
    若检索结果中 low_confidence=true，请直接回答：
    "知识库中暂无相关信息，建议查阅相关规范或咨询专业人员。"
    不得编造答案或猜测性回答。
    ```
  - `HVACExpertSkill.execute()` 完善：检查工具结果中 `low_confidence` 标志，若为 true 则将 `hvac_refusal` Prompt 注入 interpreter_generator 的 system message
- **验收**: 低置信度问题不产生幻觉回答，输出拒答模板

### T3: 报告引用来源
- **文件**: `src/config/prompts.yaml`, `src/skills/hvac_expert_skill.py`
- **改动**:
  - `prompts.yaml` 新增 `hvac_citation_format` Prompt：
    ```
    回答末尾必须标注依据来源，格式：
    ---
    **依据**：[检索片段标题/摘要，不超过 50 字]
    ```
  - `HVACExpertSkill.execute()` 完善：在工具结果中传递检索片段摘要给 LLM
- **验收**: 正常回答末尾有"依据：..."标注，拒答时不显示来源

### T4: 检索冗余优化（MMR）
- **文件**: `src/tools/query_hvac_knowledge.py`
- **改动**:
  - ChromaDB query 改用 MMR（Maximal Marginal Relevance）减少重复：
    ```python
    collection.query(
        query_texts=[query],
        n_results=TOP_K,
        include=["documents", "distances", "metadatas"],
    )
    ```
  - `TOP_K` 从 5 降到 3，减少冗余
  - 对重复文档（相似度 > 0.95）去重，只保留最高分项
- **验收**: 检索结果无高度相似片段，多样性提升

### T5: 测试
- **文件**: `src/tests/test_hvac_quality.py`
- **改动**:
  - 测试已知 HVAC 问题：distance < 0.6，low_confidence=false
  - 测试无关问题（量子力学）：low_confidence=true
  - 测试回答末尾有"依据："字符串
  - 测试 TOP_K=3 返回 3 条结果
- **验收**: `pytest src/tests/test_hvac_quality.py` 全部通过

---

## 关键架构决策

**为什么阈值设为 0.6 而非更低？**  
ChromaDB all-MiniLM-L6-v2 模型在 HVAC 领域测试中，distance 0.6 是准确率/召回率的平衡点。0.4 过于严格（漏掉变体问法），0.8 过于宽松（引入无关内容）。阈值可通过 `agent_config.yaml` 迭代调优。

**为什么拒答在 Skill 层而非 Graph 节点？**  
拒答是 HVAC 专家的业务逻辑（只有 HVAC 问题需要严格拒答，能源调度可以有更大容错）。放在 `HVACExpertSkill.execute()` 中符合 Skills 职责划分。

**与 BaseSkill 的关系**:  
T2/T3 的 execute() 逻辑在 `hvac_expert_skill.py` 中实现，继承 BaseSkill 接口。若 BaseSkill 方案已完成，直接覆盖 execute()；否则先实现静态方法，后续 Phase 6 前统一迁移。

---

## 关键文件
- `src/tools/query_hvac_knowledge.py` — 检索逻辑 + 阈值过滤 + MMR
- `src/skills/hvac_expert_skill.py` — 置信度判断 / 拒答 / 引用来源 SOP
- `src/config/prompts.yaml` — hvac_refusal / hvac_citation_format
- `data/hvac_knowledge/` — ChromaDB 向量库（已入库 5613 条）

## Skills 融合说明
- T1-T3 的置信度/拒答/引用逻辑实现在 `hvac_expert_skill.py`，不写入 nodes.py
- 详见 `docs/plan_skills_refactor.md`
