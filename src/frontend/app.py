"""app — V3 多模态调度 Agent + HVAC 知识库 Streamlit 前端

所属层：frontend
依赖：streamlit, src.graph.builder
对接 V3 引擎：N/A（通过 graph 间接调用）
"""
import streamlit as st

from src.graph.builder import graph

st.set_page_config(page_title="青山 V3 多模态调度 Agent", layout="wide")
st.title("青山 V3 多模态调度 Agent")
st.caption("暖通空调专家问答 · 能源调度分析 · 基于 QingShan-TimeDiT + PhysicsAI")

# 初始化对话历史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 侧边栏
with st.sidebar:
    st.header("配置")
    target_date = st.text_input("目标日期（调度场景）", value="2026-05-15")
    datacenter_id = st.text_input("数据中心 ID（AIDC 场景）", value="DC-SH-01")
    st.divider()
    st.markdown("**示例问题**")
    examples = [
        "冷水机组 COP 如何计算？",
        "地铁车站环控系统如何节能优化？",
        "明天产线全开，评估能耗风险",
        "冷冻水系统出现压差异常如何诊断？",
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

    # 调用 Agent
    with st.chat_message("assistant"):
        with st.spinner("Agent 正在分析..."):
            try:
                full_input = (
                    f"{user_input}\n"
                    f"[target_date={target_date}, datacenter_id={datacenter_id}]"
                )
                result = graph.invoke({"user_input": full_input})
                report = result.get("final_report", "（无回答）")
                st.markdown(report)

                # 展示工具调用详情
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
                    st.warning(f"Agent 警告: {result['error']}")

                st.session_state.chat_history.append({"role": "assistant", "content": report})

            except Exception as e:
                err = f"运行出错: {e}"
                st.error(err)
                st.session_state.chat_history.append({"role": "assistant", "content": err})

st.markdown("---")
st.caption("Phase 1 Demo · HVAC 知识库 5613 条 · V3 引擎为 Mock 数据")
