"""
Google Cloud Functions Gen 2 入口文件
使用 functions-framework 将 FastAPI ASGI 应用转换为 Cloud Functions 兼容格式
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app

# 使用 functions-framework 创建 WSGI 应用
try:
    from functions_framework import create_app
    
    # 创建 WSGI 应用
    functions_app = create_app(app)
    
    def main(request):
        """
        Google Cloud Functions Gen 2 HTTP 函数入口
        
        Args:
            request: Cloud Functions HTTP 请求对象 (flask.Request)
            
        Returns:
            HTTP 响应
        """
        return functions_app(request.environ, request.start_response)
        
except ImportError:
    # 如果没有 functions-framework，使用 mangum
    try:
        from mangum import Mangum
        from flask import Request, Response
        import asyncio
        import json
        
        # 创建 ASGI 适配器
        handler = Mangum(app, lifespan="off")
        
        def main(request):
            """Cloud Functions 入口（使用 Mangum）"""
            # 将 Flask Request 转换为 ASGI scope
            scope = {
                'type': 'http',
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string if isinstance(request.query_string, bytes) else request.query_string.encode(),
                'headers': [(k.encode(), v.encode()) if isinstance(v, str) else (k.encode(), v) for k, v in request.headers.items()],
                'server': (request.host.split(':')[0] if ':' in request.host else request.host, 443),
                'scheme': 'https',
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
                    response_headers = message['headers']
                elif message['type'] == 'http.response.body':
                    response_body_parts.append(message.get('body', b''))
            
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
        # 最后的备选方案：直接错误
        def main(request):
            """Cloud Functions 入口（错误处理）"""
            from flask import Response
            import json
            return Response(
                json.dumps({
                    'error': 'Missing required dependencies',
                    'message': 'Please install functions-framework or mangum'
                }),
                mimetype='application/json',
                status=500
            )
