"""ui_router_skill — 监控页面查询与跳转技能

所属层：skills
依赖：src.tools.navigate_to_page, src.tools.java_backend, src.schemas.action_agent
对接 V3 引擎：N/A（Java 后端监控 API）

SOP：
  1. 识别查询意图 — 根据 LLM 调用的 Java 工具类型判断用户查询目标
  2. Java 工具取数 — 由 v3_engine_router 通过 TOOL_REGISTRY 执行
  3. 文字总结 — 由 LLM（interpreter_generator）生成流式 token 输出
  4. UIAction 生成 — 本 Skill 根据工具调用结果推断跳转路由

Skill 的职责集中在第 4 步：接收本轮工具调用结果，决定是否下发 UIAction。
优先使用 LLM 显式调用的 navigate_to_page，其次根据 Java 工具类型自动推断。

Java 工具（fetch_cop_data 等）在 Phase 4 替换为真实 HTTP，此 Skill 无需改动。

Prompt keys（src/config/prompts.yaml）：
  - action_agent_nav_hint : 路由表 + 跳转时机判断指令
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.schemas.action_agent import UIAction

logger = logging.getLogger(__name__)

# 工具 → 路由映射（Java 后端工具自动推断跳转目标）
_TOOL_ROUTE_MAP: Dict[str, str] = {
    "fetch_cop_data": "/chiller-room",
    "fetch_energy_summary": "/energy-monitor",
    "fetch_active_alarms": "/alarms",
}


class UIRouterSkill:
    """监控页面查询与跳转技能。

    v3_engine_router 执行完本轮工具调用后，将结果列表传给 infer_navigation()，
    由 Skill 根据 SOP 决定是否生成 UIAction。router 节点不含业务逻辑。
    """

    name = "ui_router"
    tools = [
        "navigate_to_page",
        "fetch_cop_data",
        "fetch_energy_summary",
        "fetch_active_alarms",
    ]
    prompt_keys = ["action_agent_nav_hint"]
    description = "监控页面查询与跳转（实时 COP、能耗、报警，下发页面跳转信号）"

    @staticmethod
    def infer_navigation(
        tool_results: List[Tuple[str, Dict[str, Any], Dict[str, Any]]],
    ) -> Optional[UIAction]:
        """SOP 核心：根据本轮工具调用结果推断页面跳转。

        优先级：
          1. LLM 显式调用了 navigate_to_page → 原样采用
          2. LLM 调用了 Java 后端工具 → 根据工具类型自动映射路由

        仅返回零或一个 UIAction，避免重复跳转。

        Args:
            tool_results: [(tool_name, result_dict, args_dict), ...]

        Returns:
            UIAction 或 None
        """
        # 优先：LLM 显式调用了 navigate_to_page
        for name, result, args in tool_results:
            if name == "navigate_to_page" and "error" not in result:
                try:
                    action = UIAction(**result)
                    logger.info(
                        f"UIRouterSkill: 采用 LLM 显式跳转 → {action.route}"
                    )
                    return action
                except Exception as e:
                    logger.warning(f"UIRouterSkill: navigate_to_page 结果解析失败: {e}")

        # 兜底：Java 后端工具 → 自动推断跳转路由
        for name, result, args in tool_results:
            route = _TOOL_ROUTE_MAP.get(name)
            if route and "error" not in result:
                params = {k: v for k, v in args.items() if v is not None}
                action = UIAction(type="navigate", route=route, params=params)
                logger.info(
                    f"UIRouterSkill: 根据 {name} 自动推断跳转 → {route}"
                )
                return action

        return None
