# CHANGELOG — 青山大模型 V3.0 决策层 Agent

> 完整变更历史记录。近期变更摘要见 `AI_CONTEXT.md` §6。

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-06-12 | 老架构概念清理：删除 3 个 Mock 工具（query_timedit/verify_physics/fetch_aidc_cooling）及其在 TOOL_REGISTRY/TOOL_SCHEMAS 的注册；删除过时 Schema（TimeDiTForecast/AIDCCoolingStatus）；修正 Prompt 架构层级错误（第0层→第3层决策层）；清理所有文件头注释的老架构引用（对接V3引擎→对接算法层）；删除占位文件（checkpointer.py/sft_export.py）；更新 README 和前端文件的架构定位 | 魏博源 |
| 2026-06-12 | API 交付前端对接：新增 CORS 中间件 + 可选 Bearer Token 鉴权 + 启动脚本 run.py + API 配置段（ApiConfig）+ 前端对接文档（Vue.js 代码示例 + TypeScript 类型定义 + SSE 流式对接指南）。api.py 版本升至 0.3.0 | 魏博源 |
| 2026-06-12 | Token 自动刷新机制（Phase 4.3）：新建 src/utils/fuca_token_refresher.py（逆向福加前端 RSA 加密 + 登录 + mb/token 获取 + .env 自动更新）；改造 java_backend.py（动态 Token 管理 + 401/code=401 自动刷新重试 + 线程安全锁）；.env 新增 FUCA_LOGIN_NAME/FUCA_PASSWORD；requirements.txt 新增 pycryptodome | 魏博源 |
| 2026-06-12 | 新增 fetch_photovoltaic_daily 日度光伏发电量工具（累加 15min 功率数据计算日发电量）。修复 fetch_cop_data 字段映射（水系统累计COP=7.0）。新增 fetch_efficiency_detail 通用能效查询（8 种参数） | 魏博源 |
| 2026-06-12 | Phase 4.2 代码审查 + 重构：提取 _api_get/_api_post 公共函数消除样板；新增 fetch_photovoltaic_monthly 工具；action_agent_nav_hint prompt 精简并补充全部新工具导航规则。54 tests 全通过 | 魏博源 |
| 2026-06-12 | Phase 4.2 Task 3+4 完成：代码实现（8 个工具接入真实 API）。fetch_cop_data/fetch_active_alarms 从 Mock 改为真实 API；新增 fetch_carbon_info/fetch_photovoltaic_monthly/fetch_energy_usage/fetch_device_rank/fetch_environment_params/fetch_efficiency_calendar。schemas 新增 6 个 Pydantic 模型 | 魏博源 |
| 2026-06-12 | Phase 4.2 Task 2 完成：Chrome MCP 全量抓取（Batch 1+2+3）。5 个页面共抓取 17 个接口（含 4 个 Bonus）。抓取数据保存至 docs/api_capture_batch1.md + docs/api_capture_batch2.md | 魏博源 |
| 2026-06-11 | Phase 4.2 Task 1 完成：接口清单质量检查与补全。扫描 docs/跳转接口逻辑.md（31条接口），识别 5 个跳转路由缺失、9 个触发操作模糊、4 个出参需后处理。与用户确认后补全：环境参数跳转 `/index/index`、报警用动态日期、cwerId=3602、deviceCodes 8 个设备。生成优先级排序文档 docs/api_mapping_prioritized.md（P0×3 + P1×5 + P2×5 独立接口，暂缓 2 个） | 魏博源 |
| 2026-06-11 | Phase 4.2 Task 0 完成：路由配置解耦（routes.yaml 单点管理）。routes.yaml 新增 tools 字段关联工具；ui_router_skill.py 的 _TOOL_ROUTE_MAP 改为动态构建；app.py 的 _ROUTE_NAMES 改为动态构建；prompts.yaml 的 action_agent_nav_hint 移除硬编码路由表（仅保留推理规则）；nodes.py 新增 _build_route_table_md 动态注入路由表到 system prompt。前端改路由只需修改 routes.yaml 一处 | 魏博源 |
| 2026-06-08 | Phase 4 部分完成：接入福加真实API（fetch_energy_summary），配置site_mapping.yaml站点映射，修复Streamlit跳转链接显示问题（pending_actions被st.rerun()清除），测试文件规范化（移至src/tests/） | 魏博源 |
| 2026-06-08 | 修复：UIRouterSkill 支持多意图多跳转链接（返回 List[UIAction]），前端动态名称 + 多链接展示；修复 fetch_cop_data/fetch_active_alarms 因残存 JAVA_API_BASE_URL 引用导致异常（改为纯 Mock fallback）；清理 java_backend.py 调试日志 | 魏博源 |
| 2026-06-05 | RAG 质量修复：删除8条重复含湿量问答、优化回答格式、切换 embedding 模型为 BAAI/bge-small-zh-v1.5（中文HVAC专业术语匹配大幅提升） | 魏博源 |
| 2026-06-05 | 修复 query_hvac_knowledge NumPy 数组布尔判断错误 + Agent 导航功能修复 | 魏博源 |
| 2026-06-04 | 代码规范审计修复：11 个 __init__.py 补充标准 docstring、graph/nodes.py 和 services/api.py 补充返回值类型标注和 Args/Returns docstring、CLAUDE.md 补充 skills/services/memory/tests 层名枚举 | 魏博源 |
| 2026-06-04 | Skills 基类完成：BaseSkill 抽象基类 + 4 个 Skill 迁移 + 统一调度 + get_skill/get_matched_skills 工厂函数 + 15 测试通过（总 53） | 魏博源 |
| 2026-06-04 | Phase 7 完成：多意图识别与拆分执行（IntentItem + intent_plan + 分段报告 + SSE intent_plan + 16 测试通过） | 魏博源 |
| 2026-06-04 | Phase 3 完成：RAG 质量优化（置信度阈值过滤 + MMR 去重 + 拒答 + 引用来源 + 19 测试通过） | 魏博源 |
| 2026-06-04 | 新增 Phase 7：多意图识别与拆分执行，创建 plan_phase7_multi_intent.md，更新 AI_CONTEXT.md | 魏博源 |
| 2026-06-04 | 全面完善 Phase 3/4/5/6 规划文档（补充业务场景/架构决策/详细改动），新建 plan_skills_base_class.md（BaseSkill 基类方案），更新 AI_CONTEXT.md | 魏博源 |
| 2026-06-04 | 规划 Phase 6：数据可视化 + 报表导出，创建 plan_phase6_visualization_export.md，更新 AI_CONTEXT.md（§1.3/§3/§4/§5/§6） | 魏博源 |
| 2026-05-26 | Phase 2 T6：page_context 注入 cognitive_parser system prompt（current_route + site_id），新建 test_action_agent.py 集成测试（2 passed） | 魏博源 |
| 2026-05-26 | Phase 2 T2（重构）：导航工具 navigate_to_page + UIRouterSkill.infer_navigation SOP，v3_engine_router 改为 Skill 调度分发（不写业务逻辑），prompts.yaml 新增 action_agent_nav_hint 路由表 | 魏博源 |
| 2026-05-26 | Phase 2 T3：Java 后端工具（fetch_cop_data/energy_summary/active_alarms），Mock fallback，注册到 TOOL_REGISTRY | 魏博源 |
| 2026-05-26 | Phase 2 T5：POST /stream SSE 端点，astream_events 推送 text/action/done 事件 | 魏博源 |
| 2026-05-26 | Phase 2 T4：FastAPI 骨架 + /invoke 端点，接收 ActionAgentInput，同步运行 graph 返回 report + actions | 魏博源 |
| 2026-05-26 | Phase 2 T1：新建 action_agent.py（PageContext/ActionAgentInput/UIAction），AgentState 扩展 page_context + pending_actions | 魏博源 |
| 2026-05-22 | Skills 架构重组：建立 src/skills/ 骨架（4个Skill），更新 CLAUDE.md/AI_CONTEXT.md，新增 plan_skills_refactor.md | 魏博源 |
| 2026-05-21 | 工程规范升级：Prompt 强制集中管理 + 版本控制（CLAUDE.md/AI_CONTEXT.md 同步更新） | 魏博源 |
| 2026-05-21 | Phase 2 升级为 Action Agent：UIAction 跳转信号 + Java 后端工具层，创建 plan_phase2_action_agent.md | 魏博源 |
| 2026-05-21 | 规划 Phase 2-5，创建 docs/plan_*.md，精简并重写 AI_CONTEXT | 魏博源 |
| 2026-05-21 | token 级流式前端（stream_mode=messages），streaming=True | 魏博源 |
| 2026-05-18 | LLM_PROVIDER 切换、DeepSeek V4 适配、ONNX Embedding | 魏博源 |
| 2026-05-18 | HVAC RAG 集成（5613 条）、ReAct 循环、对话前端 | 魏博源 |
| 2026-05-14 | Phase 1 重构：V3 架构全量实现 | 魏博源 |

> 更早历史见 `git log`。
