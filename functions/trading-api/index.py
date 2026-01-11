"""
CloudBase 云函数入口
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app

def main_handler(event, context):
    """
    云函数入口
    将 FastAPI 应用包装为 CloudBase 云函数
    """
    try:
        from mangum import Mangum
        
        handler = Mangum(app, lifespan="off")
        
        return handler(event, context)
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
