"""
测试前后端连接的诊断脚本
"""
import requests
import time

def test_health_endpoint():
    """测试健康检查端点"""
    print("1. 测试 /health 端点...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"   ✓ 状态码: {response.status_code}")
        print(f"   ✓ 响应: {response.json()}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    print()

def test_analyze_endpoint():
    """测试分析端点"""
    print("2. 测试 /api/analyze/octocat 端点...")
    print("   (这可能需要几秒钟...)")
    try:
        start_time = time.time()
        response = requests.get(
            "http://localhost:8000/api/analyze/octocat",
            timeout=30
        )
        elapsed = time.time() - start_time
        print(f"   ✓ 状态码: {response.status_code}")
        print(f"   ✓ 耗时: {elapsed:.2f}秒")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 用户名: {data.get('username')}")
            print(f"   ✓ 技术倾向数量: {len(data.get('tech_tendency', []))}")
        else:
            print(f"   ✗ 响应: {response.text}")
    except requests.Timeout:
        print(f"   ✗ 请求超时(30秒)")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    print()

def test_vite_proxy():
    """测试Vite代理"""
    print("3. 测试 Vite 代理 (http://localhost:5173/api/health)...")
    try:
        response = requests.get("http://localhost:5173/api/health", timeout=5)
        print(f"   ✓ 状态码: {response.status_code}")
        print(f"   ✓ 响应: {response.json()}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("DevScope 连接诊断")
    print("=" * 60)
    print()
    
    test_health_endpoint()
    test_vite_proxy()
    test_analyze_endpoint()
    
    print("=" * 60)
    print("诊断完成")
    print("=" * 60)
