"""hvac_expert_skill — HVAC 专家问答技能

所属层：skills
依赖：src.tools.query_hvac_knowledge, src.config.settings
对接 V3 引擎：N/A（ChromaDB RAG）

SOP：
  1. 调用 query_hvac_knowledge 检索相关 Q&A
  2. 若 low_confidence=True → 触发拒答（hvac_refusal Prompt）
  3. 否则综合检索结果生成回答，末尾附引用来源（hvac_citation_format Prompt）

Prompt keys（src/config/prompts.yaml）：
  - hvac_expert          : 领域专家角色设定
  - hvac_refusal         : 低置信度拒答指令
  - hvac_citation_format : 引用来源格式要求
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HVACExpertSkill:
    """HVAC 专家问答技能。

    execute() 在 v3_engine_router_node 执行完 query_hvac_knowledge 后调用，
    根据检索结果的 low_confidence 标志决定后续行为：
      - low_confidence=True  → 注入拒答 Prompt，截断检索内容
      - low_confidence=False → 注入引用格式 Prompt，传递 source_snippets
    """

    name = "hvac_expert"
    tools = ["query_hvac_knowledge"]
    prompt_keys = ["hvac_expert", "hvac_refusal", "hvac_citation_format"]
    description = "暖通空调专家问答（规范查询、能效计算、故障诊断、节能优化）"

    @staticmethod
    def execute(
        tool_results: List[tuple],
        prompts: Dict[str, Any],
    ) -> Dict[str, Any]:
        """处理 query_hvac_knowledge 工具结果，返回 interpreter 上下文。

        Args:
            tool_results: [(tool_name, result_dict, args), ...] 本轮工具执行结果
            prompts: 从 prompts.yaml 加载的完整 Prompt 字典

        Returns:
            字典，包含：
              - system_suffix: 追加到 interpreter_generator system prompt 的内容
              - context_override: 若不为 None，替换传给 interpreter 的 hvac_knowledge 上下文
              - low_confidence: 是否低置信度
        """
        # 找到 query_hvac_knowledge 的结果
        hvac_result: Optional[Dict] = None
        for name, result, _args in tool_results:
            if name == "query_hvac_knowledge" and "error" not in result:
                hvac_result = result
                break

        if hvac_result is None:
            return {"system_suffix": "", "context_override": None, "low_confidence": False}

        low_confidence = hvac_result.get("low_confidence", False)
        source_snippets = hvac_result.get("source_snippets", [])

        if low_confidence:
            # 拒答模式：注入 hvac_refusal prompt，清空检索内容
            refusal_prompt = prompts.get("hvac_refusal", {}).get("system", "")
            logger.info("HVAC 检索低置信度，触发拒答")
            return {
                "system_suffix": f"\n\n{refusal_prompt}",
                "context_override": {"low_confidence": True, "query": hvac_result.get("query", "")},
                "low_confidence": True,
            }

        # 正常模式：注入引用格式 prompt + source_snippets
        citation_prompt = prompts.get("hvac_citation_format", {}).get("system", "")
        logger.info(f"HVAC 检索正常，{len(hvac_result.get('results', []))} 条结果，注入引用格式")
        return {
            "system_suffix": f"\n\n{citation_prompt}\n\n可用的引用来源摘要：\n" +
                             "\n".join(f"- {s}" for s in source_snippets) if source_snippets
                             else f"\n\n{citation_prompt}",
            "context_override": None,
            "low_confidence": False,
        }
