"""app — V3 多模态调度 Agent Streamlit 前端

所属层：frontend
依赖：streamlit, src.graph.builder
对接 V3 引擎：N/A（通过 graph 间接调用）
"""
import streamlit as st

from src.graph.builder import graph

st.set_page_config(page_title="青山 V3 多模态调度 Agent", layout="wide")
st.title("青山 V3 多模态调度 Agent")
st.caption("基于 QingShan-TimeDiT + PhysicsAI 的认知交互层 Demo")

with st.sidebar:
    st.header("输入配置")
    user_input = st.text_area(
        "业务意图输入",
        value="明天有大批订单急产，产线全开，请评估能耗风险并给出调度建议。",
        height=120,
    )
    target_date = st.text_input("目标日期", value="2026-05-15")
    datacenter_id = st.text_input("数据中心 ID（AIDC 场景）", value="DC-SH-01")

if st.button("运行 Agent", type="primary"):
    with st.spinner("V3 Agent 正在分析..."):
        try:
            result = graph.invoke({
                "user_input": (
                    f"{user_input}\n"
                    f"[target_date={target_date}, datacenter_id={datacenter_id}]"
                ),
            })

            st.success("分析完成")
            st.markdown(result.get("final_report", "（无报告）"))

            with st.expander("V3 引擎原始数据"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("TimeDiT 预测")
                    st.json(result.get("timedit_data") or {})
                with col2:
                    st.subheader("PhysicsAI 验证")
                    st.json(result.get("physics_verification") or {})
                with col3:
                    st.subheader("AIDC 液冷状态")
                    st.json(result.get("aidc_cooling") or {})

            if result.get("constraints"):
                with st.expander("意图解析结果（ConstraintMatrix）"):
                    st.json(result["constraints"])

            if result.get("error"):
                st.warning(f"Agent 警告: {result['error']}")

        except Exception as e:
            st.error(f"运行出错: {e}")

st.markdown("---")
st.caption("Phase 1 Mock Demo — V3 引擎为模拟数据")
