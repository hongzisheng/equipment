import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8800"

apis = [
    {"name": "工人管理-列表", "url": f"{BASE_URL}/api/workers", "method": "GET"},
    {"name": "设备管理-列表", "url": f"{BASE_URL}/api/equipment-instances", "method": "GET"},
    {"name": "物料管理-列表", "url": f"{BASE_URL}/api/materials", "method": "GET"},
    {"name": "工具管理-列表", "url": f"{BASE_URL}/api/maintenance-tools", "method": "GET"},
    {"name": "流程确认-列表", "url": f"{BASE_URL}/process/list", "method": "GET"},
    {"name": "流程确认-设备信息", "url": f"{BASE_URL}/process/equipment/info", "method": "GET"},
    {"name": "信息面板-工人状态", "url": f"{BASE_URL}/info/workers", "method": "POST"},
    {"name": "信息面板-工单列表", "url": f"{BASE_URL}/info/orders", "method": "GET"},
    {"name": "信息面板-物料库存", "url": f"{BASE_URL}/info/materials", "method": "POST"},
    {"name": "信息面板-工具状态", "url": f"{BASE_URL}/info/tools", "method": "POST"},
    {"name": "调度-工人列表", "url": f"{BASE_URL}/api/workers", "method": "GET"},
    {"name": "调度-工人类型", "url": f"{BASE_URL}/api/worker-types", "method": "GET"},
    {"name": "调度-设备分类", "url": f"{BASE_URL}/api/equipment-categories", "method": "GET"},
    {"name": "调度-选中工人", "url": f"{BASE_URL}/api/selected-workers", "method": "GET"},
    {"name": "工单管理-工单列表", "url": f"{BASE_URL}/work-orders", "method": "GET"},
    {"name": "工单管理-工单任务", "url": f"{BASE_URL}/work-order-tasks", "method": "GET"},
    {"name": "工单管理-工序模板", "url": f"{BASE_URL}/process-templates", "method": "GET"},
]

print("=" * 60)
print("API接口测试报告")
print("=" * 60)

success_count = 0
fail_count = 0
fail_details = []

for api in apis:
    try:
        if api["method"] == "GET":
            req = urllib.request.Request(api["url"], method="GET")
        else:
            req = urllib.request.Request(api["url"], method="POST", data=b"{}", headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            try:
                data = json.loads(response.read().decode())
                code = data.get("code", data.get("success", "N/A"))
                data_count = len(data.get("data", [])) if isinstance(data.get("data"), list) else \
                             len(data.get("data", {}).get("workers", [])) if isinstance(data.get("data"), dict) else \
                             len(data.get("data", {}).get("list", [])) if isinstance(data.get("data"), dict) else \
                             data.get("total_count", data.get("total", "N/A"))
                
                print(f"✓ [{status_code}] {api['name']}")
                print(f"   响应码: {code}")
                print(f"   数据量: {data_count}")
                success_count += 1
            except json.JSONDecodeError:
                content = response.read().decode()[:200]
                print(f"✓ [{status_code}] {api['name']}")
                print(f"   响应: {content}")
                success_count += 1
                
    except urllib.error.HTTPError as e:
        print(f"✗ [{e.code}] {api['name']}")
        print(f"   错误: {e.reason}")
        fail_count += 1
        fail_details.append(f"{api['name']}: HTTP {e.code} {e.reason}")
    except urllib.error.URLError as e:
        print(f"✗ [连接失败] {api['name']}")
        print(f"   错误: {e.reason}")
        fail_count += 1
        fail_details.append(f"{api['name']}: 连接失败 {e.reason}")
    except Exception as e:
        print(f"✗ [未知错误] {api['name']}")
        print(f"   错误: {str(e)}")
        fail_count += 1
        fail_details.append(f"{api['name']}: {str(e)}")
    
    print()

print("=" * 60)
print(f"测试结果: 成功 {success_count} / 失败 {fail_count}")
print("=" * 60)

if fail_details:
    print("\n失败详情:")
    for detail in fail_details:
        print(f"  - {detail}")
