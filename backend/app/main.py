"""
FastAPI应用入口
"""
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 延迟导入配置，允许在 Cloud Functions 环境中延迟验证
try:
    from app.config import settings
except Exception as e:
    # 如果配置加载失败，创建一个最小配置
    import os
    class MinimalSettings:
        PROJECT_NAME = "交易复盘系统"
        VERSION = "1.0.0"
        API_V1_PREFIX = "/api/v1"
        CORS_ORIGINS = []
        DATABASE_URL = os.getenv("DATABASE_URL", "")
    settings = MinimalSettings()
    print(f"[警告] 配置加载失败，使用最小配置: {e}")

from app.api.v1 import api_router

# 在云环境中自动运行数据库迁移（异步执行，不阻塞应用启动）
is_gcp = os.getenv("FUNCTION_TARGET") or os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT")

if is_gcp:
    import threading
    def run_migrations_async():
        """异步运行数据库迁移，不阻塞应用启动"""
        try:
            from app.utils.migrate import run_migrations
            print(f"[App Startup] 检测到 Google Cloud Functions 环境，开始异步运行数据库迁移...")
            run_migrations()
        except Exception as e:
            print(f"[App Startup] 数据库迁移失败（非致命错误）: {e}")
            import traceback
            traceback.print_exc()
    
    # 在后台线程中运行迁移，不阻塞应用启动
    migration_thread = threading.Thread(target=run_migrations_async, daemon=True)
    migration_thread.start()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件 - 必须在其他中间件之前
# 过滤掉通配符域名，使用正则表达式匹配
import re
precise_origins = [origin for origin in settings.CORS_ORIGINS if "*" not in origin]

# CORS正则表达式模式 - 匹配所有 Cloud Functions 和 Cloud Run 域名
CORS_ORIGIN_REGEX = r"https://.*\.cloudfunctions\.net|https://.*\.run\.app|https://.*\.a\.run\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=CORS_ORIGIN_REGEX,  # 允许所有 Google Cloud Functions 和 Cloud Run 域名
    allow_origins=precise_origins,  # 精确匹配的域名（本地开发等）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def get_allowed_origin(request: Request) -> str:
    """获取允许的Origin，支持精确匹配和正则匹配"""
    origin = request.headers.get("origin")
    if not origin:
        return "*"
    
    # 检查精确匹配
    if origin in settings.CORS_ORIGINS:
        return origin
    
    # 检查正则匹配（Google Cloud Functions 域名）
    if re.match(CORS_ORIGIN_REGEX, origin):
        return origin
    
    # 如果都不匹配，返回第一个允许的源或通配符
    return settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "*"


def get_cors_headers(request: Request) -> dict:
    """获取CORS响应头"""
    origin = get_allowed_origin(request)
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }


# 全局异常处理，确保CORS头总是被添加
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理，确保CORS头总是被添加"""
    import traceback
    error_msg = str(exc)
    print(f"[Global Exception Handler] 错误: {error_msg}")
    traceback.print_exc()
    
    # 确保 CORS 头总是被添加
    cors_headers = get_cors_headers(request)
    
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {error_msg}"},
        headers=cors_headers
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理，确保CORS头总是被添加"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=get_cors_headers(request)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理，确保CORS头总是被添加"""
    from fastapi.encoders import jsonable_encoder
    # 使用 jsonable_encoder 确保所有字段都能被正确序列化
    errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
        headers=get_cors_headers(request)
    )

# 注册路由（使用 try-except 确保即使路由注册失败，应用也能启动）
try:
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
except Exception as e:
    print(f"[警告] API 路由注册失败: {e}")
    import traceback
    traceback.print_exc()
    # 创建一个简单的错误路由，避免应用完全无法启动
    @app.get(settings.API_V1_PREFIX + "/{path:path}")
    def api_error_handler(path: str):
        return {"error": "API路由注册失败", "message": str(e)}


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "交易复盘系统API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check(request: Request):
    """健康检查 - 不依赖任何外部服务，确保返回 CORS 头"""
    try:
        # 基本健康检查，不访问数据库或其他服务
        response_data = {
            "status": "ok",
            "service": "trading-api",
            "version": settings.VERSION
        }
        # 确保返回 CORS 头
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=response_data,
            headers=get_cors_headers(request)
        )
    except Exception as e:
        # 即使健康检查本身出错，也返回错误信息
        import traceback
        error_details = traceback.format_exc()
        print(f"[Health Check Error] {error_details}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "service": "trading-api"
            },
            headers=get_cors_headers(request)
        )

