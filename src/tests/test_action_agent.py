"""test_action_agent — /stream 端点集成测试

所属层：tests
依赖：fastapi, httpx, pytest, unittest.mock
对接 V3 引擎：N/A（Mock graph.astream_events）
"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.services.api import app
from src.schemas.action_agent import UIAction


def _make_action_event():
    action = UIAction(route="/chiller-room", params={"site_id": "SH-01"})
    return action


async def _mock_astream_events(initial_state, version="v2"):
    """模拟 graph.astream_events，依次产出 text、action、done 事件所需的 LangGraph 事件。"""
    from langchain_core.messages import AIMessageChunk

    # text 事件
    yield {
        "event": "on_chat_model_stream",
        "data": {"chunk": AIMessageChunk(content="冷水机房当前 COP 为 4.2")},
    }
    # action 事件（通过 on_chain_end 携带 pending_actions）
    yield {
        "event": "on_chain_end",
        "data": {"output": {"pending_actions": [_make_action_event()]}},
    }


@pytest.mark.asyncio
async def test_stream_contains_action_event():
    with patch("src.services.api.graph") as mock_graph:
        mock_graph.astream_events = _mock_astream_events

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/stream",
                json={
                    "user_input": "冷水机房的 COP 是多少？",
                    "page_context": {"current_route": "/chiller-room", "site_id": "SH-01"},
                },
            )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    event_types = [
        line.removeprefix("event: ").strip()
        for line in body.splitlines()
        if line.startswith("event:")
    ]

    assert "text" in event_types, f"缺少 text 事件，实际事件：{event_types}"
    assert "action" in event_types, f"缺少 action 事件，实际事件：{event_types}"
    assert "done" in event_types, f"缺少 done 事件，实际事件：{event_types}"

    # 验证 action payload 包含正确路由
    action_lines = [
        line.removeprefix("data: ").strip()
        for i, line in enumerate(body.splitlines())
        if i > 0 and body.splitlines()[i - 1].strip() == "event: action"
    ]
    assert action_lines, "action 事件缺少 data 行"
    payload = json.loads(action_lines[0])
    assert payload.get("route") == "/chiller-room"


@pytest.mark.asyncio
async def test_stream_page_context_injected_into_system_prompt():
    """验证 page_context 被注入到 cognitive_parser 的 system prompt 中。"""
    captured_messages = []

    async def _capture_astream_events(initial_state, version="v2"):
        # 触发 cognitive_parser_node 以捕获注入后的 messages
        from src.graph.nodes import cognitive_parser_node
        from src.schemas.action_agent import PageContext

        state = {
            "user_input": "查询 COP",
            "page_context": PageContext(current_route="/chiller-room", site_id="SH-01"),
        }
        # 直接调用节点（不走 LLM），只验证 messages 构造
        # mock LLM invoke
        from unittest.mock import MagicMock
        from langchain_core.messages import AIMessage

        with patch("src.graph.nodes._get_llm") as mock_llm_factory:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = AIMessage(content="ok", tool_calls=[])
            mock_llm_factory.return_value = mock_llm
            result = cognitive_parser_node(state)
            captured_messages.extend(result.get("messages", []))

        yield {"event": "on_chain_end", "data": {"output": {}}}

    with patch("src.services.api.graph") as mock_graph:
        mock_graph.astream_events = _capture_astream_events

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/stream",
                json={
                    "user_input": "查询 COP",
                    "page_context": {"current_route": "/chiller-room", "site_id": "SH-01"},
                },
            )

    system_msg = next((m for m in captured_messages if hasattr(m, "type") and m.type == "system"), None)
    assert system_msg is not None, "未找到 SystemMessage"
    assert "/chiller-room" in system_msg.content, "current_route 未注入 system prompt"
    assert "SH-01" in system_msg.content, "site_id 未注入 system prompt"


@pytest.mark.asyncio
async def test_page_context_fallback_none_site_id():
    """验证 PageContext 为 Pydantic 对象且 site_id 为 None 时不崩溃。"""
    from unittest.mock import MagicMock, patch
    from langchain_core.messages import AIMessage
    from src.graph.nodes import cognitive_parser_node
    from src.schemas.action_agent import PageContext

    state = {
        "user_input": "查询 COP",
        "page_context": PageContext(current_route="/", site_id=None),
    }

    with patch("src.graph.nodes._get_llm") as mock_llm_factory:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="ok", tool_calls=[])
        mock_llm_factory.return_value = mock_llm
        result = cognitive_parser_node(state)

    messages = result.get("messages", [])
    system_msg = next((m for m in messages if hasattr(m, "type") and m.type == "system"), None)
    assert system_msg is not None
    assert "未指定" in system_msg.content, "site_id=None 时应显示'未指定'"
