"""ReAct 节点实现"""
from typing import Dict, Any
from src.agent.state import AgentState
from src.tools.compute_metrics import compute_metrics
from src.tools.compete_price import compete_price
from src.tools.calc_benefit import calc_benefit


def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent 决策节点 (简化版 ReAct)
    在完整版本中，这里会调用 LLM 进行 Thought 并决定调用哪个工具
    当前 Demo 版本：按顺序调用所有工具
    """
    # TODO: 集成 LLM 进行真正的 ReAct 循环
    # 当前为简化实现，直接调用工具

    metrics = compute_metrics(state["load"], state["solar"], state["grid_price"])
    price_analysis = compete_price(state["grid_price"])
    benefit = calc_benefit(
        state["load"], state["solar"], state["grid_price"],
        state["soc"], state["max_power"]
    )

    return {
        "metrics": metrics,
        "price_analysis": price_analysis,
        "benefit": benefit,
        "iteration": state.get("iteration", 0) + 1,
        "next_action": "generate_report"  # 预留决策字段
    }


def generate_report_node(state: AgentState) -> Dict[str, str]:
    """生成调度策略报告"""
    metrics = state["metrics"]
    price = state["price_analysis"]
    benefit = state["benefit"]

    report = f"""## 今日家庭能源调度策略解读

#### 🌙 【00:00–06:00】谷段充电期
**计划**: 电网低价购电充电，储能补能备用
**说明**: 谷段电价 {price['min_price']}元/kWh，为全天最低，优先储能充电

#### ☀️ 【06:00–17:00】光伏优先期
**计划**: 光伏发电 {metrics['total_solar_kwh']}kWh，优先自用，富余储能
**说明**: 光伏利用率 {metrics['solar_utilization_pct']}%，减少电网购电

#### 🌆 【17:00–21:00】峰段放电期
**计划**: 储能放电供应负荷，避免高价购电
**说明**: 峰段电价 {price['max_price']}元/kWh，储能放电节省成本

#### 🌙 【21:00–24:00】补充调整期
**计划**: 低负荷待机，保持储能备电能力

---

**总体概述**: 今日调度以"{state['user_pref']}"为目标，通过峰谷套利预计节省 {benefit['savings']}元（{benefit['savings_pct']}%）

**收益对比**:
- 基准成本: {benefit['baseline_cost']}元
- 优化成本: {benefit['optimized_cost']}元
- 节省金额: {benefit['savings']}元

**总结建议**: 当前策略已充分利用峰谷价差（{price['arbitrage_potential_pct']}%），建议保持现有调度模式
"""

    return {"report": report}
