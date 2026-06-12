"""FastAPI 服务层 — Action Agent HTTP API

所属层：services
依赖：fastapi, uvicorn, src.graph.builder, src.schemas, src.config.settings
对接 V3 引擎：N/A（通过 Graph 间接调用 Tools）
"""
import json
import logging
import secrets
from typing import AsyncIterator, List

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import AIMessageChunk

from src.config.settings import settings
from src.graph.builder import graph
from src.schemas.action_agent import ActionAgentInput, UIAction
from src.schemas.v3_engine import IntentItem

logger = logging.getLogger(__name__)

app = FastAPI(
    title="EnerGraph Action Agent",
    description="青山 V3 多模态调度 Agent HTTP API",
    version="0.3.0",
)

# ── CORS 中间件 ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 鉴权（可选） ─────────────────────────────────────────────────
_security = HTTPBearer(auto_error=False)


async def _verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> None:
    """Bearer Token 鉴权。api_key 为空时跳过（开发模式）。

    Raises:
        HTTPException: 401 — 密钥不匹配
    """
    expected = settings.api.api_key
    if not expected:
        return  # 开发模式，不鉴权
    if credentials is None or not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(status_code=401, detail="无效的 API Key")


@app.get("/health")
async def health() -> dict:
    """健康检查端点。

    Returns:
        包含 status 字段的状态字典
    """
    return {"status": "ok"}


@app.post("/invoke")
async def invoke(
    input_data: ActionAgentInput,
    _: None = Depends(_verify_api_key),
) -> JSONResponse:
    """同步运行 Agent，返回最终报告和 UI 动作列表。

    接收用户输入和可选页面上下文，经过完整的 ReAct 循环后，
    返回 LLM 生成的 Markdown 报告和所有待执行的 UI 动作。

    Args:
        input_data: 包含 user_input 和可选 page_context 的请求体

    Returns:
        JSONResponse，body 含 report(str) 和 actions(List[dict])

    Raises:
        HTTPException: Agent 执行失败时返回 500
    """
    initial_state: dict = {"user_input": input_data.user_input}
    if input_data.page_context is not None:
        initial_state["page_context"] = input_data.page_context

    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"Agent 调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {e}")

    error = result.get("error")
    if error:
        raise HTTPException(status_code=500, detail=str(error))

    report: str = result.get("final_report", "")
    pending_actions: List[UIAction] = result.get("pending_actions", [])

    actions_dicts = []
    for action in pending_actions:
        if isinstance(action, UIAction):
            actions_dicts.append(action.model_dump())
        elif isinstance(action, dict):
            actions_dicts.append(action)
        else:
            actions_dicts.append(str(action))

    return JSONResponse(content={
        "report": report,
        "actions": actions_dicts,
    })


async def _sse_generator(input_data: ActionAgentInput) -> AsyncIterator[str]:
    """SSE 流式推送生成器：逐 token 推送 text/intent_plan/action/done 事件。

    Args:
        input_data: 包含 user_input 和可选 page_context 的请求体

    Yields:
        SSE 格式字符串（event: text/action/intent_plan/done/error）
    """
    initial_state: dict = {"user_input": input_data.user_input}
    if input_data.page_context is not None:
        initial_state["page_context"] = input_data.page_context

    try:
        async for event in graph.astream_events(initial_state, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    yield f"event: text\ndata: {json.dumps({'text': chunk.content}, ensure_ascii=False)}\n\n"

            elif kind == "on_chain_end":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict):
                    # Phase 7: intent_plan 事件
                    intent_plan = output.get("intent_plan")
                    if intent_plan:
                        intents_payload = [
                            i.model_dump() if isinstance(i, IntentItem)
                            else (i if isinstance(i, dict) else {"id": 0, "description": str(i)})
                            for i in intent_plan
                        ]
                        yield f"event: intent_plan\ndata: {json.dumps({'intents': intents_payload}, ensure_ascii=False)}\n\n"

                    # action 事件
                    actions = output.get("pending_actions", [])
                    for action in actions:
                        payload = action.model_dump() if isinstance(action, UIAction) else action
                        yield f"event: action\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"SSE 流式推送失败: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    yield "event: done\ndata: {}\n\n"


@app.post("/stream")
async def stream(
    input_data: ActionAgentInput,
    _: None = Depends(_verify_api_key),
) -> StreamingResponse:
    """流式运行 Agent，以 SSE 格式推送 text / intent_plan / action / done 事件。

    Args:
        input_data: 包含 user_input 和可选 page_context 的请求体

    Returns:
        StreamingResponse（media_type=text/event-stream）
    """
    return StreamingResponse(_sse_generator(input_data), media_type="text/event-stream")
