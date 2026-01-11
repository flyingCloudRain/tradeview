"""
配置文件
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "交易复盘系统"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    # 优先使用环境变量，如果没有则尝试SQLite（用于开发测试）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'trading_review.db')}"
    )
    
    # Supabase配置
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Redis配置（可选）
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # CORS配置
    # 支持从环境变量读取，格式：JSON 数组字符串，如 '["https://example.com"]'
    _cors_origins_env = os.getenv("CORS_ORIGINS")
    if _cors_origins_env:
        import json
        try:
            CORS_ORIGINS: list = json.loads(_cors_origins_env)
        except json.JSONDecodeError:
            # 如果解析失败，使用默认值
            CORS_ORIGINS: list = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com",
                "https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com",
            ]
    else:
        CORS_ORIGINS: list = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com",
            "https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com",
        ]
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

