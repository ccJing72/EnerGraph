# EnerGraph — Phase 4: 真实预测 API 对接

**目标**: 将 Mock 工具替换为真实 gRPC/HTTP 调用，工具签名不变。
**前置条件**: Phase 3 完成（Agent 质量稳定）
**完成标志**: 三个 Mock 工具均对接真实接口，Mock 作为 fallback 保留

---

## 子任务（每个子任务 = 一个 commit）

### T1: 配置层新增 API 端点
- **文件**: `config/agent_config.yaml`, `src/config/settings.py`
- **改动**: 新增 `timedit_url`, `physics_ai_url`, `aidc_url` 字段；`.env.example` 新增对应变量
- **验收**: `settings.timedit_url` 可读取；未配置时不报错（None）

### T2: TimeDiT 真实对接
- **文件**: `src/tools/query_timedit.py`
- **改动**: 若 `TIMEDIT_URL` 已配置则调用真实 HTTP；否则 fallback 到 Mock
- **输出模型**: `TimeDiTForecast` 不变
- **验收**: 真实接口返回数据可解析为 `TimeDiTForecast`

### T3: PhysicsAI 真实对接
- **文件**: `src/tools/verify_physics.py`
- **改动**: 同上，`PHYSICS_AI_URL` 控制
- **输出模型**: `PhysicsResidual` 不变

### T4: AIDC 液冷真实对接
- **文件**: `src/tools/fetch_aidc_cooling.py`
- **改动**: 同上，`AIDC_URL` 控制
- **输出模型**: `AIDCCoolingStatus` 不变

### T5: 集成测试
- **文件**: `src/tests/test_tools_integration.py`
- **改动**: 用 `pytest-httpx` mock HTTP server，验证请求格式和响应解析
- **验收**: 无需真实接口，pytest 通过

---

## 关键文件
- `src/tools/query_timedit.py` / `verify_physics.py` / `fetch_aidc_cooling.py`
- `src/schemas/v3_engine.py` — 输出模型（不改）
- `config/agent_config.yaml` — 新增 URL 配置

## 注意
- 工具签名（函数名、参数、返回类型）**不得改变**，否则 TOOL_SCHEMAS 需同步更新
- 真实 API 文档由算法团队提供后再开始 T2-T4

## Skills 融合说明
- T2-T4 各引擎工具替换为真实 HTTP 后，`EnergyDispatchSkill` 无需改动（工具签名不变）
- 详见 `docs/plan_skills_refactor.md`
