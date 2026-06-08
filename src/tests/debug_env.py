import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.tools.java_backend import fetch_energy_summary, _is_mock

print(f"环境变量检查:")
print(f"  FUCA_API_BASE_URL = {os.getenv('FUCA_API_BASE_URL')}")
print(f"  FUCA_API_TOKEN = {os.getenv('FUCA_API_TOKEN')[:20]}..." if os.getenv('FUCA_API_TOKEN') else "  FUCA_API_TOKEN = None")
print(f"  _is_mock() = {_is_mock()}")
print()

result = fetch_energy_summary("FJJB000001", "2026-06-08")
print(f"工具调用结果:")
if "error" in result:
    print(f"  ❌ 错误: {result['error']}")
else:
    print(f"  ✅ 总用电量: {result['total_consumption_kwh']} kWh")
    print(f"  站点ID: {result['site_id']}")
