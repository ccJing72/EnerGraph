"""query_hvac_knowledge — HVAC 知识库 RAG 检索工具

所属层：tools
依赖：chromadb, src.schemas.v3_engine
对接 V3 引擎：N/A（本地向量库）
"""
import logging
from pathlib import Path
from typing import Any, Dict

from src.schemas.v3_engine import HVACKnowledgeResult

logger = logging.getLogger(__name__)

DB_PATH = str(Path(__file__).resolve().parents[2] / "data" / "hvac_knowledge")
COLLECTION_NAME = "hvac_qa"
TOP_K = 5


def query_hvac_knowledge(question: str) -> Dict[str, Any]:
    """从 HVAC 知识库检索与问题最相关的 Q&A。

    Args:
        question: 用户的暖通空调相关问题

    Returns:
        HVACKnowledgeResult 的 dict 表示
    """
    try:
        import chromadb
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        ef = OpenAIEmbeddingFunction(model_name="text-embedding-3-small")
        client = chromadb.PersistentClient(path=DB_PATH)
        col = client.get_collection(COLLECTION_NAME, embedding_function=ef)

        res = col.query(query_texts=[question], n_results=TOP_K)
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        distances = res["distances"][0]

        return HVACKnowledgeResult(
            query=question,
            results=docs,
            system_types=[m.get("system_type", "general") for m in metas],
            distances=distances,
        ).model_dump()
    except Exception as e:
        logger.error(f"query_hvac_knowledge 失败: {e}")
        return {"error": f"query_hvac_knowledge: {e}"}
