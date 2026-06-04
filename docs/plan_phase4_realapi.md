# EnerGraph — Phase 4: 真实预测 API 对接

**目标**: 将 Mock 工具替换为真实 gRPC/HTTP 调用，工具签名不变，Mock 作为 fallback 保留。  
**前置条件**: Phase 3 完成（Agent 质量稳定）；算法团队 API 文档已提供  
**完成标志**: 三个 Mock 工具均对接真实接口，`pytest-httpx` 测试通过

---

## 业务场景

### 场景 1: TimeDiT 真实预测
用户问："明天 SH-01 的负荷预测怎么样？"

Agent 应：
1. 调用 `query_timedit_forecast`，实际请求算法团队 TimeDiT HTTP 服务
2. 返回真实预测数据（24 小时负荷/光伏曲线 + 置信区间）
3. 若 API 超时或不可用，降级为 Mock 数据并在回答中标注"演示数据"

### 场景 2: PhysicsAI 物理验证
用户问："当前冷水机组运行参数是否安全？"

Agent 应：
1. 调用 `verify_physics_consistency`，将实时 COP / 温度传入 PhysicsAI
2. 返回物理残差（偏差百分比），若超过安全阈值则触发告警

---

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/tests/test_tools_integration.py` | 用 `pytest-httpx` mock HTTP server 测试真实对接 |

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `config/agent_config.yaml` | 新增 `timedit_url` / `physics_ai_url` / `aidc_url` 字段 |
| `src/config/settings.py` | 加载新增 URL 配置 |
| `.env.example` | 新增 `TIMEDIT_URL` / `PHYSICS_AI_URL` / `AIDC_URL` |
| `src/tools/query_timedit.py` | 真实 HTTP 调用 + Mock fallback |
| `src/tools/verify_physics.py` | 真实 HTTP 调用 + Mock fallback |
| `src/tools/fetch_aidc_cooling.py` | 真实 HTTP 调用 + Mock fallback |

---

## 子任务（每个子任务 = 一个 commit）

### T1: 配置层新增 API 端点
- **文件**: `config/agent_config.yaml`, `src/config/settings.py`, `.env.example`
- **改动**:
  - `agent_config.yaml` 新增：
    ```yaml
    api_endpoints:
      timedit_url: null      # TimeDiT 服务地址，如 http://10.0.1.100:8080
      physics_ai_url: null   # PhysicsAI 服务地址
      aidc_url: null         # AIDC 液冷服务地址
    ```
  - `settings.py` 新增对应属性，读取 `.env` 中的 `TIMEDIT_URL` / `PHYSICS_AI_URL` / `AIDC_URL`
  - `.env.example` 新增注释说明
- **验收**: `settings.timedit_url` 可读取；未配置时为 None，不报错

### T2: TimeDiT 真实对接
- **文件**: `src/tools/query_timedit.py`
- **改动**:
  - 若 `TIMEDIT_URL` 已配置，调用真实 HTTP：
    ```python
    resp = httpx.post(
        f"{settings.timedit_url}/predict",
        json={"target_date": target_date, "site_id": site_id},
        timeout=30,
    )
    ```
  - 解析响应为 `TimeDiTForecast`（load_forecast / solar_forecast / confidence_interval）
  - 超时或 5xx 时降级 Mock，并在返回 dict 中追加 `"fallback": "mock"`
  - 未配置 `TIMEDIT_URL` 时直接走 Mock
- **验收**: 真实接口返回数据可解析为 `TimeDiTForecast`；Mock fallback 正常工作

### T3: PhysicsAI 真实对接
- **文件**: `src/tools/verify_physics.py`
- **改动**:
  - 若 `PHYSICS_AI_URL` 已配置：
    ```python
    resp = httpx.post(
        f"{settings.physics_ai_url}/verify",
        json={"cop": cop, "temps": temps, ...},
        timeout=20,
    )
    ```
  - 解析响应为 `PhysicsResidual`（residual_pct / is_safe / violation_fields）
  - fallback 逻辑同 T2
- **验收**: 真实接口返回数据可解析为 `PhysicsResidual`

### T4: AIDC 液冷真实对接
- **文件**: `src/tools/fetch_aidc_cooling.py`
- **改动**:
  - 若 `AIDC_URL` 已配置：
    ```python
    resp = httpx.get(
        f"{settings.aidc_url}/cooling/status",
        params={"site_id": site_id},
        timeout=15,
    )
    ```
  - 解析响应为 `AIDCCoolingStatus`
  - fallback 逻辑同 T2
- **验收**: 真实接口返回数据可解析为 `AIDCCoolingStatus`

### T5: 集成测试
- **文件**: `src/tests/test_tools_integration.py`
- **改动**:
  - 用 `pytest-httpx` mock HTTP server，模拟三个算法服务
  - 测试正常响应：请求格式正确 + 响应解析为对应 Pydantic 模型
  - 测试超时降级：mock 5xx 或超时，验证 fallback 到 Mock 数据 + `fallback: "mock"` 字段
  - 测试未配置 URL：直接返回 Mock，不发 HTTP 请求
- **验收**: 无需真实接口，`pytest src/tests/test_tools_integration.py` 全部通过

---

## 关键架构决策

**为什么用环境变量而非配置文件控制 API 地址？**  
API 地址属于部署相关配置，不同环境（dev/staging/prod）地址不同。通过 `.env` 注入比修改 `agent_config.yaml` 更符合 12-Factor App 原则，也防止误提交生产地址到 Git。

**为什么 fallback 到 Mock 而非直接报错？**  
演示和客户现场可能无真实服务。Mock fallback 保证 Agent 可用性，同时通过 `fallback: "mock"` 字段让前端/用户知道数据来源非真实，避免误导决策。

**工具签名为何不得改变？**  
`TOOL_SCHEMAS` 是 LLM function calling 的契约，改动签名会导致 LLM 调用失败，且需同步更新所有 Prompt 中的工具描述。

**与 BaseSkill 的关系**:  
`EnergyDispatchSkill.execute()` 在 T2-T4 完成后完善编排逻辑（意图解析 → 引擎调度 → 物理验证 → 报告），继承 BaseSkill 接口。工具签名不变，Skill 无需改动。

---

## 依赖安装
```bash
pip install pytest-httpx  # HTTP mock 测试
```

## 关键文件
- `src/tools/query_timedit.py` / `verify_physics.py` / `fetch_aidc_cooling.py` — 真实对接
- `src/schemas/v3_engine.py` — 输出模型（不改）
- `config/agent_config.yaml` — 新增 URL 配置

## 注意
- 工具签名（函数名、参数、返回类型）**不得改变**，否则 TOOL_SCHEMAS 需同步更新
- 真实 API 文档由算法团队提供后再开始 T2-T4

## Skills 融合说明
- T2-T4 各引擎工具替换为真实 HTTP 后，`EnergyDispatchSkill` 无需改动（工具签名不变）
- 详见 `docs/plan_skills_refactor.md`
