"""
Google Cloud Functions Gen 2 入口文件
使用 mangum 适配器将 FastAPI ASGI 应用转换为 Cloud Functions 兼容格式
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app

# 使用 mangum 适配器（推荐用于 Cloud Functions Gen 2）
try:
    from mangum import Mangum
    
    # 创建 ASGI 适配器
    handler = Mangum(app, lifespan="off")
    
    def main(request):
        """
        Google Cloud Functions Gen 2 HTTP 函数入口
        
        Args:
            request: Cloud Functions HTTP 请求对象
            
        Returns:
            HTTP 响应
        """
        return handler(request)
        
except ImportError:
    # 如果没有 mangum，尝试使用 functions-framework
    try:
        from functions_framework import create_app
        
        functions_app = create_app(app)
        
        def main(request):
            """Cloud Functions 入口（使用 functions-framework）"""
            return functions_app(request.environ, lambda status, headers: None)
            
    except ImportError:
        # 最后的备选方案：直接使用 FastAPI（需要手动处理请求）
        from fastapi import Request
        from fastapi.responses import Response
        import json
        
        async def main(request):
            """Cloud Functions 入口（直接 ASGI 方式）"""
            # 将 Cloud Functions 请求转换为 ASGI 格式
            scope = {
                "type": "http",
                "method": request.method,
                "path": request.path,
                "query_string": request.query_string.encode() if request.query_string else b"",
                "headers": [(k.encode(), v.encode()) for k, v in request.headers.items()],
            }
            
            async def receive():
                return {
                    "type": "http.request",
                    "body": await request.get_data(),
                }
            
            async def send(message):
                pass  # 响应将通过返回值发送
            
            return await app(scope, receive, send)
