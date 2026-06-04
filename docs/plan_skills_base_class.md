# EnerGraph — Skills 基础设施升级方案（BaseSkill 基类 + 生命周期管理）

**目标**: 引入 `BaseSkill` 抽象基类，统一所有 Skill 的接口契约、生命周期钩子和错误处理，为 Phase 3-6 的 Skill 扩展奠定工程基础。  
**前置条件**: Phase 2 完成（Skills 骨架已建立）  
**完成标志**: 现有 4 个 Skill 均继承 BaseSkill，`v3_engine_router` 通过统一接口调度 Skill，不依赖具体子类实现  
**执行时机**: 可在 Phase 3 之前或与其他 Phase 并行执行（1-2 个 session 完成）

---

## 行业背景与设计动机

根据 2026 年 AI Agent 行业实践（Anthropic / Microsoft / LangChain），Skill 架构的核心原则是：

```
Agent = Identity + Memory + Judgment
Skill = Procedure + Tools + Context（HOW）
Tool  = Atomic Function（最小能力单元）
```

- **Skill 是"怎么做"**，Agent 是"谁来做 + 何时做"
- Skill 应模块化、可组合、按需加载（Progressive Disclosure）
- 每个 Skill 继承统一基类，标准化 I/O 和错误处理，降低 Agent 规划负担

本项目的 Skill 当前是"薄包装"（仅含 name/tools/prompt_keys + 少量静态方法），缺少统一接口。随着 Phase 3-6 扩展，Skill 逻辑将膨胀，需要提前建立基类约束。

---

## BaseSkill 接口设计

```python
# src/skills/base_skill.py

class BaseSkill(ABC):
    """所有 Skill 的抽象基类。
    
    强制每个 Skill 声明：
    - 元信息（name / tools / prompt_keys / description）
    - execute() 方法（Skill 核心编排逻辑）
    - 可选生命周期钩子（before_execute / after_execute）
    
    v3_engine_router 只依赖 BaseSkill 接口调度，不感知具体子类。
    """
    
    # ── 元信息（子类必须声明）────────────────────────────
    name: str
    tools: List[str]
    prompt_keys: List[str]
    description: str
    
    # ── 核心方法 ─────────────────────────────────────────
    @abstractmethod
    def execute(
        self,
        tool_results: List[Tuple[str, Dict, Dict]],
        state: AgentState,
    ) -> Dict[str, Any]:
        """Skill 编排逻辑：接收工具调用结果 + 当前状态，返回状态更新。
        
        Args:
            tool_results: [(tool_name, result_dict, args_dict), ...]
            state: 当前 AgentState
            
        Returns:
            AgentState 更新字典（如 pending_actions / pending_data_cards / context 等）
        """
    
    # ── 生命周期钩子（可选覆盖）────────────────────────
    def before_execute(self, state: AgentState) -> AgentState:
        """执行前预处理（如参数归一化、上下文注入）。默认无操作。"""
        return state
    
    def after_execute(self, state: AgentState, updates: Dict) -> Dict:
        """执行后清理/审计（如日志、指标上报）。默认无操作。"""
        return updates
    
    # ── 工具集辅助 ─────────────────────────────────────
    def has_tool(self, tool_name: str) -> bool:
        """判断某工具是否属于本 Skill。"""
        return tool_name in self.tools
```

---

## 子任务（每个子任务 = 一个 commit）

### T1: 新建 BaseSkill 基类 + 注册表升级
- **文件**: `src/skills/base_skill.py`, `src/skills/__init__.py`
- **改动**:
  - 新建 `base_skill.py`，定义 `BaseSkill` ABC（含 execute / before_execute / after_execute / has_tool）
  - `__init__.py` 中 `SKILL_REGISTRY` 类型注解改为 `Dict[str, BaseSkill]`
  - 新增 `get_skill(name: str) -> BaseSkill` 工厂函数，替代直接 dict 访问
- **验收**: `python -c "from src.skills.base_skill import BaseSkill; print(BaseSkill.__abstractmethods__)"` 输出 `frozenset({'execute'})`

### T2: 迁移现有 Skill 到 BaseSkill
- **文件**: `src/skills/hvac_expert_skill.py`, `src/skills/energy_dispatch_skill.py`, `src/skills/ui_router_skill.py`, `src/skills/v3_interpreter_skill.py`
- **改动**:
  - 各 Skill 继承 `BaseSkill`，实现 `execute()` 方法
  - `UIRouterSkill.execute()` 封装 `infer_navigation()` 调用
  - 其余 Skill 的 `execute()` 暂为骨架（返回空 updates），等各自 Phase 完善
- **验收**: `python -c "from src.skills import SKILL_REGISTRY; print([s.name for s in SKILL_REGISTRY.values()])"` 无报错

### T3: v3_engine_router 统一调度接口
- **文件**: `src/graph/nodes.py`
- **改动**:
  - `v3_engine_router_node` 改为通过 `BaseSkill.execute()` 统一调度
  - 调用链：`skill.before_execute(state)` → `skill.execute(tool_results, state)` → `skill.after_execute(state, updates)`
  - 不依赖具体子类，只依赖 `BaseSkill` 接口
- **验收**: 现有 pytest 测试通过，`graph.invoke({"user_input": "..."})` 无报错

### T4: Skill 单元测试（基类契约）
- **文件**: `src/tests/test_base_skill.py`
- **改动**:
  - 测试 BaseSkill 不可直接实例化（abstract）
  - 测试子类未实现 execute() 时 TypeError
  - 测试 before/after_execute 钩子调用顺序
  - 测试 get_skill() 工厂函数
- **验收**: `pytest src/tests/test_base_skill.py` 全部通过

---

## 关键架构决策

**为什么引入 BaseSkill 而非继续用 dict 注册？**  
Phase 3-6 每个 Skill 都会有 execute 逻辑（RAG 拒答 / 数据导出 / 语音编排），统一基类强制接口契约，防止各 Phase 开发者各自为政。v3_engine_router 只需面向 BaseSkill 编程，降低节点复杂度。

**为什么 before/after 钩子而非装饰器？**  
钩子模式更符合 LangGraph 状态机的纯函数风格，且易于测试。装饰器在 async 场景下易引入复杂度。

**与 plan_skills_refactor.md 的关系**：  
本方案是 `plan_skills_refactor.md` 的工程升级，不替代它。Skills 目录结构和分工原则不变，只是每个 Skill 增加基类约束。

---

## 关键文件
- `src/skills/base_skill.py` — BaseSkill 抽象基类
- `src/skills/__init__.py` — 注册表升级 + 工厂函数
- `src/graph/nodes.py` — 统一调度接口
- `src/tests/test_base_skill.py` — 基类契约测试

## Skills 融合说明
- 本方案完成后，Phase 3-6 新建或完善的 Skill 均须继承 BaseSkill
- 已有 Skill 迁移为 BaseSkill 子类，现有行为不变（向后兼容）
- 详见 `docs/plan_skills_refactor.md`
