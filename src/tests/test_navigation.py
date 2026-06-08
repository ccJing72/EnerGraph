import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.graph.builder import graph

# 测试能耗查询是否生成跳转
result = graph.invoke({
    "user_input": "今天江北工厂的用电量是多少？",
    "page_context": {
        "current_route": "/index/index",
        "site_id": "FJJB000001",
    }
})

print("\n=== AgentState 返回结果 ===")
print(f"pending_actions: {result.get('pending_actions')}")
print(f"final_report 长度: {len(result.get('final_report', ''))}")

if result.get("pending_actions"):
    print("\n✅ 生成了跳转动作:")
    for action in result["pending_actions"]:
        print(f"  类型: {action.type if hasattr(action, 'type') else action.get('type')}")
        print(f"  路由: {action.route if hasattr(action, 'route') else action.get('route')}")
        print(f"  参数: {action.params if hasattr(action, 'params') else action.get('params')}")
else:
    print("\n❌ 没有生成跳转动作")
