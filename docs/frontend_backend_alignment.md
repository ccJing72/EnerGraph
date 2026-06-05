# Agent 导航功能前后端对接文档

**文档版本**: v1.0  
**创建日期**: 2026-06-05  
**对接目的**: 确保 Agent 导航路由与前端实际路由、后端数据接口完全对齐

---

## 一、与前端团队对接

### 1.1 路由表校验（必需）

**对接目标**: 校验 Agent 维护的 24 个可访问路由 + 10 个受限路由是否与前端实际路由一致

**需要前端提供**:

```
1. Vue Router 配置文件导出
   - 文件路径：src/router/index.ts（或类似）
   - 格式：JSON 或 TypeScript 路由配置
   - 示例：
     {
       path: '/integrated-monitor/energy-monitor',
       name: 'EnergyMonitor',
       component: () => import('@/views/monitor/EnergyMonitor.vue'),
       meta: { requiresAuth: true, requiresProject: false }
     }

2. 路由权限元数据
   - 哪些路由需要登录（requiresAuth）
   - 哪些路由需要选择项目（requiresProject）
   - 哪些路由需要特定角色（roles: ['admin', 'operator']）
```

**对接方式**:
- 前端提供 `router-export.json`（可用脚本自动生成）
- 或提供在线文档（如 Confluence/飞书文档）

**Agent 团队责任**:
- 比对 `config/routes.yaml` 与前端提供的路由表
- 修正路径差异（如 `/energy-monitor` 实际是 `/integrated-monitor/energy-monitor`）
- 标记受限路由及其限制条件

---

### 1.2 路由参数规范（必需）

**对接目标**: 了解每个路由需要哪些参数（query params / path params）

**需要前端提供**:

```
路由参数清单（按路由分组）：

/integrated-monitor/energy-monitor
  - query params: 
      site_id: string (必填，站点ID)
      date_range: string (可选，日期范围 YYYY-MM-DD~YYYY-MM-DD)
  - path params: 无

/smart-maintenance/equipment-operation
  - query params:
      site_id: string (必填)
      device_id: string (可选，设备ID，不传则显示设备列表)
  - path params: 无

/analysis/consumption-panel
  - query params:
      site_id: string (必填)
      time_range: 'day' | 'month' | 'year' (可选，默认 day)
  - path params: 无

... (所有 24 个路由)
```

**对接方式**:
- 前端提供 Markdown 表格或 JSON 文件
- 或在 Swagger 文档中标注前端路由参数

**Agent 团队责任**:
- 在 `config/routes.yaml` 中新增 `params` 字段
- UIRouterSkill 生成 UIAction 时自动填充必填参数（从 `page_context.site_id` 获取）

---

### 1.3 路由变更通知机制（推荐）

**对接目标**: 建立长期同步机制，前端更新路由后自动通知 Agent 团队

**需要前端提供**:

```
方案 A：Webhook 通知（推荐）
- 前端在 CI/CD 流程中检测路由变更
- 变更后调用 Agent 团队的 Webhook: POST /api/route-change-notify
- Body: { added: [...], modified: [...], removed: [...] }

方案 B：定期同步
- 每月前端导出一次 router-export.json
- 放到共享目录或发送给 Agent 团队

方案 C：API 端点（中期方案）
- 前端提供 GET /api/routes 端点
- 返回当前所有路由的元数据
- Agent 启动时调用该端点获取最新路由表
```

**对接方式**:
- 双方技术负责人确定采用哪个方案
- Agent 团队提供接收接口（如选方案 A）

---

### 1.4 页面状态上下文（可选，但推荐）

**对接目标**: 了解页面之间的数据传递方式，优化 Agent 跳转体验

**需要前端提供**:

```
典型场景示例：

场景 1：从首页跳转到能源监控
  - 首页选中了"福加本厂"（site_id: FJ-01）
  - 跳转时需要保持 site_id 上下文
  - 期望：router.push({ path: '/integrated-monitor/energy-monitor', query: { site_id: 'FJ-01' } })

场景 2：从设备列表跳转到设备详情
  - 列表页选中了"冷水机组#1"（device_id: CH-01）
  - 跳转时需要传递 device_id
  - 期望：router.push({ path: '/smart-maintenance/equipment-operation', query: { site_id: 'FJ-01', device_id: 'CH-01' } })
```

**对接方式**:
- 前端提供 5-10 个典型跳转场景的示例代码
- Agent 团队在 UIRouterSkill 中实现相同的参数传递逻辑

---

## 二、与后端团队对接

### 2.1 监控数据接口清单（必需）

**对接目标**: 确认 Java 后端提供的所有监控数据接口，替换当前的 Mock 数据

**需要后端提供**:

```
接口清单（按功能分组）：

【设备监控类】
1. GET /api/cop/query
   - 功能：查询冷水机房 COP 数据
   - 请求参数：
       site_id: string (必填)
       time_range: string (可选，格式: YYYY-MM-DD~YYYY-MM-DD)
   - 响应示例：
     {
       "code": 0,
       "data": {
         "instant_cop": 6.90,
         "accumulated_cop": 7.20,
         "chiller_power": 121.5,
         "cooling_capacity": 837.4
       }
     }

2. GET /api/devices/status
   - 功能：查询设备运行状态
   - 请求参数：
       site_id: string
       device_type: 'chiller' | 'pump' | 'cooling_tower' (可选)
   - 响应示例：
     {
       "code": 0,
       "data": [
         { "device_id": "CH-01", "name": "冷水机组#1", "status": "running", "power": 121.5 }
       ]
     }

【能耗分析类】
3. GET /api/energy/summary
   - 功能：查询能耗汇总数据
   - 请求参数：...
   - 响应示例：...

【报警管理类】
4. GET /api/alarms/active
   - 功能：查询实时报警
   - 请求参数：...
   - 响应示例：...

... (列出所有接口)
```

**对接方式**:
- 后端提供 Swagger/OpenAPI 文档 URL
- 或提供 Postman Collection 导出文件
- 或提供接口文档 Markdown

**Agent 团队责任**:
- 在 `src/tools/java_backend.py` 中实现所有接口调用
- 移除 Mock 数据逻辑
- 添加错误处理和超时控制

---

### 2.2 接口鉴权方式（必需）

**对接目标**: 了解如何进行 API 鉴权，确保 Agent 能正常调用后端接口

**需要后端提供**:

```
鉴权方案（选择一种）：

方案 A：API Key
- Header: X-API-Key: <api_key>
- 后端提供专用 API Key（不要用生产环境的 Key）
- Agent 配置在 .env: JAVA_API_KEY=xxx

方案 B：JWT Token
- Header: Authorization: Bearer <jwt_token>
- 提供 Token 获取接口: POST /api/auth/token
- Agent 在启动时获取 Token，定期刷新

方案 C：服务间调用（内网）
- 无需鉴权，通过内网 IP 白名单控制
- Agent 服务器 IP 加入白名单
```

**对接方式**:
- 后端技术负责人提供鉴权方案说明
- 提供测试环境的凭证（API Key / 测试账号）

---

### 2.3 错误码规范（推荐）

**对接目标**: 了解接口错误码含义，Agent 能正确处理异常情况

**需要后端提供**:

```
错误码清单：

{
  0: "成功",
  1001: "参数错误",
  1002: "缺少必填参数",
  2001: "站点不存在",
  2002: "设备不存在",
  3001: "数据查询失败",
  3002: "数据库连接超时",
  4001: "无权限访问",
  4002: "Token 过期",
  5001: "内部服务器错误"
}
```

**对接方式**:
- 后端提供错误码文档
- Agent 团队在 `java_backend.py` 中实现错误码映射

---

### 2.4 测试环境与生产环境（必需）

**对接目标**: 获取测试环境和生产环境的接口地址

**需要后端提供**:

```
环境配置：

测试环境：
- Base URL: http://test-api.fuca.com
- 说明：可随意调用，数据为 Mock 数据或历史数据
- 凭证：API Key = test_xxx（或测试账号）

预生产环境（可选）：
- Base URL: http://pre-api.fuca.com
- 说明：接近真实数据，调用需谨慎
- 凭证：需申请

生产环境：
- Base URL: https://api.fuca.com
- 说明：真实数据，Agent 上线后使用
- 凭证：正式 API Key（需安全保管）
```

**Agent 团队责任**:
- 在 `.env` 中配置环境变量：
  ```
  JAVA_API_BASE_URL=http://test-api.fuca.com
  JAVA_API_KEY=test_xxx
  ```
- 开发阶段使用测试环境
- 上线前切换到生产环境

---

## 三、对接流程建议

### 3.1 对接会议安排

**第一次会议：需求宣讲（30分钟）**
- 参与方：Agent 团队 + 前端负责人 + 后端负责人
- 议题：
  1. Agent 导航功能演示（5分钟）
  2. 说明需要前后端提供的数据（10分钟）
  3. 讨论对接方案和时间节点（15分钟）

**第二次会议：技术对接（1小时）**
- 参与方：Agent 开发者 + 前端开发者 + 后端开发者
- 议题：
  1. 前端提供路由表和参数规范（20分钟）
  2. 后端提供接口文档和测试环境（20分钟）
  3. 现场联调测试（20分钟）

**第三次会议：验收测试（1小时）**
- 参与方：同上 + 测试人员
- 议题：
  1. 端到端测试演示（30分钟）
  2. 问题记录和修复计划（20分钟）
  3. 上线时间确认（10分钟）

---

### 3.2 对接资料交付清单

**前端团队需交付**:
- [ ] Vue Router 配置文件或路由表 JSON（`router-export.json`）
- [ ] 路由参数规范文档（Markdown 或 Excel）
- [ ] 受限路由权限说明文档
- [ ] 典型跳转场景示例代码（5-10个）

**后端团队需交付**:
- [ ] Swagger/OpenAPI 文档 URL 或 Postman Collection
- [ ] 测试环境地址和凭证（API Key 或测试账号）
- [ ] 错误码清单文档
- [ ] 接口响应示例（每个接口至少1个）

**Agent 团队需交付**:
- [ ] 路由修复实施计划（`docs/plan_fix_navigation_routes.md`）
- [ ] 前后端对接文档（本文档）
- [ ] 测试报告（单元测试 + 集成测试结果）
- [ ] 部署说明文档

---

## 四、快速对接清单（TL;DR）

### 最小可行对接（MVP）

**如果时间紧迫，至少需要这些**：

| 优先级 | 对接项 | 提供方 | 交付物 | 预计耗时 |
|--------|--------|--------|--------|---------|
| **P0** | 路由表校验 | 前端 | `router-export.json`（24个路由） | 30分钟 |
| **P0** | 路由参数规范 | 前端 | 参数清单 Markdown | 1小时 |
| **P0** | 后端接口文档 | 后端 | Swagger URL | 已有 |
| **P0** | 测试环境凭证 | 后端 | API Key 或测试账号 | 10分钟 |

**其余对接项可后续补充**。

---

## 五、对接时间线建议

```
Week 1: 准备阶段
  Day 1: Agent 团队发送对接需求邮件
  Day 2-3: 前后端团队准备资料
  Day 4: 第一次对接会议（需求宣讲）

Week 2: 技术对接
  Day 1: 第二次对接会议（技术对接）
  Day 2-4: Agent 团队实施修复
  Day 5: 第三次对接会议（验收测试）

Week 3: 上线部署
  Day 1-2: 修复遗留问题
  Day 3: 生产环境部署
  Day 4-5: 监控和优化
```

---

**文档状态**: ✅ 完成  
**维护责任**: Agent 团队  
**更新频率**: 每次前端路由变更或后端接口变更后更新

