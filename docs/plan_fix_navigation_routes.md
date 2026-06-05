# Agent 页面导航功能修复实施计划

**文档版本**: v1.0  
**创建日期**: 2026-06-05  
**负责模块**: UIRouterSkill + cognitive_parser  
**关联文档**: `docs/analysis_nav_routes.md`, `docs/plan_phase2_action_agent.md`

---

## 1. 执行摘要 (Executive Summary)

### 1.1 问题定位

根据 `docs/analysis_nav_routes.md` 的福加网页路由分析报告，当前 Agent 页面导航功能存在**严重架构缺陷**：

| 缺陷编号 | 问题描述 | 影响范围 | 严重程度 |
|---------|---------|---------|---------|
| **DEF-001** | `prompts.yaml` 中的路由表全部为虚假路径（如 `/chiller-room`） | cognitive_parser 节点 | 🔴 严重 |
| **DEF-002** | `ui_router_skill.py` 中的 `_TOOL_ROUTE_MAP` 自动推断逻辑生成虚假路径 | UIRouterSkill 执行层 | 🔴 严重 |
| **DEF-003** | 真实前端路由为多级嵌套结构（如 `/integrated-monitor/energy-monitor`），与当前单层路由假设不符 | 整体导航逻辑 | 🔴 严重 |
| **DEF-004** | 10 个页面需要项目上下文/权限才能访问（重定向至 `/fucaView`），Agent 无感知机制 | 用户体验 | 🟡 中等 |
| **DEF-005** | 缺少路由表版本同步机制，前端更新路由后 Agent 无法自动获知 | 长期维护性 | 🟡 中等 |

### 1.2 修复目标

- **短期目标 (本计划范围)**：修复 DEF-001、DEF-002、DEF-003，使 Agent 能正确导航已验证的 24 个真实页面
- **中期目标 (后续迭代)**：建立路由表 API 端点，实现动态路由查询
- **长期目标 (架构演进)**：前端注入路由表至 `page_context`，实现零配置同步

### 1.3 设计原则

1. **架构红线遵守**：Agent 仅作"翻译官"，不直接计算路由逻辑，所有路由映射来自配置或 API
2. **最小侵入**：优先修改配置文件（`prompts.yaml`），其次修改 Skill 代码（`ui_router_skill.py`），避免改动 Graph 核心节点
3. **向后兼容**：保留当前 SSE + UIAction 机制，不破坏前端 `useAgentSSE.ts` 现有逻辑
4. **可测试性**：所有路由映射逻辑必须可单元测试，不依赖 LLM 调用

---

## 2. 当前状态分析 (Current State Analysis)

### 2.1 现有路由数据结构

#### 2.1.1 prompts.yaml 中的虚假路由表

**位置**: `src/config/prompts.yaml` → `cognitive_parser` → 路由提示部分

**当前内容** (示例片段):
```yaml
cognitive_parser: |
  ...
  可用页面路由：
  - /chiller-room (冷机房监控)
  - /energy-monitor (能源监控)
  - /alarm-center (告警中心)
  ...
```

**问题**: 这些路径在真实前端不存在，导致 LLM 生成错误的 `navigate_to_page` 工具调用参数。

#### 2.1.2 ui_router_skill.py 中的映射逻辑

**位置**: `src/skills/ui_router_skill.py` → `_TOOL_ROUTE_MAP` 字典

**当前逻辑**:
```python
_TOOL_ROUTE_MAP = {
    "navigate_to_page": {
        "冷机房": "/chiller-room",
        "能源监控": "/energy-monitor",
        ...
    }
}
```

**问题**: 硬编码的虚假路径，且映射规则与真实前端路由结构不匹配。

### 2.2 真实前端路由结构 (来自 analysis_nav_routes.md)

#### 2.2.1 路由分类统计

根据福加网页爬取分析，真实可用路由共 **24 个**，按功能模块分类：

| 分类 | 数量 | 典型路径 |
|------|------|---------|
| **综合监控** | 3 | `/integrated-monitor/energy-monitor` |
| **分析面板** | 5 | `/analysis/consumption-panel` |
| **运维管理** | 7 | `/operation/work-order-list` |
| **系统配置** | 5 | `/system/user-management` |
| **设备监控** | 4 | `/device/chiller-monitoring` |

**关键发现**:
- 所有路由均为 **两级嵌套** 结构 (`/<category>/<page>`)
- 路径使用 **kebab-case** 命名规范（如 `energy-monitor`）
- 中文页面名称与路径存在 **非线性映射** 关系（如 "能源监控总览" → `/integrated-monitor/energy-monitor`）

#### 2.2.2 受限页面 (需要权限/项目上下文)

以下 10 个页面在无上下文访问时会重定向至 `/fucaView`:

```
/analysis/load-forecast          # 负荷预测
/analysis/equipment-efficiency   # 设备效率分析
/operation/inspection-plan       # 巡检计划
/operation/maintenance-record    # 维护记录
/system/permission-config        # 权限配置
/device/hvac-control             # 暖通控制
... (共10个，详见 analysis_nav_routes.md §3.2)
```

**短期处理策略**: 在路由映射中标记这些页面，Agent 导航时附加提示（如 "该页面需要选择项目后才能查看"）。

---

## 3. 解决方案设计 (Solution Design)

### 3.1 总体架构变更

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 配置驱动 (本计划实施)                                   │
├─────────────────────────────────────────────────────────────────┤
│  prompts.yaml                                                    │
│  ├─ cognitive_parser: 包含完整真实路由表 (24个)                  │
│  └─ ui_router_hint: 新增受限页面提示模板                        │
│                                                                   │
│  ui_router_skill.py                                              │
│  ├─ 移除硬编码 _TOOL_ROUTE_MAP                                   │
│  ├─ 新增 ROUTE_REGISTRY (从 YAML 加载)                          │
│  └─ 新增 get_route_by_keywords() 模糊匹配函数                    │
├─────────────────────────────────────────────────────────────────┤
│  Phase 2: API 驱动 (中期规划, 不在本计划范围)                    │
├─────────────────────────────────────────────────────────────────┤
│  新增 /api/agent/routes 端点                                     │
│  └─ 返回 { routes: [...], restricted: [...] }                   │
│                                                                   │
│  cognitive_parser 启动时调用 fetch_route_table tool              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心变更点

#### 3.2.1 prompts.yaml 路由表更新

**新增专用配置块** `route_registry`:

```yaml
# 页面路由注册表 (来自前端真实路由, 同步日期: 2026-06-05)
route_registry:
  accessible:  # 24个可直接访问页面
    - path: "/integrated-monitor/energy-monitor"
      keywords: ["能源监控", "能源监控总览", "能耗"]
      category: "综合监控"
      description: "实时能耗数据、峰谷分析"
    
    - path: "/analysis/consumption-panel"
      keywords: ["能耗分析", "消费面板", "用能分析"]
      category: "分析面板"
      description: "历史能耗趋势、同比环比"
    
    # ... (完整24条记录)
  
  restricted:  # 10个受限页面
    - path: "/analysis/load-forecast"
      keywords: ["负荷预测"]
      reason: "需要选择项目后查看"
    # ... (完整10条记录)
```

**优势**:
- 集中管理所有路由映射
- 支持多关键词模糊匹配（提升 LLM 意图识别准确率）
- 与 CLAUDE.md Prompt 管理规范对齐

#### 3.2.2 ui_router_skill.py 重构

**移除内容**:
```python
# 删除硬编码字典
_TOOL_ROUTE_MAP = { ... }  # 完全删除
```

**新增内容**:
```python
from src.config.settings import settings

# 启动时加载路由注册表
ROUTE_REGISTRY = settings.prompts.get("route_registry", {})
ACCESSIBLE_ROUTES = ROUTE_REGISTRY.get("accessible", [])
RESTRICTED_ROUTES = ROUTE_REGISTRY.get("restricted", [])

def get_route_by_keywords(user_intent: str) -> dict:
    """根据用户意图关键词匹配最佳路由
    
    Args:
        user_intent: 用户输入的页面描述（如"能源监控"、"工单列表"）
    
    Returns:
        {
            "path": "/integrated-monitor/energy-monitor",
            "category": "综合监控",
            "is_restricted": False,
            "restriction_reason": None
        }
    """
    # 模糊匹配逻辑（使用 difflib.SequenceMatcher 或简单关键词包含）
    pass
```

**设计要点**:
- 路由映射逻辑从配置文件驱动，代码仅负责查询
- 支持模糊匹配（用户说"能源"也能匹配"能源监控总览"）
- 返回结构化数据，包含受限标记

### 3.3 数据流变更

#### 修复前的流程 (有缺陷):
```
用户输入: "打开能源监控页面"
    ↓
cognitive_parser (LLM 基于虚假路由表推理)
    ↓
生成 Tool Call: navigate_to_page(page_name="能源监控")
    ↓
ui_router_skill 查询 _TOOL_ROUTE_MAP["能源监控"] → "/energy-monitor" ❌
    ↓
返回 UIAction: {"type": "navigate", "payload": {"path": "/energy-monitor"}}
    ↓
前端执行 router.push("/energy-monitor") → 404 页面
```

#### 修复后的流程 (正确):
```
用户输入: "打开能源监控页面"
    ↓
cognitive_parser (LLM 基于真实路由表推理)
    ↓
生成 Tool Call: navigate_to_page(page_name="能源监控")
    ↓
ui_router_skill.get_route_by_keywords("能源监控")
    ├─ 匹配 ROUTE_REGISTRY["accessible"][0]
    └─ 返回 {"path": "/integrated-monitor/energy-monitor", ...} ✅
    ↓
返回 UIAction: {"type": "navigate", "payload": {"path": "/integrated-monitor/energy-monitor"}}
    ↓
前端执行 router.push("/integrated-monitor/energy-monitor") → 正确页面
```

---

## 4. 实施阶段 (Implementation Phases)

### 4.1 Phase 1: 路由注册表构建 (优先级: P0)

#### 任务 4.1.1: 创建路由配置文件

**文件**: `config/routes.yaml` (新建)

**内容**: 从 `docs/analysis_nav_routes.md` §2.1 提取完整的 24 个可访问路由和 10 个受限路由，结构化为 YAML。

**数据结构**:
```yaml
# 路由注册表 v1.0 (同步日期: 2026-06-05)
accessible_routes:
  - path: "/integrated-monitor/energy-monitor"
    name: "能源监控总览"
    keywords: ["能源监控", "能耗", "能源"]
    category: "综合监控"
    description: "实时能耗数据、峰谷分析、电价统计"
  
  - path: "/integrated-monitor/device-status"
    name: "设备状态总览"
    keywords: ["设备状态", "设备监控", "设备"]
    category: "综合监控"
    description: "冷机、水泵、冷塔运行状态"
  
  # ... 继续添加其余 22 个路由

restricted_routes:
  - path: "/analysis/load-forecast"
    name: "负荷预测"
    keywords: ["负荷预测", "预测"]
    reason: "需要选择项目后查看"
  
  # ... 继续添加其余 9 个路由
```

**验收标准**:
- ✅ 所有 24 个可访问路由完整录入
- ✅ 所有 10 个受限路由完整录入
- ✅ 每个路由至少包含 2-3 个关键词变体
- ✅ YAML 语法验证通过 (`yamllint config/routes.yaml`)

**时间估算**: 1.5 小时

#### 任务 4.1.2: 集成路由表到 prompts.yaml

**文件**: `src/config/prompts.yaml`

**修改内容**:
```yaml
# 在文件顶部新增
route_registry: !include ../config/routes.yaml

# 修改 cognitive_parser 的路由提示部分
cognitive_parser: |
  你是能源管理系统的意图解析器...
  
  **可用页面路由** (共24个):
  {%- for route in route_registry.accessible_routes %}
  - {{ route.name }} ({{ route.path }}): {{ route.description }}
  {%- endfor %}
  
  **受限页面** (需要项目上下文, 共10个):
  {%- for route in route_registry.restricted_routes %}
  - {{ route.name }}: {{ route.reason }}
  {%- endfor %}
```

**注意事项**:
- 使用 YAML `!include` 指令避免重复维护
- 如果 PyYAML 不支持 `!include`，改用 Jinja2 模板渲染
- 确保 `settings.py` 的 `load_prompts()` 函数能正确解析

**验收标准**:
- ✅ `settings.prompts["route_registry"]` 可正常读取
- ✅ `cognitive_parser` Prompt 包含所有真实路由

**时间估算**: 0.5 小时

### 4.2 Phase 2: ui_router_skill.py 重构 (优先级: P0)

#### 任务 4.2.1: 重构路由匹配逻辑

**文件**: `src/skills/ui_router_skill.py`

**删除代码**:
```python
# 完全移除硬编码字典
_TOOL_ROUTE_MAP = {
    "navigate_to_page": {
        "冷机房": "/chiller-room",
        "能源监控": "/energy-monitor",
        ...
    }
}
```

**新增代码**:
```python
from difflib import SequenceMatcher
from src.config.settings import settings

class RouteRegistry:
    """路由注册表管理器"""
    
    def __init__(self):
        self.routes_config = settings.prompts.get("route_registry", {})
        self.accessible = self.routes_config.get("accessible_routes", [])
        self.restricted = self.routes_config.get("restricted_routes", [])
    
    def find_route(self, keyword: str) -> dict:
        """根据关键词匹配路由
        
        Args:
            keyword: 用户输入的页面描述
        
        Returns:
            {
                "path": "/integrated-monitor/energy-monitor",
                "name": "能源监控总览",
                "is_restricted": False,
                "restriction_reason": None
            }
        """
        best_match = None
        best_score = 0.0
        
        # 先匹配可访问路由
        for route in self.accessible:
            for kw in route.get("keywords", []):
                score = SequenceMatcher(None, keyword, kw).ratio()
                if score > best_score:
                    best_score = score
                    best_match = {
                        "path": route["path"],
                        "name": route["name"],
                        "is_restricted": False,
                        "restriction_reason": None
                    }
        
        # 再匹配受限路由
        for route in self.restricted:
            for kw in route.get("keywords", []):
                score = SequenceMatcher(None, keyword, kw).ratio()
                if score > best_score:
                    best_score = score
                    best_match = {
                        "path": route["path"],
                        "name": route["name"],
                        "is_restricted": True,
                        "restriction_reason": route["reason"]
                    }
        
        if best_score < 0.6:  # 相似度阈值
            return {"error": f"未找到匹配的页面: {keyword}"}
        
        return best_match

# 全局单例
route_registry = RouteRegistry()
```

**验收标准**:
- ✅ 移除所有硬编码路由字典
- ✅ `RouteRegistry` 可从配置加载路由
- ✅ `find_route()` 通过单元测试

**时间估算**: 1 小时

#### 任务 4.2.2: 更新 UIRouterSkill.execute() 方法

**文件**: `src/skills/ui_router_skill.py`

**修改 `execute()` 方法**:
```python
def execute(self, state: AgentState, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行 UI 路由操作"""
    action = params.get("action")
    
    if action == "navigate_to_page":
        page_name = params.get("page_name", "")
        
        # 使用新的路由匹配逻辑
        route_info = route_registry.find_route(page_name)
        
        if "error" in route_info:
            return {"error": route_info["error"]}
        
        # 处理受限页面
        if route_info["is_restricted"]:
            return {
                "ui_action": {
                    "type": "navigate",
                    "payload": {"path": route_info["path"]}
                },
                "message": f"正在打开【{route_info['name']}】，{route_info['restriction_reason']}"
            }
        
        # 正常导航
        return {
            "ui_action": {
                "type": "navigate",
                "payload": {"path": route_info["path"]}
            },
            "message": f"正在打开【{route_info['name']}】页面"
        }
```

**验收标准**:
- ✅ 移除对 `_TOOL_ROUTE_MAP` 的引用
- ✅ 使用 `route_registry.find_route()` 替代硬编码查询
- ✅ 受限页面返回友好提示信息

**时间估算**: 0.5 小时

### 4.3 Phase 3: 单元测试 (优先级: P0)

#### 任务 4.3.1: 编写路由匹配测试

**文件**: `src/tests/test_ui_router_skill.py`

**测试用例**:
```python
import pytest
from src.skills.ui_router_skill import RouteRegistry

class TestRouteRegistry:
    
    def test_exact_match(self):
        """测试精确匹配"""
        registry = RouteRegistry()
        result = registry.find_route("能源监控总览")
        assert result["path"] == "/integrated-monitor/energy-monitor"
        assert result["is_restricted"] is False
    
    def test_fuzzy_match(self):
        """测试模糊匹配"""
        registry = RouteRegistry()
        result = registry.find_route("能源监控")
        assert result["path"] == "/integrated-monitor/energy-monitor"
    
    def test_restricted_page(self):
        """测试受限页面"""
        registry = RouteRegistry()
        result = registry.find_route("负荷预测")
        assert result["is_restricted"] is True
        assert "需要选择项目" in result["restriction_reason"]
    
    def test_no_match(self):
        """测试无匹配结果"""
        registry = RouteRegistry()
        result = registry.find_route("不存在的页面XYZ")
        assert "error" in result
```

**验收标准**:
- ✅ 所有测试用例通过 (`pytest src/tests/test_ui_router_skill.py -v`)
- ✅ 覆盖精确匹配、模糊匹配、受限页面、无匹配 4 种场景

**时间估算**: 1 小时

### 4.4 Phase 4: 集成测试 (优先级: P1)

#### 任务 4.4.1: 端到端测试场景

**测试环境**: 本地开发环境 + 前端运行

**测试用例**:

| 场景 | 用户输入 | 期望行为 | 验证点 |
|------|---------|---------|--------|
| TC-001 | "打开能源监控页面" | 导航至 `/integrated-monitor/energy-monitor` | ✅ 页面正确加载 |
| TC-002 | "查看工单列表" | 导航至 `/operation/work-order-list` | ✅ 页面正确加载 |
| TC-003 | "打开负荷预测" | 导航至 `/analysis/load-forecast` + 提示受限 | ✅ 显示权限提示 |
| TC-004 | "能源分析" | 模糊匹配至 `/analysis/consumption-panel` | ✅ 模糊匹配成功 |
| TC-005 | "打开不存在的页面" | 返回错误提示 | ✅ 友好错误信息 |

**验收标准**:
- ✅ 所有 5 个测试场景通过
- ✅ 前端 `useAgentSSE.ts` 正确处理 `navigate` 类型的 UIAction
- ✅ 无 404 错误或路由异常

**时间估算**: 1.5 小时

---

## 5. 验证计划 (Verification Plan)

### 5.1 验收标准矩阵

| 验收项 | 标准 | 验证方法 | 负责人 |
|--------|------|----------|--------|
| **功能完整性** | 24个可访问路由全部可用 | 手动测试 + 自动化测试 | 开发者 |
| **准确性** | 路由匹配准确率 ≥ 95% | 批量测试50个不同表述 | 测试者 |
| **容错性** | 无匹配时返回友好提示 | 边界测试 | 开发者 |
| **性能** | 路由匹配耗时 < 100ms | 性能基准测试 | 开发者 |
| **兼容性** | 不破坏现有前端 SSE 逻辑 | 回归测试 | 测试者 |

### 5.2 测试数据集

**准备50个测试用例**，覆盖：
- **精确表述**: "能源监控总览"、"工单列表"（10个）
- **简化表述**: "能源监控"、"工单"（10个）
- **口语化表述**: "看一下能耗"、"查工单"（10个）
- **错别字/近似词**: "能原监控"、"功单列表"（10个）
- **无匹配**: "不存在的页面"、"XYZ"（10个）

**验收标准**:
- 前40个应正确匹配（准确率 80%）
- 后10个应返回友好错误提示

---

## 6. 风险缓解与回滚策略 (Risk Mitigation & Rollback)

### 6.1 风险识别

| 风险编号 | 风险描述 | 影响程度 | 概率 | 缓解措施 |
|---------|---------|---------|------|---------|
| **R-001** | 路由表维护不及时，前端更新后 Agent 不同步 | 高 | 中 | 在 `routes.yaml` 顶部注明同步日期，建立定期审计机制 |
| **R-002** | 模糊匹配算法误匹配 | 中 | 低 | 设置相似度阈值 0.6，低于阈值返回候选列表供用户选择 |
| **R-003** | LLM 理解偏差，传入错误的 `page_name` | 中 | 中 | 在 Prompt 中增加示例，提升 LLM 意图理解准确性 |
| **R-004** | 受限页面处理不当，用户体验差 | 低 | 低 | 返回清晰提示信息 + 建议操作步骤 |

### 6.2 回滚预案

**触发条件**:
- 修复后导航成功率 < 80%
- 出现系统级错误（如配置加载失败）
- 前端出现大量 404 错误

**回滚步骤**:
1. **保留备份**: 修改前对以下文件打 tag：
   ```bash
   git tag backup-before-route-fix
   git push origin backup-before-route-fix
   ```

2. **快速回滚**:
   ```bash
   git revert <commit-hash>  # 回滚相关 commits
   git push origin main
   ```

3. **验证回滚**: 运行集成测试确认原功能恢复

---

## 7. 时间线与资源分配 (Timeline & Resources)

### 7.1 总体时间估算

| 阶段 | 任务数 | 预计耗时 | 累计耗时 | 优先级 |
|------|--------|---------|---------|--------|
| Phase 1: 路由注册表构建 | 2 | 2.0h | 2.0h | P0 |
| Phase 2: 代码重构 | 2 | 1.5h | 3.5h | P0 |
| Phase 3: 单元测试 | 1 | 1.0h | 4.5h | P0 |
| Phase 4: 集成测试 | 1 | 1.5h | 6.0h | P1 |
| **总计** | **6** | **6.0h** | - | - |

### 7.2 里程碑节点

```
Day 1 (前2小时):
├─ 创建 config/routes.yaml
├─ 集成到 prompts.yaml
└─ Milestone: 路由表可加载 ✓

Day 1 (后2小时):
├─ 重构 ui_router_skill.py
├─ 实现 RouteRegistry 类
└─ Milestone: 代码重构完成 ✓

Day 2 (前2小时):
├─ 编写单元测试
├─ 执行集成测试
└─ Milestone: 所有测试通过 ✓

Day 2 (后续):
├─ Code Review
├─ 提交合并到 main
└─ Milestone: 功能上线 ✓
```

### 7.3 资源需求

- **开发者**: 1人，具备 Python/LangGraph/YAML 经验
- **测试者**: 0.5人，熟悉前端路由机制
- **环境**: 本地开发环境 + 前端运行环境
- **依赖**: 无外部依赖，纯内部重构

---

## 8. Git 提交策略 (Commit Strategy)

### 8.1 分支策略

```bash
# 从 main 创建功能分支
git checkout main
git pull origin main
git checkout -b fix/navigation-routes
```

### 8.2 提交拆分

**遵循 CLAUDE.md 规范**，每个 Phase 独立提交：

| Commit | 标签 | 描述 | 文件变更 |
|--------|------|------|---------|
| #1 | `[config]` | 新增真实路由注册表 | `config/routes.yaml` (新建) |
| #2 | `[config]` | 集成路由表到 prompts.yaml | `src/config/prompts.yaml` |
| #3 | `[refactor]` | ui_router_skill 重构：移除硬编码路由映射 | `src/skills/ui_router_skill.py` |
| #4 | `[test]` | 新增路由匹配单元测试 | `src/tests/test_ui_router_skill.py` |
| #5 | `[docs]` | 更新 AI_CONTEXT.md 变更日志 | `AI_CONTEXT.md` |

**Commit Message 示例**:
```
[config] 新增真实路由注册表：24个可访问路由 + 10个受限路由

- 从 docs/analysis_nav_routes.md 提取真实前端路由
- 支持多关键词模糊匹配
- 标记受限页面及限制原因
```

### 8.3 推送与合并

```bash
# 逐个 commit 后推送
git add config/routes.yaml
git commit -m "[config] 新增真实路由注册表：24个可访问路由 + 10个受限路由"

git add src/config/prompts.yaml
git commit -m "[config] 集成路由表到 prompts.yaml"

# ... 其余提交

# 推送到远程
git push origin fix/navigation-routes

# 本地测试通过后合并到 main（或发起 PR）
git checkout main
git merge fix/navigation-routes
git push origin main
```

---

## 9. 总结与下一步行动 (Conclusion & Next Steps)

### 9.1 本计划解决的问题

本实施计划通过**配置驱动**的方式，彻底解决了当前 Agent 页面导航功能的三大核心缺陷：

✅ **DEF-001**: 替换虚假路由为真实前端路由（24个可访问路由）  
✅ **DEF-002**: 移除硬编码映射逻辑，改为从 YAML 配置加载  
✅ **DEF-003**: 支持多级嵌套路由结构（`/category/page`）  

### 9.2 遗留问题与中期规划

本计划**未解决**的问题（留待后续迭代）：

🔶 **DEF-004**: 受限页面权限感知（当前仅提供文字提示）  
🔶 **DEF-005**: 路由表版本同步机制（当前需手动更新 `routes.yaml`）  

**中期改进方向**:
- **Phase 2** (3周后): 建立 `/api/agent/routes` 端点，Agent 启动时动态获取路由表
- **Phase 3** (2个月后): 前端在 `page_context` 中注入路由表，实现零配置同步

### 9.3 成功标准

修复完成后，应达到以下效果：

1. **用户说"打开能源监控"** → Agent 正确导航至 `/integrated-monitor/energy-monitor`
2. **用户说"查看工单"** → Agent 正确导航至 `/operation/work-order-list`
3. **用户说"负荷预测"** → Agent 导航成功 + 提示需要项目上下文
4. **单元测试覆盖率** ≥ 90%，所有测试用例通过
5. **端到端测试** 通过率 100%（5/5 场景）

### 9.4 下一步行动

1. **立即执行**: 按照 §4 实施阶段逐步完成代码修改
2. **Code Review**: 提交前由团队成员审查路由表完整性
3. **更新文档**: 完成后更新 `AI_CONTEXT.md` §6 变更日志
4. **知识沉淀**: 将路由维护流程写入团队文档

---

**文档状态**: ✅ 完成  
**预计实施时间**: 6 小时（1.5 工作日）  
**风险等级**: 低（纯重构，无新功能，可快速回滚）

