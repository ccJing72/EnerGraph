"""模拟真实客户多种问法测试

验证 Agent 对不同表述的理解能力
"""
import requests
import json

# 真实客户可能的各种问法
test_cases = [
    {
        "name": "直接询问用电量",
        "input": "今天江北工厂的用电量是多少？",
    },
    {
        "name": "口语化表述",
        "input": "今天用了多少电？",
    },
    {
        "name": "能耗查询",
        "input": "帮我查一下今天的能耗情况",
    },
    {
        "name": "数据查看请求",
        "input": "我想看看今天的电量数据",
    },
]

def test_customer_query(user_input: str, test_name: str):
    """测试单个客户询问"""
    url = "http://localhost:8000/stream"

    payload = {
        "user_input": user_input,
        "page_context": {
            "current_route": "/index/index",
            "site_id": "FJJB000001"
        }
    }

    print(f"\n{'='*70}")
    print(f"测试场景: {test_name}")
    print(f"客户询问: {user_input}")
    print(f"{'='*70}\n")

    response = requests.post(url, json=payload, stream=True, timeout=60)

    found_action = False
    action_data = None

    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')

        if line.startswith('event:'):
            event_type = line.split(':', 1)[1].strip()
        elif line.startswith('data:'):
            data_str = line.split(':', 1)[1].strip()
            data = json.loads(data_str)

            if event_type == 'action':
                found_action = True
                action_data = data
                print(f"✅ 触发跳转:")
                print(f"   目标页面: {data['route']}")
                print(f"   携带参数: {data['params']}")
                break
            elif event_type == 'done':
                break

    if not found_action:
        print("❌ 未触发跳转")
        return False

    # 验证跳转是否正确
    expected_route = "/analysis/consumption-panel"
    if action_data['route'] == expected_route:
        print(f"✅ 跳转路由正确: {expected_route}")
        return True
    else:
        print(f"❌ 跳转路由错误: 期望 {expected_route}, 实际 {action_data['route']}")
        return False

if __name__ == "__main__":
    print("\n🚀 开始真实客户场景测试")
    print(f"共 {len(test_cases)} 个测试场景\n")

    results = []

    for test in test_cases:
        success = test_customer_query(test["input"], test["name"])
        results.append({
            "name": test["name"],
            "success": success
        })

    # 统计结果
    print(f"\n{'='*70}")
    print("📊 测试结果汇总:")
    print(f"{'='*70}\n")

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    for r in results:
        status = "✅ 通过" if r["success"] else "❌ 失败"
        print(f"{status} - {r['name']}")

    print(f"\n通过率: {passed}/{total} ({passed*100//total}%)")

    if passed == total:
        print("\n🎉 所有场景测试通过！Agent 理解能力良好。")
    else:
        print(f"\n⚠️ {total - passed} 个场景失败，需要优化。")
