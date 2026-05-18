"""rag_ingest — 将 HVAC 语料库入库到 ChromaDB 向量数据库

所属层：pipelines
依赖：chromadb, python-dotenv
对接 V3 引擎：N/A
"""
import json
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

JSONL_PATH = Path(__file__).resolve().parents[2] / "unified_hvac_training_data20260509.jsonl"
DB_PATH = str(Path(__file__).resolve().parents[2] / "data" / "hvac_knowledge")
COLLECTION_NAME = "hvac_qa"
BATCH_SIZE = 100


def _clean_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _classify_system(system: str) -> str:
    if "地铁" in system or "车站" in system:
        return "metro"
    if "商业" in system:
        return "commercial"
    if "规范" in system or "标准" in system:
        return "standard"
    return "general"


def ingest(jsonl_path: str = str(JSONL_PATH), db_path: str = DB_PATH) -> int:
    """将 JSONL 语料入库到 ChromaDB，幂等执行。

    Args:
        jsonl_path: HVAC 语料 JSONL 文件路径
        db_path: ChromaDB 持久化目录

    Returns:
        入库条目总数

    Raises:
        FileNotFoundError: 语料文件不存在
        ImportError: chromadb 未安装
    """
    import chromadb
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    if not Path(jsonl_path).exists():
        raise FileNotFoundError(f"语料文件不存在: {jsonl_path}")

    ef = OpenAIEmbeddingFunction(model_name="text-embedding-3-small")
    client = chromadb.PersistentClient(path=db_path)

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        col = client.get_collection(COLLECTION_NAME, embedding_function=ef)
        count = col.count()
        if count > 0:
            print(f"[rag_ingest] 已存在 {count} 条，跳过入库。")
            return count
        client.delete_collection(COLLECTION_NAME)

    col = client.create_collection(COLLECTION_NAME, embedding_function=ef)

    docs, metas, ids = [], [], []
    with open(jsonl_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                d = json.loads(line)
                msgs = d["messages"]
                question = msgs[1]["content"]
                answer = _clean_think(msgs[2]["content"])
                system = msgs[0]["content"]
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

            docs.append(f"问题：{question}\n回答：{answer}")
            metas.append({"system_type": _classify_system(system), "system": system[:100]})
            ids.append(f"hvac_{i}")

            if len(docs) >= BATCH_SIZE:
                col.add(documents=docs, metadatas=metas, ids=ids)
                print(f"  已入库 {i + 1} 条...", end="\r")
                docs, metas, ids = [], [], []

    if docs:
        col.add(documents=docs, metadatas=metas, ids=ids)

    total = col.count()
    print(f"\n[rag_ingest] 入库完成，共 {total} 条。")
    return total


if __name__ == "__main__":
    ingest()
