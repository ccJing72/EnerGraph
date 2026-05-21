"""app — V3 多模态调度 Agent + HVAC 知识库 Streamlit 前端

所属层：frontend
依赖：streamlit, src.graph.builder
对接 V3 引擎：N/A（通过 graph 间接调用）
"""
import sys
from pathlib import Path

_src_root = Path(__file__).resolve().parents[2]
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

import streamlit as st

from src.graph.builder import graph

st.set_page_config(page_title="青山 V3 多模态调度 Agent", layout="wide")
st.title("青山 V3 多模态调度 Agent")
st.caption("暖通空调专家问答 · 能源调度分析 · 基于 QingShan-TimeDiT + PhysicsAI")

NODE_STEPS = {
    "cognitive_parser": "意图解析 — 分析问题类型，选择工具",
    "v3_engine_router": "工具调用 — 检索知识库 / 查询引擎数据",
    "interpreter_generator": "生成回答 — 综合数据，撰写报告",
}

# 初始化对话历史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 侧边栏
with st.sidebar:
    st.header("配置")
    target_date = st.text_input("目标日期（调度场景）", value="2026-05-15")
    datacenter_id = st.text_input("数据中心 ID（AIDC 场景）", value="Mock 假数据")
    st.divider()
    st.markdown("**示例问题**")
    examples = [
        "冷水机组 COP 如何计算？",
        "地铁车站环控系统如何节能优化？",
        "冷冻水系统出现压差异常如何诊断？",
        "ASHRAE 标准中空调系统能效有哪些要求？",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state.pending_input = ex
    if st.button("清空对话", type="secondary", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# 显示历史对话
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 处理侧边栏示例按钮触发
if "pending_input" in st.session_state:
    user_input = st.session_state.pop("pending_input")
else:
    user_input = st.chat_input("输入问题或业务意图（如：冷水机组COP如何计算？）")

if user_input:
    # 显示用户消息
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 调用 Agent（token 级流式）
    with st.chat_message("assistant"):
        try:
            full_input = (
                f"{user_input}\n"
                f"[target_date={target_date}, datacenter_id={datacenter_id}]"
            )

            answer_ph = st.empty()
            think_ph = st.empty()
            steps_ph = st.empty()

            answer_text = ""
            think_text = ""
            steps = []
            result = {}
            tool_names = []
            seen_nodes = set()
            current_node = None

            for event in graph.stream(
                {"user_input": full_input},
                stream_mode=["updates", "messages"],
            ):
                mode, data = event

                if mode == "messages":
                    chunk, meta = data
                    node = meta.get("langgraph_node", "")

                    # 节点切换时更新步骤
                    if node and node != current_node:
                        current_node = node
                        if node not in seen_nodes:
                            seen_nodes.add(node)
                            if node in NODE_STEPS:
                                label = NODE_STEPS[node]
                                if node == "v3_engine_router" and tool_names:
                                    label += f"（{', '.join(tool_names)}）"
                                steps.append(f"✅ {label}")
                                steps_ph.markdown("\n".join(steps))

                    # 检测工具调用
                    if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                        for tc in chunk.tool_call_chunks:
                            if tc.get("name") and tc["name"] not in tool_names:
                                tool_names.append(tc["name"])

                    # 流式文本
                    content = chunk.content if hasattr(chunk, "content") and chunk.content else ""
                    if content:
                        if node == "interpreter_generator":
                            answer_text += content
                            answer_ph.markdown(answer_text + "▌")
                        elif node == "cognitive_parser":
                            think_text += content
                            think_ph.caption(f"💭 {think_text[:200]}{'…' if len(think_text) > 200 else ''}")

                elif mode == "updates":
                    for node_name, update in data.items():
                        # 确保节点出现在步骤中
                        if node_name not in seen_nodes:
                            seen_nodes.add(node_name)
                            if node_name in NODE_STEPS:
                                label = NODE_STEPS[node_name]
                                if node_name == "v3_engine_router" and tool_names:
                                    label += f"（{', '.join(tool_names)}）"
                                steps.append(f"✅ {label}")
                                steps_ph.markdown("\n".join(steps))
                        # 合并结果
                        for k, v in update.items():
                            if k not in ("messages",):
                                result[k] = v

            # 最终输出
            final = answer_text or result.get("final_report", "（无回答）")
            answer_ph.markdown(final)
            think_ph.empty()

            # 工具调用详情
            details = {}
            if result.get("hvac_knowledge"):
                details["HVAC 知识库检索"] = result["hvac_knowledge"]
            if result.get("timedit_data"):
                details["TimeDiT 预测"] = result["timedit_data"]
            if result.get("physics_verification"):
                details["PhysicsAI 验证"] = result["physics_verification"]
            if result.get("aidc_cooling"):
                details["AIDC 液冷状态"] = result["aidc_cooling"]
            if result.get("constraints"):
                details["意图解析（ConstraintMatrix）"] = result["constraints"]

            if details:
                with st.expander("引擎数据详情"):
                    for label, data in details.items():
                        st.subheader(label)
                        st.json(data)

            if result.get("error"):
                st.warning(f"警告: {result['error']}")

            st.session_state.chat_history.append({"role": "assistant", "content": final})

        except Exception as e:
            import traceback
            err_detail = traceback.format_exc()
            st.error(f"运行出错: {e}")
            with st.expander("调试详情"):
                st.code(err_detail)
            st.session_state.chat_history.append({"role": "assistant", "content": f"运行出错: {e}"})

st.markdown("---")
st.caption("Phase 1 Demo · HVAC 知识库 5613 条 · V3 引擎为 Mock 数据")
