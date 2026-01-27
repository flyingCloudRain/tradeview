"""
Google Cloud Functions Gen 2 入口文件
使用 Mangum 将 FastAPI ASGI 应用转换为 Cloud Functions 兼容格式
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app

# 使用 Mangum 作为 ASGI 适配器（推荐方式）
try:
    from mangum import Mangum
    from flask import Request, Response
    import asyncio
    
    # 创建 ASGI 适配器
    handler = Mangum(app, lifespan="off")
    
    def main(request: Request) -> Response:
        """
        Google Cloud Functions Gen 2 HTTP 函数入口
        
        Args:
            request: Cloud Functions HTTP 请求对象 (flask.Request)
            
        Returns:
            Flask Response 对象
        """
        # 将 Flask Request 转换为 ASGI scope
        path = request.path
        if request.query_string:
            path = f"{path}?{request.query_string.decode() if isinstance(request.query_string, bytes) else request.query_string}"
        
        scope = {
            'type': 'http',
            'method': request.method,
            'path': request.path,
            'raw_path': request.path.encode(),
            'query_string': request.query_string if isinstance(request.query_string, bytes) else request.query_string.encode(),
            'headers': [
                (k.lower().encode(), v.encode() if isinstance(v, str) else v)
                for k, v in request.headers.items()
            ],
            'client': None,
            'server': (request.host.split(':')[0] if ':' in request.host else request.host, 443),
            'scheme': 'https',
            'root_path': '',
            'app': None,
            'asgi': {'version': '3.0', 'spec_version': '2.0'},
        }
        
        # 创建 ASGI 消息
        request_body = request.data if request.data else b''
        body_received = False
        
        async def receive():
            nonlocal body_received
            if not body_received:
                body_received = True
                return {
                    'type': 'http.request',
                    'body': request_body,
                    'more_body': False,
                }
            return {
                'type': 'http.request',
                'body': b'',
                'more_body': False,
            }
        
        response_status = 200
        response_headers = []
        response_body_parts = []
        
        async def send(message):
            nonlocal response_status, response_headers, response_body_parts
            if message['type'] == 'http.response.start':
                response_status = message['status']
                response_headers = [
                    (k.decode() if isinstance(k, bytes) else k, v.decode() if isinstance(v, bytes) else v)
                    for k, v in message['headers']
                ]
            elif message['type'] == 'http.response.body':
                body = message.get('body', b'')
                if isinstance(body, str):
                    body = body.encode()
                response_body_parts.append(body)
        
        # 运行 ASGI 应用
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(handler(scope, receive, send))
        
        # 构建 Flask Response
        return Response(
            b''.join(response_body_parts),
            status=response_status,
            headers=dict(response_headers)
        )
        
except ImportError:
    # 如果 Mangum 不可用，尝试使用 functions-framework（不推荐，但作为备选）
    try:
        from functions_framework import create_app
        from flask import Request
        
        # 注意：functions-framework 主要用于 WSGI，FastAPI 是 ASGI
        # 这里作为最后的备选方案
        def main(request: Request):
            """Cloud Functions 入口（使用 functions-framework，可能不工作）"""
            from flask import Response
            import json
            return Response(
                json.dumps({
                    'error': 'Mangum adapter not available',
                    'message': 'Please install mangum>=0.17.0 for FastAPI support'
                }),
                mimetype='application/json',
                status=500
            )
    except ImportError:
        # 最后的备选方案：直接错误
        def main(request):
            """Cloud Functions 入口（错误处理）"""
            from flask import Response
            import json
            return Response(
                json.dumps({
                    'error': 'Missing required dependencies',
                    'message': 'Please install mangum>=0.17.0 for FastAPI support'
                }),
                mimetype='application/json',
                status=500
            )
