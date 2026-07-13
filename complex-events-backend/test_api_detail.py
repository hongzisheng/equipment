import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8800"

apis_to_check = [
    {"name": "工人管理-列表", "url": f"{BASE_URL}/api/workers", "method": "GET"},
    {"name": "设备管理-列表", "url": f"{BASE_URL}/api/equipment-instances", "method": "GET"},
    {"name": "物料管理-列表", "url": f"{BASE_URL}/api/materials", "method": "GET"},
    {"name": "流程确认-列表", "url": f"{BASE_URL}/process/list", "method": "GET"},
]

print("=" * 80)
print("API接口详细测试报告")
print("=" * 80)

for api in apis_to_check:
    print(f"\n{'='*80}")
    print(f"测试: {api['name']}")
    print(f"URL: {api['url']}")
    print(f"方法: {api['method']}")
    print("-" * 80)
    
    try:
        if api["method"] == "GET":
            req = urllib.request.Request(api["url"], method="GET")
        else:
            req = urllib.request.Request(api["url"], method="POST", data=b"{}", headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            content = response.read().decode()
            
            print(f"HTTP状态码: {status_code}")
            print(f"响应内容: {content[:500]}")
            
            try:
                data = json.loads(content)
                print(f"\n解析后的JSON:")
                print(f"  code: {data.get('code')}")
                print(f"  message: {data.get('message')}")
                print(f"  data类型: {type(data.get('data'))}")
                if isinstance(data.get('data'), list):
                    print(f"  data长度: {len(data.get('data'))}")
                elif isinstance(data.get('data'), dict):
                    print(f"  data键: {list(data.get('data').keys())}")
                    for k, v in data.get('data', {}).items():
                        if isinstance(v, list):
                            print(f"    {k}: {len(v)}条数据")
                        else:
                            print(f"    {k}: {v}")
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} - {e.reason}")
        try:
            content = e.read().decode()
            print(f"错误响应: {content}")
        except:
            pass
    except urllib.error.URLError as e:
        print(f"连接错误: {e.reason}")
    except Exception as e:
        print(f"未知错误: {str(e)}")

print("\n" + "=" * 80)
