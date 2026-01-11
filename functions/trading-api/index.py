"""
CloudBase 云函数入口
"""
import sys
import os
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 设置 CloudBase 环境标识
os.environ["CLOUDBASE_ENV"] = "true"

# 在导入 app 之前运行数据库迁移（只运行一次）
try:
    from app.utils.migrate import run_migrations
    print("[CloudBase Handler] 开始运行数据库迁移...")
    run_migrations()
except Exception as e:
    print(f"[CloudBase Handler] 数据库迁移失败（非致命错误）: {e}")
    # 不抛出异常，允许应用继续启动

from app.main import app

def main_handler(event, context):
    """
    云函数入口
    将 FastAPI 应用包装为 CloudBase 云函数
    """
    try:
        from mangum import Mangum
        
        # 处理路径前缀（如果 HTTP 访问服务传递了 /trading-api 前缀）
        path = event.get("path", "/")
        if path.startswith("/trading-api"):
            # 去掉 /trading-api 前缀
            path = path[len("/trading-api"):]
            if not path:
                path = "/"
            event["path"] = path
        
        # 调试日志
        print(f"[CloudBase Handler] Event: {json.dumps(event, default=str, indent=2)}")
        print(f"[CloudBase Handler] Path: {path}")
        print(f"[CloudBase Handler] Headers: {event.get('headers', {})}")
        
        handler = Mangum(app, lifespan="off")
        result = handler(event, context)
        
        # 确保响应包含 CORS 头
        if isinstance(result, dict) and "headers" in result:
            headers = result.get("headers", {})
            # 如果响应头中没有 CORS 头，添加它们
            origin = event.get("headers", {}).get("origin") or event.get("headers", {}).get("Origin")
            if origin and "access-control-allow-origin" not in {k.lower(): v for k, v in headers.items()}:
                if not isinstance(headers, dict):
                    headers = dict(headers) if headers else {}
                headers["Access-Control-Allow-Origin"] = origin
                headers["Access-Control-Allow-Credentials"] = "true"
                headers["Access-Control-Allow-Methods"] = "*"
                headers["Access-Control-Allow-Headers"] = "*"
                result["headers"] = headers
        
        return result
    except ImportError:
        # 如果没有安装 mangum，使用简单的适配器
        from fastapi.responses import JSONResponse
        
        # 解析事件
        path = event.get("path", "/")
        method = event.get("httpMethod", "GET")
        headers = event.get("headers", {})
        query_string = event.get("queryString", "")
        body = event.get("body", "")
        
        # 构建 ASGI 请求
        async def receive():
            return {
                "type": "http.request",
                "body": body.encode() if body else b"",
            }
        
        # 这里需要实现完整的 ASGI 适配
        # 建议安装 mangum 库
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Please install mangum: pip install mangum"}'
        }
