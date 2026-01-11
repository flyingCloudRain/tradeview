#!/usr/bin/env python3
"""
后端服务状态检测脚本
检查本地和 CloudBase 后端服务是否运行
"""
import sys
import os
import requests
import time
from pathlib import Path

# CloudBase API 地址
CLOUDBASE_API_BASE = "https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api"
LOCAL_API_BASE = "http://localhost:8000/api/v1"

def check_url(url, timeout=5):
    """检查 URL 是否可访问"""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=False)
        return {
            "status": "running",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response_time": response.elapsed.total_seconds()
        }
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "请求超时"}
    except requests.exceptions.ConnectionError:
        return {"status": "not_running", "error": "连接失败"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_health_endpoint(base_url):
    """测试健康检查端点"""
    health_url = f"{base_url}/health"
    if not health_url.startswith("http"):
        # 如果是相对路径，需要调整
        if base_url.endswith("/api/v1"):
            health_url = base_url.replace("/api/v1", "/health")
        else:
            health_url = f"{base_url}/health"
    
    print(f"   健康检查: {health_url}")
    result = check_url(health_url)
    return result

def test_api_endpoint(base_url):
    """测试 API 端点"""
    # 测试根路径
    root_url = base_url.replace("/api/v1", "") if "/api/v1" in base_url else base_url
    root_url = root_url.rstrip("/")
    
    print(f"   API 根路径: {root_url}/")
    root_result = check_url(f"{root_url}/")
    
    # 测试 API v1 端点（使用一个简单的端点）
    api_url = f"{base_url}/index/?date=2025-01-10"
    print(f"   API 端点: {api_url}")
    api_result = check_url(api_url)
    
    return {
        "root": root_result,
        "api": api_result
    }

def check_local_backend():
    """检查本地后端服务"""
    print("=" * 60)
    print("1. 检查本地后端服务")
    print("=" * 60)
    
    print(f"本地 API 地址: {LOCAL_API_BASE}")
    
    # 测试健康检查
    health_result = test_health_endpoint(LOCAL_API_BASE.replace("/api/v1", ""))
    
    if health_result["status"] == "running":
        print(f"✅ 本地后端服务正在运行")
        print(f"   状态码: {health_result['status_code']}")
        print(f"   响应时间: {health_result['response_time']:.3f}秒")
        
        # 测试 API 端点
        api_results = test_api_endpoint(LOCAL_API_BASE)
        
        if api_results["root"]["status"] == "running":
            print(f"✅ API 根路径可访问 (状态码: {api_results['root']['status_code']})")
        else:
            print(f"⚠️  API 根路径不可访问: {api_results['root'].get('error', '未知错误')}")
        
        return True
    else:
        print(f"❌ 本地后端服务未运行")
        print(f"   错误: {health_result.get('error', '未知错误')}")
        print(f"   提示: 请运行 'cd backend && uvicorn app.main:app --reload' 启动本地服务")
        return False

def check_cloudbase_backend():
    """检查 CloudBase 后端服务"""
    print("\n" + "=" * 60)
    print("2. 检查 CloudBase 后端服务")
    print("=" * 60)
    
    print(f"CloudBase API 地址: {CLOUDBASE_API_BASE}")
    
    # 测试健康检查
    health_url = f"{CLOUDBASE_API_BASE.replace('/api/v1', '')}/health"
    print(f"   健康检查: {health_url}")
    health_result = check_url(health_url)
    
    if health_result["status"] == "running":
        print(f"✅ CloudBase 后端服务正在运行")
        print(f"   状态码: {health_result['status_code']}")
        if 'response_time' in health_result:
            print(f"   响应时间: {health_result['response_time']:.3f}秒")
        
        # 检查 CORS 头
        if 'headers' in health_result:
            cors_headers = {k: v for k, v in health_result['headers'].items() 
                          if 'access-control' in k.lower()}
            if cors_headers:
                print(f"   CORS 头: {', '.join(cors_headers.keys())}")
        
        # 测试 API 端点
        print(f"\n   测试 API 端点...")
        api_results = test_api_endpoint(CLOUDBASE_API_BASE)
        
        if api_results["api"]["status"] == "running":
            status_code = api_results["api"]["status_code"]
            if status_code == 200:
                print(f"✅ API 端点可访问 (状态码: {status_code})")
            elif status_code == 400:
                print(f"⚠️  API 端点返回 400 (可能是参数问题，但服务在运行)")
            else:
                print(f"⚠️  API 端点返回状态码: {status_code}")
        else:
            print(f"⚠️  API 端点不可访问: {api_results['api'].get('error', '未知错误')}")
        
        return True
    elif health_result["status"] == "not_running":
        print(f"❌ CloudBase 后端服务未运行或不可访问")
        print(f"   错误: {health_result.get('error', '连接失败')}")
        print(f"   可能原因:")
        print(f"   1. 云函数未部署")
        print(f"   2. HTTP 访问服务未配置")
        print(f"   3. 网络问题")
        return False
    elif health_result["status"] == "timeout":
        print(f"⚠️  CloudBase 后端服务响应超时")
        print(f"   可能原因: 服务正在启动或网络延迟")
        return False
    else:
        print(f"❌ CloudBase 后端服务检查失败")
        print(f"   错误: {health_result.get('error', '未知错误')}")
        return False

def check_process():
    """检查本地进程（如果可能）"""
    print("\n" + "=" * 60)
    print("3. 检查本地进程")
    print("=" * 60)
    
    try:
        import subprocess
        
        # 检查是否有 uvicorn 进程
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ 找到 {len(pids)} 个 uvicorn 进程")
            for pid in pids:
                if pid:
                    print(f"   PID: {pid}")
            return True
        else:
            print("⚠️  未找到 uvicorn 进程")
            return False
    except Exception as e:
        print(f"⚠️  无法检查进程: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("后端服务状态检测")
    print("=" * 60)
    print(f"检测时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 检查本地后端
    results.append(("本地后端", check_local_backend()))
    
    # 检查 CloudBase 后端
    results.append(("CloudBase 后端", check_cloudbase_backend()))
    
    # 检查进程（可选）
    try:
        check_process()
    except:
        pass
    
    # 总结
    print("\n" + "=" * 60)
    print("检测总结")
    print("=" * 60)
    
    running_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ 运行中" if result else "❌ 未运行"
        print(f"{name:20} {status}")
    
    print(f"\n总计: {running_count}/{total_count} 个后端服务运行中")
    
    if running_count == 0:
        print("\n⚠️  没有检测到运行中的后端服务")
        print("   建议:")
        print("   1. 启动本地服务: cd backend && uvicorn app.main:app --reload")
        print("   2. 或部署到 CloudBase: tcb fn deploy trading-api")
    elif running_count == total_count:
        print("\n🎉 所有后端服务正常运行！")
    else:
        print(f"\n⚠️  部分后端服务未运行")
    
    return 0 if running_count > 0 else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n检测已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检测过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
