"""fix_qa_mismatch — 修复 JSONL 含湿量问答问题

问题诊断：
  1. 含湿量问答覆盖机制不足 - 之前已修复回答但还有深层问题
  2. embedding 模型 all-MiniLM-L6-v2 对长回答嵌入效果差
  3. 重复条目互相干扰

修复方案：
  1. 删除 8 条重复的含湿量问答，只保留 1 条
  2. 优化回答为精简版（embedding 更聚焦）
  3. 重新入库
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # data/
PROJECT_ROOT = ROOT.parent  # EnerGraph/
JSONL_PATH = ROOT / "unified_hvac_training_data20260509.jsonl"
DB_PATH = PROJECT_ROOT / "data" / "hvac_knowledge"

CORRECT_ANSWER = """含湿量与相对湿度的核心区别及工程选用方法：

## 一、含湿量（d）
**定义**：湿空气中水蒸气质量与干空气质量之比，单位g/kg干空气。
**公式**：d = 0.622 × Pq / (P - Pq)
**特点**：绝对量值，不随温度变化（不结露时），只有加减湿操作才改变。

## 二、相对湿度（φ）
**定义**：水蒸气分压力与同温度下饱和水蒸气分压力之比，单位%。
**公式**：φ = Pq / Pq.b × 100%
**特点**：相对量值，随温度变化（温度↑→φ↓，温度↓→φ↑），反映饱和程度。

## 三、工程选用场景
| 场景 | 选用参数 | 原因 |
|------|---------|------|
| 空气处理（加热/冷却/加湿/除湿） | 含湿量 d | 计算除湿量 Δd |
| 结露风险判断 | 相对湿度 φ | φ=100% 时达到露点，风口结露风险 |
| 空调负荷计算 | 两者都需要 | 显热负荷用温差，潜热负荷用含湿量差 Qq = G × Δd × 2500 |
| 新风除湿负荷 | 含湿量 d | 计算室内外含湿量差 |

## 四、工程实例
夏季空调设计：室内 26℃/φ=55%→d=11.6g/kg，室外 35℃/φ=75%→d=27.2g/kg
新风除湿量 Δd = 27.2 - 11.6 = 15.6g/kg。用含湿量 d 计算除湿负荷，用相对湿度 φ 判断舒适度。"""


def fix_and_dedup():
    """删除重复的含湿量问答，只保留1条并写入优化回答"""
    if not JSONL_PATH.exists():
        print(f"❌ 文件不存在: {JSONL_PATH}")
        return False

    with open(JSONL_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    total = len(lines)
    new_lines = []
    kept_one = False
    dup_count = 0

    for line in lines:
        d = json.loads(line.strip())
        q = d["messages"][1]["content"]

        # 检测含湿量问答（不论当前回答是什么）
        if "含湿量与相对湿度有何区别" in q and "在工程计算中如何选用" in q:
            if not kept_one:
                # 保留第一条，更新为优化回答
                d["messages"][2]["content"] = CORRECT_ANSWER
                new_lines.append(json.dumps(d, ensure_ascii=False))
                kept_one = True
                print(f"✅ 保留第1条并写入优化回答")
            else:
                # 删除后续重复
                dup_count += 1
                print(f"🗑️ 删除重复条目")
                continue
        else:
            new_lines.append(json.dumps(d, ensure_ascii=False))

    removed = total - len(new_lines)
    with open(JSONL_PATH, "w", encoding="utf-8") as f:
        for nl in new_lines:
            f.write(nl + "\n")

    print(f"\n原始: {total} 条 → 处理后: {len(new_lines)} 条")
    print(f"删除重复: {removed} 条")
    return True


def cleanup_chromadb():
    """清理旧的 ChromaDB segment 目录"""
    if not DB_PATH.exists():
        print(f"⚠️ ChromaDB 目录不存在: {DB_PATH}")
        return

    dirs = sorted([d for d in DB_PATH.iterdir() if d.is_dir()])
    old_dirs = [d for d in dirs if d.name != "chroma.sqlite3"]
    if len(old_dirs) > 1:
        for d in old_dirs[:-1]:
            shutil.rmtree(d)
            print(f"🗑️ 删除旧 segment: {d.name}")


if __name__ == "__main__":
    print("=== 步骤1: 修复 JSONL（去重+优化回答）===\n")
    fix_and_dedup()

    print("\n=== 步骤2: 清理 ChromaDB ===")
    cleanup_chromadb()

    print("\n=== 步骤3: 删除旧集合并重新入库 ===")
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    import chromadb
    client = chromadb.PersistentClient(path=str(DB_PATH))
    existing = [c.name for c in client.list_collections()]
    if 'hvac_qa' in existing:
        client.delete_collection('hvac_qa')
        print("✅ 已删除旧 hvac_qa 集合")
    from src.pipelines.rag_ingest import ingest
    total = ingest(jsonl_path=str(JSONL_PATH), db_path=str(DB_PATH))
    print(f"入库完成，共 {total} 条")
