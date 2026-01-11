"""
FastAPI应用入口
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.api.v1 import api_router

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

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.tcloudbaseapp\.com",  # 允许所有 tcloudbaseapp.com 子域名
    allow_origins=precise_origins,  # 精确匹配的域名（本地开发等）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 全局异常处理，确保CORS头总是被添加
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理，确保CORS头总是被添加"""
    import traceback
    error_msg = str(exc)
    print(f"[Global Exception Handler] 错误: {error_msg}")
    traceback.print_exc()
    origin = request.headers.get("origin", "*")
    if origin not in settings.CORS_ORIGINS and origin != "*":
        origin = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "*"
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {error_msg}"},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理，确保CORS头总是被添加"""
    origin = request.headers.get("origin", "*")
    if origin not in settings.CORS_ORIGINS and origin != "*":
        origin = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "*"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理，确保CORS头总是被添加"""
    from fastapi.encoders import jsonable_encoder
    origin = request.headers.get("origin", "*")
    if origin not in settings.CORS_ORIGINS and origin != "*":
        origin = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "*"
    # 使用 jsonable_encoder 确保所有字段都能被正确序列化
    errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    )

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "交易复盘系统API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}

