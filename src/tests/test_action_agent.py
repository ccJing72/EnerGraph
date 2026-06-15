"""test_action_agent — /stream 端点集成测试

所属层：tests
依赖：fastapi, httpx, pytest, unittest.mock
对接算法层：N/A（Mock graph.astream_events）
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
    """模拟 graph.astream_events，依次产出 thinking、tool_call、tool_result、text、action、done 事件。"""
    from langchain_core.messages import AIMessageChunk, ToolMessage

    # thinking 事件（cognitive_parser 工具调用前的思考）
    yield {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_node": "cognitive_parser"},
        "data": {"chunk": AIMessageChunk(content="让我查询一下")},
    }
    # tool_call 事件（cognitive_parser 决定调用工具）
    from unittest.mock import MagicMock
    mock_output = MagicMock()
    mock_output.tool_calls = [{"name": "fetch_cop_data", "args": {"site_id": "SH-01"}, "id": "call_01"}]
    yield {
        "event": "on_chat_model_end",
        "metadata": {"langgraph_node": "cognitive_parser"},
        "data": {"output": mock_output},
    }
    # tool_result 事件（v3_engine_router 返回工具结果）
    tool_msg = ToolMessage(content='{"cumulative_cop": 4.2}', tool_call_id="call_01")
    yield {
        "event": "on_chain_stream",
        "metadata": {"langgraph_node": "v3_engine_router"},
        "data": {"chunk": {"messages": [tool_msg]}},
    }
    # text 事件（cognitive_parser 工具调用后的最终回答）
    yield {
        "event": "on_chat_model_stream",
        "metadata": {"langgraph_node": "cognitive_parser"},
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

    assert "thinking" in event_types, f"缺少 thinking 事件，实际事件：{event_types}"
    assert "tool_call" in event_types, f"缺少 tool_call 事件，实际事件：{event_types}"
    assert "tool_result" in event_types, f"缺少 tool_result 事件，实际事件：{event_types}"
    assert "text" in event_types, f"缺少 text 事件，实际事件：{event_types}"
    assert "action" in event_types, f"缺少 action 事件，实际事件：{event_types}"
    assert "done" in event_types, f"缺少 done 事件，实际事件：{event_types}"

    # 验证 tool_call payload
    tool_call_lines = [
        line.removeprefix("data: ").strip()
        for i, line in enumerate(body.splitlines())
        if i > 0 and body.splitlines()[i - 1].strip() == "event: tool_call"
    ]
    assert tool_call_lines, "tool_call 事件缺少 data 行"
    tc_payload = json.loads(tool_call_lines[0])
    assert tc_payload.get("name") == "fetch_cop_data"

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
