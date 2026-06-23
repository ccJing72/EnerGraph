# MCP 接口契约 — 算法模型层 ↔ 决策层

> 定义决策层（EnerGraph）与算法模型层（9 个计算引擎）之间的 MCP 接口规范。
> 算法团队按此规范封装 MCP Server，Agent 通过 MCP Client 调用。
> 版本: v1.0（草案）| 最后更新: 2026-06-12 | 状态: **待算法团队确认**

---

## 1. 通用规范

| 项目 | 规范 |
|------|------|
| 协议 | MCP (Model Context Protocol) |
| 传输 | HTTP + SSE 流式响应 |
| Server 框架 | FastAPI + JSON Schema |
| 数据格式 | JSON（`application/json`） |
| 认证 | Bearer Token（与 EnerGraph 统一鉴权） |
| 错误格式 | `{"error": {"code": "...", "message": "...", "retryable": true/false}}` |
| 超时 | 单次调用 ≤ 30s，超时返回 `timeout` 错误 |

---

## 2. 接口清单

| # | 模型名称 | MCP Tool Name | 类型 | 优先级 | 调用方 |
|---|---------|--------------|------|--------|--------|
| 1 | 电负荷预测 | `predict_load` | 预测 | P0 | **Agent 直接调用**（单预测查询）+ optimize_dispatch 内部调用 |
| 2 | 光伏出力预测 | `predict_solar` | 预测 | P0 | **Agent 直接调用**（单预测查询）+ optimize_dispatch 内部调用 |
| 3 | 电价预测 | `predict_electricity_price` | 预测 | P1 | **Agent 直接调用**（电价趋势查询）+ optimize_dispatch 内部调用 |
| 4 | 冷负荷预测 | `predict_cooling_load` | 预测 | P1 | Agent 直接调用 |
| 5 | 碳排放预测 | `predict_carbon` | 预测 | P2 | Agent 直接调用 |
| 6 | 设备健康诊断 | `diagnose_equipment` | 诊断 | P1 | Agent 直接调用 |
| 7 | 机房能效诊断 | `diagnose_room_efficiency` | 诊断 | P2 | Agent 直接调用 |
| 8 | 制冷系统寻优 | `optimize_cooling` | 优化 | P1 | Agent 直接调用 |
| 9 | 储能调度优化 | `optimize_dispatch` | 优化 | P0 | **Agent 直接调用**（PowerAI 核心） |

> **双路径调用设计**：
> - **单预测查询路径**：用户问"明天预计用多少电"、"光伏发电趋势"等单一预测问题时，Agent 直接调用对应的预测模型（#1-5），返回简洁预测结果。
> - **综合调度路径**：用户问"给我出个充放电策略"时，Agent 只需调用 `optimize_dispatch`（#9），由优化模型内部自行调用各预测模型获取数据，综合计算后返回候选方案。Agent 无需分别获取预测数据再拼装传入——这降低了编排复杂度，也让优化模型可独立迭代预测策略。
>
> 两条路径并存，Agent 按用户意图智能选择。

---

## 3. 接口详细定义

### 3.1 predict_load — 电负荷预测

> LSTM+Attention / PatchTST，MAPE 5-8%

**输入**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "horizon_hours": 24,
  "features": {
    "production_schedule": "normal",
    "weather_forecast": "sunny"
  }
}
```

**输出**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "model_version": "load-v2.1",
  "forecasts": [
    {"hour": 0, "load_kw": 420.5, "confidence_lower": 380.0, "confidence_upper": 460.0},
    {"hour": 1, "load_kw": 380.2, "confidence_lower": 345.0, "confidence_upper": 415.0}
  ],
  "peak_hour": 10,
  "peak_load_kw": 1580.0,
  "daily_total_kwh": 18200.0
}
```

---

### 3.2 predict_solar — 光伏出力预测

> CNN-LSTM-Transformer + 晴空模型物理约束，MAPE 8-12%

**输入**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "horizon_hours": 24,
  "panel_capacity_kw": 200
}
```

**输出**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "model_version": "solar-v1.3",
  "forecasts": [
    {"hour": 6, "solar_kw": 15.2, "irradiance": 200},
    {"hour": 12, "solar_kw": 175.0, "irradiance": 850}
  ],
  "daily_total_kwh": 820.0,
  "peak_power_kw": 178.5,
  "peak_hour": 12,
  "weather_condition": "partly_cloudy"
}
```

---

### 3.3 predict_electricity_price — 电价预测

> Transformer + LightGBM 集成 + 峰谷时段编码

**输入**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "horizon_hours": 24
}
```

**输出**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "tariff_type": "two_part",
  "forecasts": [
    {"hour": 0, "price_yuan_kwh": 0.35, "period": "valley"},
    {"hour": 10, "price_yuan_kwh": 1.12, "period": "peak"},
    {"hour": 14, "price_yuan_kwh": 0.72, "period": "flat"}
  ],
  "peak_valley_spread": 0.77
}
```

---

### 3.4 predict_cooling_load — 冷负荷预测

> LSTM-XGBoost + RC 网络热动力学建模

**输入**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "horizon_hours": 24,
  "outdoor_temp_forecast": [28, 29, 30, 32, 33, 34],
  "occupancy_estimate": "normal"
}
```

**输出**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "forecasts": [
    {"hour": 0, "cooling_load_kw": 80.0},
    {"hour": 14, "cooling_load_kw": 450.0}
  ],
  "peak_cooling_kw": 480.0,
  "daily_total_kwh": 5600.0
}
```

---

### 3.5 predict_carbon — 碳排放预测

> 排放因子法 + LSTM + ISO 14064

**输入**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "horizon_days": 7,
  "energy_data": {"grid_kwh": 5000, "solar_kwh": 800}
}
```

**输出**：
```json
{
  "site_id": "FJJB000001",
  "forecasts": [
    {"date": "2026-06-15", "carbon_kg_co2e": 2800.0, "grid_emission": 3200.0, "solar_offset": 400.0}
  ],
  "weekly_total_kg_co2e": 19500.0,
  "emission_factor": 0.5810
}
```

---

### 3.6 diagnose_equipment — 设备健康诊断

> CNN-LSTM + ECM 融合，SOH 评估 + RUL 预测

**输入**：
```json
{
  "site_id": "FJJB000001",
  "equipment_id": "KTXT-CWER-CWEG-0001",
  "equipment_type": "chiller",
  "diagnosis_scope": ["soh", "rul", "anomaly"]
}
```

**输出**：
```json
{
  "equipment_id": "KTXT-CWER-CWEG-0001",
  "equipment_type": "chiller",
  "diagnosis_time": "2026-06-15T10:30:00",
  "soh_percent": 92.5,
  "rul_days": 1200,
  "health_status": "good",
  "anomalies": [
    {
      "type": "vibration_increase",
      "severity": "low",
      "description": "压缩机振动值较上月上升 8%，仍在正常范围内",
      "recommended_action": "下次保养时重点检查"
    }
  ],
  "trend_data": {
    "soh_30d_trend": [93.0, 92.8, 92.5],
    "efficiency_trend": [4.2, 4.1, 4.0]
  }
}
```

---

### 3.7 diagnose_room_efficiency — 机房能效诊断

> Autoencoder + Isolation Forest + PUE 分解

**输入**：
```json
{
  "site_id": "FJJB000001",
  "room_id": "cwer-001",
  "analysis_period": "last_7_days"
}
```

**输出**：
```json
{
  "room_id": "cwer-001",
  "current_pue": 1.45,
  "pue_breakdown": {
    "it_load_ratio": 0.69,
    "cooling_ratio": 0.22,
    "power_distribution_loss": 0.09
  },
  "anomalies": [
    {
      "type": "cooling_efficiency_drop",
      "description": "夜间低负载时段 COP 偏低 15%",
      "potential_saving_kwh": 120
    }
  ],
  "optimization_suggestions": [
    "建议夜间降低冷冻水设定温度 1°C，预计节能 5%",
    "冷却塔风机可降频运行，当前负载率仅 40%"
  ],
  "benchmark": {
    "industry_avg_pue": 1.58,
    "ranking_percentile": 75
  }
}
```

---

### 3.8 optimize_cooling — 制冷系统主动寻优

> DDPG/SAC + MPC 滚动优化

**输入**：
```json
{
  "site_id": "FJJB000001",
  "cooling_load_forecast_kw": [100, 120, 200, 350, 450, 480],
  "outdoor_temp_forecast": [28, 29, 30, 32, 33, 34],
  "current_equipment_status": {
    "chillers_running": 1,
    "chilled_water_temp": 7.0
  },
  "optimization_horizon_hours": 6,
  "constraints": {
    "min_chilled_water_temp": 5.0,
    "max_chilled_water_temp": 12.0,
    "comfort_temp_range": [22, 26]
  }
}
```

**输出**：
```json
{
  "site_id": "FJJB000001",
  "optimization_horizon_hours": 6,
  "recommended_actions": [
    {"hour": 0, "chilled_water_setpoint": 7.0, "chillers": 1, "cooling_tower_fan_hz": 35},
    {"hour": 3, "chilled_water_setpoint": 6.5, "chillers": 2, "cooling_tower_fan_hz": 45}
  ],
  "expected_saving_kwh": 85.0,
  "expected_cop_improvement": 0.3,
  "safety_check": "all_within_limits"
}
```

---

### 3.9 optimize_dispatch — 储能调度优化（PowerAI 核心）

> DQN/PPO + NSGA-II 多目标帕累托优化

**设计原则**：预测模型（负荷/光伏/电价）作为本模型的内部依赖，由优化模型自行调用。Agent 只需传入站点 ID、电池状态和业务约束，无需分别获取预测数据再拼装传入。

**输入**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "battery_status": {
    "soc_percent": 30,
    "capacity_kwh": 1000,
    "max_charge_kw": 500,
    "max_discharge_kw": 500,
    "soh_percent": 95
  },
  "constraints": {
    "min_soc_percent": 10,
    "max_soc_percent": 95,
    "max_demand_kw": 1900,
    "grid_connection_kw": 2000
  },
  "user_preferences": {
    "safety_weight": 0.4,
    "cost_weight": 0.4,
    "carbon_weight": 0.2
  }
}
```

> **注**：`load_forecast_kw`、`solar_forecast_kw`、`price_forecast_yuan_kwh` 不再由 Agent 传入，由优化模型内部调用 predict_load / predict_solar / predict_electricity_price 获取。如优化模型实现上需要 Agent 侧传入预测数据（例如为降低优化模型外部依赖），可回退为显式传入模式。

**输出**：
```json
{
  "site_id": "FJJB000001",
  "target_date": "2026-06-15",
  "candidates": [
    {
      "strategy_id": "A",
      "label": "稳健型",
      "description": "凌晨低谷充满，上午高峰放电削峰",
      "charge_schedule": [
        {"hour": 0, "power_kw": 200, "grid_or_solar": "grid"}
      ],
      "discharge_schedule": [
        {"hour": 10, "power_kw": 300, "purpose": "peak_shaving"}
      ],
      "expected_revenue_yuan": 1080,
      "expected_peak_demand_kw": 1850,
      "risk_level": "low",
      "carbon_reduction_kg": 45
    },
    {
      "strategy_id": "B",
      "label": "激进型",
      "description": "在 A 基础上下午二次放电",
      "expected_revenue_yuan": 1350,
      "expected_peak_demand_kw": 1920,
      "risk_level": "medium",
      "risk_note": "需量可能接近上限"
    }
  ],
  "recommendation": "A",
  "recommendation_reason": "根据上周经验，方案 B 的需量风险偏高"
}
```

---

## 4. 错误码规范

| 错误码 | 含义 | 决策层处理 |
|--------|------|-----------|
| `model_unavailable` | 模型未部署 / 服务不可用 | 提示用户"算法模型暂未接入" |
| `insufficient_data` | 输入数据不足（如历史数据太短） | 提示用户需要更多数据 |
| `timeout` | 计算超时（> 30s） | 重试 1 次，仍失败则提示 |
| `invalid_input` | 输入参数校验失败 | 提示用户修正输入 |
| `internal_error` | 模型内部错误 | 记录日志，提示用户稍后重试 |

---

## 5. 部署约定

| 项目 | 约定 |
|------|------|
| MCP Server 地址 | 由 `.env` 中 `MCP_SERVER_BASE_URL` 配置 |
| 版本管理 | 每次输出包含 `model_version` 字段 |
| 热更新 | 新增模型只需注册 MCP Server，决策层无需改代码 |
| Mock 降级 | 算法模型未就绪时，决策层使用 Mock 数据（当前状态） |

---

**下一步**：与算法团队确认接口字段 → 根据确认结果更新本文 → 编写 MCP Client 调用代码
