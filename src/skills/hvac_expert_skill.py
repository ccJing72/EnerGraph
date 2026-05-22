"""hvac_expert_skill — HVAC 专家问答技能

所属层：skills
依赖：src.tools.query_hvac_knowledge
对接 V3 引擎：N/A（ChromaDB RAG）

SOP：
  1. 调用 query_hvac_knowledge 检索相关 Q&A
  2. 若 low_confidence=True → 触发拒答（Phase 3 T2）
  3. 否则综合检索结果生成回答，末尾附引用来源（Phase 3 T3）

Prompt keys（src/config/prompts.yaml）：
  - hvac_expert          : 领域专家角色设定
  - hvac_refusal         : 低置信度拒答指令（Phase 3 新增）
  - hvac_citation_format : 引用来源格式要求（Phase 3 新增）
"""


class HVACExpertSkill:
    """HVAC 专家问答技能。

    当前为骨架占位，Phase 3 T1-T3 实现具体逻辑。
    cognitive_parser 通过 SKILL_REGISTRY 引用此类获取技能描述。
    """

    name = "hvac_expert"
    tools = ["query_hvac_knowledge"]
    prompt_keys = ["hvac_expert", "hvac_refusal", "hvac_citation_format"]
    description = "暖通空调专家问答（规范查询、能效计算、故障诊断、节能优化）"
