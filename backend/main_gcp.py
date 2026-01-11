"""
Google Cloud Functions 入口文件
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app

# 使用 functions-framework 作为适配器
try:
    from functions_framework import create_app
    
    # 创建 Cloud Functions 应用
    functions_app = create_app(app)
    
    def cloud_function(request):
        """
        Google Cloud Functions HTTP 函数入口
        
        Args:
            request: Flask Request 对象（functions-framework 会自动转换）
            
        Returns:
            Flask Response 对象
        """
        return functions_app(request.environ, lambda status, headers: None)
    
except ImportError:
    # 如果没有安装 functions-framework，使用直接 ASGI 方式
    from fastapi import Request
    from fastapi.responses import Response
    import json
    
    async def cloud_function(request: Request):
        """
        Google Cloud Functions HTTP 函数入口（直接 ASGI 方式）
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            FastAPI Response 对象
        """
        # 直接使用 FastAPI 应用处理请求
        return await app(request.scope, request.receive, request._send)
