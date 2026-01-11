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
    # 必须通过环境变量设置 DATABASE_URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    
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
            ]
    else:
        CORS_ORIGINS: list = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
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

