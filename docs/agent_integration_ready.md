# Agent 真实 API 接入完成 - 前端对接指南

## ✅ 已完成功能

### 1. 真实数据查询
- **接口**：https://aiot-fuca.com/analysisWeb/energyAnalysis/v1/ECInfo
- **场景**：能耗/用电量查询
- **数据来源**：福加真实 API（已验证返回 2517.4 kWh）

### 2. 自动跳转推送
- **目标页面**：`/analysis/consumption-panel`
- **携带参数**：`site_id` + `date`
- **推送方式**：SSE `event: action`

### 3. 多种问法支持
✅ "今天江北工厂的用电量是多少？"
✅ "今天用了多少电？"
✅ "帮我查一下今天的能耗情况"
✅ "我想看看今天的电量数据"

---

## 📊 完整流程

```
用户输入
  ↓
Agent LLM 理解意图
  ↓
决策调用 fetch_energy_summary(site_id, date)
  ↓
工具函数 POST 到福加 API
  ↓
解析响应 totalEnergy: 2517.4
  ↓
生成 Markdown 报告
  ↓
推送跳转指令 (SSE event: action)
  ↓
前端 router.push()
```

---

## 🔌 前端对接步骤

### 第一步：发送请求

```javascript
const eventSource = new EventSource('/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_input: "今天用电量是多少？",
    page_context: {
      current_route: this.$route.path,  // 当前路由
      site_id: this.$store.state.currentSiteId  // 当前站点ID
    }
  })
});
```

### 第二步：监听 SSE 事件

```javascript
// 流式文本
eventSource.addEventListener('text', (e) => {
  const data = JSON.parse(e.data);
  this.agentReply += data.text;  // 逐字显示
});

// 跳转指令
eventSource.addEventListener('action', (e) => {
  const action = JSON.parse(e.data);
  // action = {type: "navigate", route: "/analysis/consumption-panel", params: {...}}
  
  this.$router.push({
    path: action.route,
    query: action.params
  });
});

// 完成
eventSource.addEventListener('done', () => {
  eventSource.close();
});
```

---

## 🧪 验证方法

### 命令行测试
```bash
curl -X POST http://localhost:8000/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "今天用电量是多少？",
    "page_context": {
      "current_route": "/index/index",
      "site_id": "FJJB000001"
    }
  }'
```

### 预期响应
```
event: text
data: {"text": "好的，我先查询..."}

event: action
data: {"type": "navigate", "route": "/analysis/consumption-panel", "params": {"site_id": "FJJB000001", "date": "2026-06-08"}}

event: done
```

---

## 📝 注意事项

1. **API 凭证**：服务器需配置 `.env` 中的 `FUCA_API_TOKEN`
2. **站点ID**：前端必须传递 `page_context.site_id`
3. **日期格式**：系统自动注入当前日期（YYYY-MM-DD）
4. **跳转时机**：Agent 会在返回数据后自动推送跳转指令

---

## 🚀 部署清单

- [x] 代码提交到 git
- [x] 测试脚本验证通过
- [x] Streamlit 演示前端可用
- [ ] 服务器部署（参考 docs/deploy_real_api.md）
- [ ] 福加网页集成 Agent 对话框
- [ ] 前端实现 SSE 事件监听

---

**当前状态**：✅ 后端完全就绪，等待前端集成
