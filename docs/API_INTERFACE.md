# API 接口规范文档

本文档定义前后端数据交互格式和工具函数接口规范，便于团队协作开发。

## 数据模型

### 1. 输入数据结构

#### AgentInput
```python
{
  "forecast_data": ForecastData,
  "system_state": SystemState,
  "basic_info": BasicInfo
}
```

#### ForecastData
```python
{
  "load": List[float],        # 24小时负载预测 (kWh)
  "solar": List[float],       # 24小时光伏预测 (kWh)
  "grid_price": List[float]   # 24小时电价 (元/kWh)
}
```

#### SystemState
```python
{
  "soc": float,              # 当前储能SOC (0-1)
  "soc_max": float,          # 最大SOC (默认0.9)
  "soc_min": float,          # 最小SOC (默认0.2)
  "max_power": float,        # 最大充放电功率 (kW)
  "user_pref": str           # 用户偏好 (cost_priority/eco_priority)
}
```

#### BasicInfo
```python
{
  "timezone": str,           # 时区 (默认UTC+8)
  "currency": str,           # 货币单位 (默认CNY)
  "query": str               # 用户查询
}
```

### 2. 输出数据结构

#### AgentOutput
```python
{
  "report": str,             # Markdown格式报告
  "language": str            # 输出语言 (zh/en)
}
```

---

## 工具函数接口

### 1. compute_metrics

**功能**: 分时段统计购电、售电、储能充放电、光伏消纳等核心指标

**输入参数**:
```python
load: List[float]          # 24小时负载数据
solar: List[float]         # 24小时光伏数据
grid_price: List[float]    # 24小时电价数据
```

**返回结果**:
```python
{
  "total_load_kwh": float,           # 总负载 (kWh)
  "total_solar_kwh": float,          # 总光伏发电 (kWh)
  "solar_utilization_pct": float,    # 光伏利用率 (%)
  "valley_load_kwh": float,          # 谷段负载 (kWh)
  "peak_load_kwh": float,            # 峰段负载 (kWh)
  "avg_price": float                 # 平均电价 (元/kWh)
}
```

### 2. compare_price

**功能**: 对比不同时段的购/售电价，识别峰谷套利机会

**输入参数**:
```python
grid_price: List[float]    # 24小时电价数据
```

**返回结果**:
```python
{
  "min_price": float,                  # 最低电价 (元/kWh)
  "max_price": float,                  # 最高电价 (元/kWh)
  "min_price_hours": List[int],        # 最低电价时段列表 (0-23)
  "max_price_hours": List[int],        # 最高电价时段列表 (0-23)
  "price_diff": float,                 # 价差 (元/kWh)
  "arbitrage_potential_pct": float     # 套利潜力 (%)
}
```

### 3. calc_benefit

**功能**: 基于调度数据计算预计成本/收益，对比基准方案

**输入参数**:
```python
load: List[float]          # 24小时负载数据
solar: List[float]         # 24小时光伏数据
grid_price: List[float]    # 24小时电价数据
soc: float                 # 当前储能SOC
max_power: float           # 最大充放电功率
```

**返回结果**:
```python
{
  "baseline_cost": float,    # 基准方案成本 (元)
  "optimized_cost": float,   # 优化方案成本 (元)
  "savings": float,          # 节省金额 (元)
  "savings_pct": float       # 节省比例 (%)
}
```

---

## Agent 状态流转

### AgentState
```python
{
  # 输入数据
  "load": List[float],
  "solar": List[float],
  "grid_price": List[float],
  "soc": float,
  "max_power": float,
  "user_pref": str,
  "query": str,
  
  # 工具调用结果
  "metrics": Dict[str, Any],
  "price_analysis": Dict[str, Any],
  "benefit": Dict[str, Any],
  
  # 控制流
  "messages": List[Dict[str, Any]],
  "next_action": str,           # "call_tool" | "generate_report" | "end"
  "tool_to_call": str | None,
  "iteration": int,

  # 扩展（RAG 预留）
  "context": str | None,
  "history": List[Dict] | None,

  # Agent 输出
  "report": str,
  "error": str | None
}
```

---

## 前端交互流程

1. **用户输入**: 通过 Streamlit 界面输入/选择示例数据
2. **数据验证**: 使用 Pydantic 模型验证输入格式
3. **Agent 执行**: 调用 LangGraph 状态图
4. **结果展示**: 渲染 Markdown 报告 + 工具调用详情

---

## 扩展指南

### 添加新工具

1. 在 `src/tools/` 下创建新的工具函数文件
2. 在 `src/tools/__init__.py` 的 `TOOL_REGISTRY` 和 `TOOL_SCHEMAS` 中注册
3. 更新 `config/agent_config.yaml` 工具列表
4. 在本文档中添加接口说明

### 修改数据模型

1. 更新 `src/schemas/` 下的对应文件
2. 同步修改 `src/agents/energy/nodes.py` 中的引用
3. 更新本文档的数据结构说明
4. 通知团队成员

---

**最后更新**: 2026-05-08
