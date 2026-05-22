# EnerGraph — Phase 3: RAG 质量优化 + 减少幻觉

**目标**: 让 HVAC 问答更准确，低置信度时明确说"不知道"而非编造。
**前置条件**: Phase 2 完成（API 可用）
**完成标志**: 低相关度问题返回置信度标志，报告引用检索来源

---

## 子任务（每个子任务 = 一个 commit）

### T1: 相关度阈值过滤
- **文件**: `src/tools/query_hvac_knowledge.py`
- **改动**: 若 top 结果 distance > 0.6，在返回结果中加 `"low_confidence": true`
- **验收**: 问"量子力学"返回 low_confidence，问"冷水机组COP"不返回

### T2: 低置信度时 Agent 拒答
- **文件**: `src/config/prompts.yaml`（interpreter_generator system prompt）
- **改动**: 加入指令：若 hvac_knowledge.low_confidence=true，回答"知识库中暂无相关信息"
- **验收**: 低置信度问题不产生幻觉回答

### T3: 报告引用来源
- **文件**: `src/config/prompts.yaml`（interpreter_generator）
- **改动**: 要求 LLM 在回答末尾注明"依据：[检索片段摘要]"
- **验收**: 报告末尾有来源标注

### T4: 减少检索冗余（MMR）
- **文件**: `src/tools/query_hvac_knowledge.py`
- **改动**: ChromaDB query 改用 `include=["documents","distances"]`，top_k 从 5 降到 3
- **验收**: 检索结果多样性提升，无重复片段

### T5: 测试
- **文件**: `src/tests/test_tools.py`
- **改动**: 测试已知问题 distance < 0.6；测试未知问题返回 low_confidence
- **验收**: pytest 通过

---

## 关键文件
- `src/tools/query_hvac_knowledge.py` — 检索逻辑
- `src/skills/hvac_expert_skill.py` — 置信度判断/拒答/引用来源 SOP（本 Phase 完善）
- `src/config/prompts.yaml` — hvac_refusal / hvac_citation_format（本 Phase 新增）
- `data/hvac_knowledge/` — ChromaDB 向量库（已入库 5613 条）

## Skills 融合说明
- T1-T3 的置信度/拒答/引用逻辑实现在 `src/skills/hvac_expert_skill.py`，不写入 nodes.py
- 详见 `docs/plan_skills_refactor.md`
