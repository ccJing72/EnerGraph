# 服务器同步指南：代码更新 + 模型切换

## 适用场景
在服务器上拉取最新代码，并完成 embedding 模型从 all-MiniLM-L6-v2 切换到 BAAI/bge-small-zh-v1.5。

---

## 步骤 1: 拉取最新代码

```bash
cd /path/to/EnerGraph          # 进入项目目录
git pull origin main            # 拉取最新代码
```

预期输出：
```
Updating 5b9654a..c9f7d01
...
src/tools/query_hvac_knowledge.py      | 修改
src/pipelines/rag_ingest.py            | 修改
requirements.txt                       | 修改
scripts/fix_qa_mismatch.py             | 新增
AI_CONTEXT.md                          | 修改
```

---

## 步骤 2: 安装新依赖

```bash
pip install -r requirements.txt
```

这会安装 `sentence-transformers>=3.0.0`。如果已有可跳过。

验证安装：
```bash
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('BAAI/bge-small-zh-v1.5'); print(f'模型维度: {m.get_sentence_embedding_dimension()}')"
```

首次加载会从 HuggingFace 下载模型（约 33MB），请确保服务器有外网访问权限。
模型自动缓存到 `~/.cache/huggingface/hub/`，后续不再重复下载。

---

## 步骤 3: 重建 ChromaDB 向量库

> 数据源 `data/unified_hvac_training_data20260509.jsonl` 您已上传到服务器。

```bash
# 第一步：清空旧集合
python -c "
import chromadb, shutil
from pathlib import Path
p = Path('data/hvac_knowledge')
c = chromadb.PersistentClient(str(p))
for col in c.list_collections():
    c.delete_collection(col.name)
for d in list(p.iterdir()):
    shutil.rmtree(d) if d.is_dir() else d.unlink()
print('ChromaDB 已清空')
"

# 第二步：重新入库（使用新模型）
python -c "
from src.pipelines.rag_ingest import ingest
total = ingest(jsonl_path='data/unified_hvac_training_data20260509.jsonl')
print(f'入库完成，共 {total} 条')
"
```

预期输出：`入库完成，共 5605 条`

---

## 步骤 4: 重启 FastAPI 服务

```bash
# 如果使用 systemd
sudo systemctl restart energraph

# 或如果使用 supervisor
supervisorctl restart energraph

# 或手动启动
uvicorn src.services.api:app --host 0.0.0.0 --port 8000
```

---

## 步骤 5: 验证功能

```bash
# 验证含湿量查询（核心验证）
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"user_input":"含湿量与相对湿度的区别及工程计算选用方法"}' \
  | python -m json.tool | head -20

# 应能看到命中正确的含湿量问答

# 验证 RAG 检索
python -c "
from src.tools.query_hvac_knowledge import query_hvac_knowledge
r = query_hvac_knowledge('什么是COP')
print('返回', len(r.get('results', [])), '条')
print('dist:', r.get('distances', []))
print('top1:', r['results'][0][:80] if 'results' in r else 'error')
"
```

---

## 常见问题

### Q: 模型下载太慢怎么办？
A: 可手动下载后放入缓存：
```bash
# 在服务端执行
pip install huggingface-hub
huggingface-cli download BAAI/bge-small-zh-v1.5
```

### Q: 离线服务器如何安装？
A: 在有网的机器上下载模型，打包后传到服务器：
```bash
# 有网机器
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5')"
tar -czf bge-model.tar.gz ~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5

# 传到服务器后解压到同目录
tar -xzf bge-model.tar.gz -C ~/.cache/huggingface/hub/
```

### Q: 旧模型是否还在？
A: 本地已删除（all-MiniLM-L6-v2 ONNX，166MB）。代码中已无任何引用，不会影响运行。

---

## 版本对照

| 组件 | 旧版本 | 新版本 |
|------|--------|--------|
| Embedding 模型 | all-MiniLM-L6-v2 | BAAI/bge-small-zh-v1.5 |
| 模型大小 | 166MB | 33MB |
| embedding 维度 | 384 | 512 |
| 依赖库 | chromadb 内置 ONNX | sentence-transformers |
| 总条目数 | 5623 | 5605 |
| Python 库 | 无需额外安装 | `sentence-transformers>=3.0.0` |
