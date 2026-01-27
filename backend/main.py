"""
Google Cloud Functions Gen 2 入口文件
使用 Mangum 将 FastAPI ASGI 应用转换为 Cloud Functions 兼容格式
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 延迟导入，确保快速启动
try:
    from app.main import app
except Exception as e:
    # 如果导入失败，创建一个简单的错误响应应用
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def error_root():
        return {"error": f"应用启动失败: {str(e)}"}
    
    @app.get("/health")
    def error_health():
        return {"status": "error", "message": str(e)}

# 使用 Mangum 作为 ASGI 适配器（推荐方式）
try:
    from mangum import Mangum
    from flask import Request, Response
    import asyncio
    import json
    
    # 创建 ASGI 适配器
    # Mangum 实例本身就是一个 ASGI 应用，可以直接调用
    mangum_handler = Mangum(app, lifespan="off")
    
    def main(request: Request) -> Response:
        """
        Google Cloud Functions Gen 2 HTTP 函数入口
        
        Args:
            request: Cloud Functions HTTP 请求对象 (flask.Request)
            
        Returns:
            Flask Response 对象
        """
        # 将 Flask Request 转换为 ASGI scope
        query_string = request.query_string
        if isinstance(query_string, str):
            query_string = query_string.encode()
        elif query_string is None:
            query_string = b''
        
        # 获取请求体
        request_body = request.data if request.data else b''
        
        scope = {
            'type': 'http',
            'method': request.method,
            'path': request.path,
            'raw_path': request.path.encode(),
            'query_string': query_string,
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
        
        # 创建 ASGI receive 函数
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
        
        # 创建 ASGI send 函数
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
        # 确保使用正确的事件循环
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 调用 Mangum handler
        # Mangum 实例是可调用的 ASGI 应用，接受 (scope, receive, send) 三个参数
        # 注意：Mangum 的 __call__ 方法签名是 __call__(self, scope, receive, send)
        # 所以调用时只需要传递 scope, receive, send 三个参数
        try:
            # 直接调用 Mangum 实例，它会自动处理 ASGI 协议
            # 确保传递的是正确的参数：scope (dict), receive (async callable), send (async callable)
            if asyncio.iscoroutinefunction(mangum_handler):
                # 如果是协程函数，直接 await
                result = loop.run_until_complete(mangum_handler(scope, receive, send))
            else:
                # 如果是可调用对象，直接调用
                result = loop.run_until_complete(mangum_handler(scope, receive, send))
        except TypeError as e:
            # 如果参数数量错误，尝试使用 __call__ 方法
            import traceback
            error_details = traceback.format_exc()
            print(f"[Mangum Error] 参数错误: {e}")
            print(f"[Mangum Error] Mangum 类型: {type(mangum_handler)}")
            print(f"[Mangum Error] Mangum 可调用: {callable(mangum_handler)}")
            print(f"[Mangum Error] 错误详情:\n{error_details}")
            # 尝试使用 __call__ 方法
            try:
                result = loop.run_until_complete(mangum_handler.__call__(scope, receive, send))
            except Exception as e2:
                print(f"[Mangum Error] __call__ 也失败: {e2}")
                return Response(
                    json.dumps({
                        'error': 'Internal server error',
                        'message': f'Mangum调用失败: {str(e)}',
                        'type': type(e).__name__
                    }),
                    mimetype='application/json',
                    status=500
                )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[Mangum Error] 调用失败: {e}")
            print(f"[Mangum Error] 错误详情:\n{error_details}")
            # 返回错误响应
            return Response(
                json.dumps({
                    'error': 'Internal server error',
                    'message': str(e),
                    'type': type(e).__name__
                }),
                mimetype='application/json',
                status=500
            )
        
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
