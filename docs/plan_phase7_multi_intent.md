# EnerGraph — Phase 7: 多意图识别与拆分执行

**目标**: 让 Agent 能够识别单条用户输入中的多个意图，拆分后依次执行各意图对应的工具链，最终生成结构化分段报告。  
**前置条件**: Phase 2 完成（ReAct 循环 + Skill 体系可用）  
**可并行**: 本 Phase 不依赖 Phase 3/4/5/6，可与任意 Phase 并行执行；建议在 Skills 基类之后  
**完成标志**: 用户输入含多个意图时（如"查 COP，导出近十天能耗，看看有没有报警"），Agent 依次执行全部意图并输出分段报告

---

## 业务场景

### 场景 1: 双意图输入
用户问："冷水机房 COP 多少？另外帮我查一下今天的能耗汇总。"

Agent 应：
1. cognitive_parser 识别出 2 个意图：① COP 查询 ② 能耗查询
2. 第 1 轮 ReAct：调用 `fetch_cop_data` + `navigate_to_page("/chiller-room")`
3. 第 2 轮 ReAct：调用 `fetch_energy_summary` + `navigate_to_page("/energy-monitor")`
4. interpreter_generator 生成分段报告：
   ```
   ## 1. 冷水机房 COP
   冷水机房#1 瞬时 COP 为 6.90...
   
   ## 2. 今日能耗汇总
   SH-01 今日总用电 11,200 kWh...
   ```

### 场景 2: 三意图复合输入
用户问："查一下冷水机房的 COP，然后帮我导出近十天的能耗数据，顺便看看有没有报警。"

Agent 应：
1. 识别 3 个意图：① COP 查询 ② 多日能耗导出 ③ 报警查询
2. 依次执行 3 轮工具调用
3. 生成 3 段结构化报告，含数据卡片（DataCard）

### 场景 3: 意图间有依赖
用户问："先查一下光伏发电预测，然后告诉我根据预测应该怎么调整排产计划。"

Agent 应：
1. 识别 2 个意图：① 光伏预测（数据获取）② 排产建议（基于①的结果推理）
2. 第 1 轮：调用 `query_timedit_forecast`
3. 第 2 轮：基于预测数据调用 `parse_business_intent`（意图②依赖①的结果）
4. 报告中标注依赖关系

---

## 现有架构分析

当前 ReAct 循环**已具备多工具调用能力**：

```
cognitive_parser → LLM 输出多个 tool_calls → v3_engine_router 并行执行
→ 返回结果 → cognitive_parser（循环）→ 可继续调用更多工具
→ 最终无 tool_calls → interpreter_generator 生成报告
```

**问题不在执行层，而在识别层和报告层**：
1. `cognitive_parser` 的 Prompt 没有引导 LLM 显式拆分多意图，容易遗漏次要意图
2. `interpreter_generator` 没有分段输出的指引，多意图结果混在一起
3. 前端无法区分"哪些数据对应哪个意图"

---

## 新增文件

| 文件 | 职责 |
|------|------|
| `src/tests/test_multi_intent.py` | 多意图识别与拆分执行测试 |

---

## 修改文件

| 文件 | 改动 |
|------|------|
| `src/config/prompts.yaml` | `cognitive_parser` 新增多意图拆分指令；`interpreter_generator` 新增分段报告格式 |
| `src/graph/state.py` | 新增 `intent_plan: Optional[List[IntentItem]]`（意图执行计划） |
| `src/graph/nodes.py` | `cognitive_parser_node` 解析意图计划；`interpreter_generator_node` 支持分段报告 |
| `src/schemas/v3_engine.py` | 新增 `IntentItem` Pydantic 模型 |
| `src/services/api.py` | SSE 新增 `event: intent_plan` 事件（可选，通知前端当前执行计划） |

---

## 子任务（每个子任务 = 一个 commit）

### T1: 意图数据模型 + AgentState 扩展
- **文件**: `src/schemas/v3_engine.py`, `src/graph/state.py`
- **改动**:
  - `v3_engine.py` 新增 `IntentItem` 模型：
    ```python
    class IntentItem(BaseModel):
        """单条用户意图。"""
        id: int = Field(..., description="意图序号（从 1 开始）")
        description: str = Field(..., description="意图描述")
        category: str = Field(default="general", description="意图类别：hvac / monitor / energy / alarm / export / general")
        depends_on: List[int] = Field(default_factory=list, description="依赖的意图 ID 列表")
        status: str = Field(default="pending", description="执行状态：pending / running / done / failed")
    ```
  - `state.py` 新增字段：
    ```python
    intent_plan: Optional[List[IntentItem]]  # 多意图执行计划
    ```
- **验收**: `python -c "from src.schemas.v3_engine import IntentItem; print(IntentItem(id=1, description='COP查询'))"` 无报错

### T2: cognitive_parser Prompt 增强（核心）
- **文件**: `src/config/prompts.yaml`
- **改动**:
  - 在 `cognitive_parser.system` 末尾追加多意图识别指令：
    ```
    ## 多意图识别

    当用户输入包含多个独立请求时，你必须：
    1. 识别所有意图，按执行优先级排列
    2. 判断意图间是否有数据依赖（如"先查预测，再给建议"）
    3. 对无依赖的意图，可在同一轮调用多个工具并行执行
    4. 对有依赖的意图，等前置意图的工具返回后再调用后续工具
    5. 每个意图至少调用一个相关工具，不要遗漏

    示例输入："查一下 COP，顺便看看今天能耗"
    → 意图 1：COP 查询 → 调用 fetch_cop_data
    → 意图 2：能耗查询 → 调用 fetch_energy_summary
    → 两者无依赖，可在同一轮并行调用
    ```
  - **注意**：此改动必须以 `[config]` 标签单独 commit
- **验收**: LLM 对多意图输入能输出多组 tool_calls

### T3: interpreter_generator 分段报告
- **文件**: `src/config/prompts.yaml`, `src/graph/nodes.py`
- **改动**:
  - `prompts.yaml` 中 `interpreter_generator.system` 追加分段报告指令：
    ```
    ## 多意图分段报告

    若本轮处理了多个用户意图，请按以下格式输出分段报告：

    ## 1. [意图 1 标题]
    [意图 1 的详细回答]

    ## 2. [意图 2 标题]
    [意图 2 的详细回答]

    ---
    **小结**：[一段话综合所有意图的结论]

    每个段落独立完整，不要因为分段而省略技术细节。
    ```
  - `interpreter_generator_node` 中，若 `state` 有 `intent_plan`，将其注入 system prompt：
    ```python
    if state.get("intent_plan"):
        intent_summary = "\n".join(
            f"- 意图 {i.id}: {i.description} ({i.status})"
            for i in state["intent_plan"]
        )
        system_content += f"\n\n## 本次处理的用户意图\n{intent_summary}"
    ```
- **验收**: 多意图输入产生的报告有清晰的 `## 1.` / `## 2.` 分段

### T4: SSE intent_plan 事件（可选增强）
- **文件**: `src/services/api.py`
- **改动**:
  - SSE 新增 `event: intent_plan`：在 cognitive_parser 识别出多意图后推送
    ```json
    {
      "intents": [
        {"id": 1, "description": "COP 查询", "category": "monitor"},
        {"id": 2, "description": "能耗导出", "category": "export"}
      ]
    }
    ```
  - 前端可据此展示"正在处理意图 1/3..."进度指示
- **验收**: curl 测试多意图输入可见 `event: intent_plan`

### T5: 测试
- **文件**: `src/tests/test_multi_intent.py`
- **改动**:
  - 测试 IntentItem 模型序列化
  - 测试 cognitive_parser Prompt 包含多意图指令
  - Mock LLM 返回多 tool_calls，验证 v3_engine_router 全部执行
  - 测试 interpreter_generator 输出含 `## 1.` / `## 2.` 分段
  - 测试意图依赖：`depends_on` 字段正确传递
- **验收**: `pytest src/tests/test_multi_intent.py` 全部通过

---

## 关键架构决策

**为什么不新建 intent_decomposer 节点？**  
当前 ReAct 循环已支持多轮工具调用，LLM 本身具备多意图识别能力。问题在于 Prompt 未引导 LLM 显式拆分，导致次要意图被遗漏。通过增强 Prompt（T2）即可解决，无需引入额外节点增加图的复杂度。新增节点还会破坏 `max_iterations` 计数逻辑。

**为什么意图计划放在 AgentState 而非独立队列？**  
与 `pending_actions` 设计原则一致——保持图的可序列化性，支持 LangGraph checkpointer。intent_plan 随状态流转，每个节点可读取当前进度。

**为什么分段报告用 Markdown ## 而非 JSON？**  
Markdown 分段对 LLM 最自然，不需要额外的 JSON schema 约束。前端可通过正则 `## \d+\.` 解析段落标题，用于目录导航或折叠展示。

**与多意图并行执行的关系**：  
无依赖意图可在同一轮 ReAct 中并行调用多个工具（当前 `v3_engine_router_node` 已支持遍历所有 `tool_calls`）。有依赖意图需等前置工具返回后在下一轮调用。这是 ReAct 循环的自然行为，无需额外并行机制。

**与 BaseSkill 的关系**:  
多意图识别在 Graph 节点层完成，不改变 Skill 的 execute() 接口。各 Skill 只需处理传入的 tool_results，不感知"这是第几个意图"。

---

## 关键文件
- `src/config/prompts.yaml` — cognitive_parser 多意图指令 + interpreter_generator 分段报告
- `src/schemas/v3_engine.py` — IntentItem 模型
- `src/graph/state.py` — intent_plan 字段
- `src/graph/nodes.py` — 意图计划注入 + 分段报告生成

## Skills 融合说明
- 多意图识别在 Graph 节点层，Skill 不感知意图拆分
- `v3_engine_router_node` 执行完工具后，照常调用各 Skill 的 `execute()`
- 详见 `docs/plan_skills_refactor.md`
