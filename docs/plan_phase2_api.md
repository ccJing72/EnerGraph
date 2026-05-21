# EnerGraph — Phase 2: FastAPI REST API

**目标**: 将 LangGraph Agent 暴露为 HTTP 服务，解耦前端依赖。
**前置条件**: Phase 1 完成（RAG + ReAct 可运行）
**完成标志**: `uvicorn src.services.api:app` 启动，`/agent/invoke` 和 `/agent/stream` 可用

---

## 子任务（每个子任务 = 一个 commit）

### T1: FastAPI 骨架 + /health
- **文件**: `src/services/api.py`
- **改动**: 创建 FastAPI app，添加 `GET /health`
- **验收**: `curl localhost:8000/health` 返回 `{"status":"ok"}`

### T2: POST /agent/invoke（同步）
- **文件**: `src/services/api.py`
- **输入**: `{"user_input": str, "target_date": str, "datacenter_id": str}`
- **输出**: `{"final_report": str, "hvac_knowledge": ..., "error": str|null}`
- **验收**: curl 调用返回完整报告

### T3: POST /agent/stream（SSE 流式）
- **文件**: `src/services/api.py`
- **改动**: `StreamingResponse` + `graph.astream()`，每个 token 作为 SSE event 推送
- **验收**: `curl -N` 可见逐 token 输出

### T4: 测试
- **文件**: `src/tests/test_api.py`
- **改动**: `TestClient` 测试 /health 和 /invoke，mock graph
- **验收**: `pytest src/tests/test_api.py` 无需 API Key 通过

### T5: 文档同步
- **文件**: `AI_CONTEXT.md` §3 §5
- **改动**: 更新目录结构，标记 Phase 2 完成

---

## 关键文件
- `src/services/api.py` — 主实现（当前为空占位）
- `src/graph/builder.py` — `graph` 单例，直接 import
- `src/schemas/v3_engine.py` — 用于 API 响应 Pydantic 模型

## 依赖安装
```bash
pip install fastapi uvicorn[standard] httpx
```
