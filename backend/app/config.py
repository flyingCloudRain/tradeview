"""
配置文件
"""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "交易复盘系统"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    # 必须通过环境变量设置 DATABASE_URL
    # 在 Cloud Functions 环境中，允许延迟验证
    DATABASE_URL: str = Field(default="", description="数据库连接URL")
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """验证 DATABASE_URL 是否设置"""
        # 在 Cloud Functions 环境中，允许延迟验证
        is_gcp = os.getenv("FUNCTION_TARGET") or os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not v and not is_gcp:
            # 非 GCP 环境必须设置 DATABASE_URL
            raise ValueError("DATABASE_URL environment variable is required")
        # GCP 环境中，如果未设置，返回空字符串，在真正使用时再验证
        return v or ""
    
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
        # 在 GCP 环境中，不使用 .env 文件，只使用环境变量
        # 这样可以避免本地配置覆盖 GCP 环境变量
        is_gcp = os.getenv("FUNCTION_TARGET") or os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT")
        env_file = None if is_gcp else ".env"  # GCP 环境中禁用 .env 文件
        case_sensitive = True


settings = Settings()

