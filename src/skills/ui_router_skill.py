"""ui_router_skill — 监控页面查询与跳转技能

所属层：skills
依赖：src.tools.navigate_to_page, src.tools.java_backend
对接 V3 引擎：N/A（Java 后端监控 API）

SOP：
  1. 识别用户查询的监控数据类型（COP / 能耗 / 报警）
  2. 调用对应 Java 后端工具获取实时数据
  3. 生成文字总结（流式 token 输出）
  4. 调用 navigate_to_page 下发页面跳转 UIAction 信号

此 Skill 是 Phase 2 的核心新增，将 UIAction 逻辑与主节点解耦。
Java 工具（fetch_cop_data 等）在 Phase 4 替换为真实 HTTP，此 Skill 无需改动。

Prompt keys（src/config/prompts.yaml）：
  - action_agent_nav_hint : 路由表 + 跳转时机判断指令（Phase 2 T2 新增）
"""


class UIRouterSkill:
    """监控页面查询与跳转技能。

    当前为骨架占位，Phase 2 T2-T3 实现导航工具和 Java 后端工具后完善。
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
