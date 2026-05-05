"""Streamlit 前端界面"""
import streamlit as st
import json
from src.models.data_models import AgentInput, ForecastData, SystemState, BasicInfo
from src.agent.graph import create_agent_graph


st.set_page_config(page_title="家庭能源调度 AI Agent", page_icon="⚡", layout="wide")

st.title("⚡ 家庭能源调度 AI Agent Demo")
st.markdown("基于 LangGraph 的能源调度策略解释系统")

# 侧边栏：输入配置
with st.sidebar:
    st.header("📊 输入数据配置")

    # 使用示例数据
    use_example = st.checkbox("使用示例数据", value=True)

    if use_example:
        example_data = {
            "forecast_data": {
                "load": [0.5, 0.4, 0.3, 0.3, 0.4, 0.6, 1.2, 1.5, 1.8, 1.6, 1.4, 1.3,
                        1.5, 1.7, 1.6, 1.4, 1.8, 2.2, 2.5, 2.1, 1.8, 1.2, 0.8, 0.6],
                "solar": [0, 0, 0, 0, 0, 0, 0.3, 1.2, 2.5, 3.8, 4.2, 4.5,
                         4.3, 3.9, 3.1, 1.8, 0.5, 0, 0, 0, 0, 0, 0, 0],
                "grid_price": [0.32, 0.32, 0.32, 0.32, 0.32, 0.45, 0.45, 0.45,
                              0.58, 0.58, 0.58, 0.58, 0.58, 0.58, 0.58, 0.45,
                              0.45, 0.65, 0.65, 0.65, 0.45, 0.45, 0.32, 0.32]
            },
            "system_state": {
                "soc": 0.3,
                "soc_max": 0.9,
                "soc_min": 0.2,
                "max_power": 3.0,
                "user_pref": "cost_priority"
            },
            "basic_info": {
                "timezone": "UTC+8",
                "currency": "CNY",
                "query": "今天的调度策略是什么？为什么这么调度？"
            }
        }
        st.json(example_data, expanded=False)

    query = st.text_input("用户查询", value="今天的调度策略是什么？为什么这么调度？")

# 主界面
if st.button("🚀 运行 Agent", type="primary"):
    with st.spinner("Agent 正在分析调度策略..."):
        try:
            # 构建输入
            agent_input = AgentInput(**example_data)

            # 创建并运行 Agent
            graph = create_agent_graph()

            initial_state = {
                "load": agent_input.forecast_data.load,
                "solar": agent_input.forecast_data.solar,
                "grid_price": agent_input.forecast_data.grid_price,
                "soc": agent_input.system_state.soc,
                "max_power": agent_input.system_state.max_power,
                "user_pref": agent_input.system_state.user_pref,
                "query": query,
                "metrics": {},
                "price_analysis": {},
                "benefit": {},
                "next_action": None,
                "iteration": 0,
                "context": None,
                "history": None,
                "report": ""
            }

            result = graph.invoke(initial_state)

            # 显示结果
            st.success("✅ 分析完成！")
            st.markdown(result["report"])

            # 显示工具调用结果
            with st.expander("🔧 工具调用详情"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("统计指标")
                    st.json(result["metrics"])
                with col2:
                    st.subheader("电价分析")
                    st.json(result["price_analysis"])
                with col3:
                    st.subheader("收益计算")
                    st.json(result["benefit"])

        except Exception as e:
            st.error(f"❌ 运行出错: {str(e)}")

# 页脚
st.markdown("---")
st.markdown("💡 **提示**: 这是一个 MVP Demo，工具函数为简化的 Mock 实现")
