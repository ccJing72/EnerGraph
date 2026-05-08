"""回退报告生成器（LLM 不可用时使用）"""
from typing import Any, Dict

_ICONS = {"moon": "🌙", "sun": "☀️", "sunset": "🌆"}


def build_report(
    metrics: Dict[str, Any],
    price_analysis: Dict[str, Any],
    benefit: Dict[str, Any],
    user_pref: str = "cost_priority",
) -> str:
    """基于工具结果生成 Markdown 调度报告."""
    lines = ["# 家庭能源调度分析报告\n"]

    # ── 调度安排 ──
    lines.append("## 调度安排\n")
    periods = metrics.get("period_analysis", [])
    if periods:
        for p in periods:
            icon = _ICONS.get(p.get("icon", ""), "")
            lines.append(f"### {icon} {p['name']} ({p['hours']})")
            lines.append(f"- 负载: {p['load_kwh']} kWh | 光伏: {p['solar_kwh']} kWh | 均价: {p['avg_price']} 元/kWh")
            if p.get("charge_kwh", 0) > 0:
                lines.append(f"- 储能充电: **{p['charge_kwh']} kWh**")
            if p.get("discharge_kwh", 0) > 0:
                lines.append(f"- 储能放电: **{p['discharge_kwh']} kWh**")
            lines.append("")
    else:
        lines.append("（无逐段数据）\n")

    # ── 收益对比 ──
    lines.append("## 收益对比\n")
    if benefit and "error" not in benefit:
        lines.append(f"- 基准成本: {benefit.get('baseline_cost', 'N/A')} 元")
        lines.append(f"- 优化成本: {benefit.get('optimized_cost', 'N/A')} 元")
        savings = benefit.get("savings", 0)
        savings_pct = benefit.get("savings_pct", 0)
        lines.append(f"- **节省: {savings} 元 ({savings_pct}%)**\n")
    else:
        lines.append("（收益数据不可用）\n")

    # ── 总结建议 ──
    lines.append("## 总结建议\n")
    pref_map = {
        "cost_priority": "当前偏好：**省钱优先**，建议充分利用谷段低价充电、峰段放电套利。",
        "eco_priority": "当前偏好：**环保优先**，建议最大化光伏自消纳，减少购网电量。",
        "backup_priority": "当前偏好：**备电优先**，建议保持较高 SOC 以应对停电风险。",
    }
    lines.append(pref_map.get(user_pref, f"用户偏好: {user_pref}"))

    if metrics and "error" not in metrics:
        lines.append(
            f"\n光伏利用率 {metrics.get('solar_utilization_pct', 0)}%，"
            f"全天均价 {metrics.get('avg_price', 0)} 元/kWh。"
        )

    return "\n".join(lines)
