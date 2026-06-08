"""测试福加 API 接口调用

运行方式：python test_fuca_api.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.java_backend import fetch_energy_summary
from datetime import datetime
import json

def test_energy_api():
    """测试能耗查询接口"""
    site_id = "FJJB000001"
    date = datetime.now().strftime("%Y-%m-%d")

    print(f"🔍 测试福加 API - 能耗查询")
    print(f"   站点: {site_id}")
    print(f"   日期: {date}")
    print("-" * 60)

    result = fetch_energy_summary(site_id=site_id, date=date)

    if "error" in result:
        print(f"❌ 调用失败: {result['error']}")
        return False

    print("✅ 调用成功！返回数据：")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return True

if __name__ == "__main__":
    success = test_energy_api()
    sys.exit(0 if success else 1)
