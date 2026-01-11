"""
数据库迁移工具
支持在 CloudBase 云函数环境中自动运行 Alembic 迁移
"""
import os
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 迁移状态标志（确保只运行一次）
_migration_run = False


def run_migrations() -> bool:
    """
    运行数据库迁移
    
    Returns:
        bool: 迁移是否成功
    """
    global _migration_run
    
    # 如果已经运行过，跳过
    if _migration_run:
        logger.info("数据库迁移已运行，跳过")
        return True
    
    try:
        # 检查数据库连接字符串
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL 未配置，跳过数据库迁移")
            return False
        
        # 隐藏密码的日志输出
        safe_url = _mask_password(database_url)
        logger.info(f"开始运行数据库迁移，数据库: {safe_url}")
        
        # 获取项目根目录
        # 在 CloudBase 环境中，路径可能是 functions/trading-api
        current_dir = Path(__file__).resolve()
        
        # 尝试找到 backend 目录或 alembic 目录
        alembic_dir = None
        alembic_ini = None
        
        # 方案1: 在 functions/trading-api 中查找
        for parent in current_dir.parents:
            alembic_path = parent / "alembic"
            alembic_ini_path = parent / "alembic.ini"
            if alembic_path.exists() and alembic_ini_path.exists():
                alembic_dir = alembic_path
                alembic_ini = alembic_ini_path
                break
        
        if not alembic_dir or not alembic_ini:
            logger.warning("未找到 alembic 目录或 alembic.ini，跳过迁移")
            return False
        
        # 设置工作目录
        original_cwd = os.getcwd()
        os.chdir(str(alembic_ini.parent))
        
        try:
            # 导入 Alembic API
            from alembic import command
            from alembic.config import Config
            
            # 创建 Alembic 配置
            alembic_cfg = Config(str(alembic_ini))
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            # 运行迁移
            logger.info("执行 alembic upgrade head...")
            command.upgrade(alembic_cfg, "head")
            
            logger.info("✅ 数据库迁移完成")
            _migration_run = True
            return True
            
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
            
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {str(e)}", exc_info=True)
        # 不抛出异常，避免影响应用启动
        # 在生产环境中，可以考虑记录到监控系统
        return False


def _mask_password(url: str) -> str:
    """隐藏数据库连接字符串中的密码"""
    try:
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        
        parsed = urlparse(url)
        if parsed.password:
            # 替换密码为 ***
            masked_netloc = parsed.netloc.replace(
                f":{parsed.password}@", ":***@"
            )
            masked = parsed._replace(netloc=masked_netloc)
            return urlunparse(masked)
        return url
    except Exception:
        # 如果解析失败，返回原字符串（不包含密码的部分）
        if "@" in url:
            parts = url.split("@")
            if len(parts) == 2:
                return f"{parts[0].split(':')[0]}:***@{parts[1]}"
        return url


def check_migration_status() -> Optional[str]:
    """
    检查当前数据库迁移版本
    
    Returns:
        Optional[str]: 当前版本号，如果检查失败返回 None
    """
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return None
        
        # 获取项目根目录
        current_dir = Path(__file__).resolve()
        alembic_ini = None
        
        for parent in current_dir.parents:
            alembic_ini_path = parent / "alembic.ini"
            if alembic_ini_path.exists():
                alembic_ini = alembic_ini_path
                break
        
        if not alembic_ini:
            return None
        
        # 设置工作目录
        original_cwd = os.getcwd()
        os.chdir(str(alembic_ini.parent))
        
        try:
            from alembic import command
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext
            from sqlalchemy import create_engine
            
            # 创建 Alembic 配置
            alembic_cfg = Config(str(alembic_ini))
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            
            # 创建引擎
            engine = create_engine(database_url)
            
            # 获取当前版本
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()
                
            return current_rev
            
        finally:
            os.chdir(original_cwd)
            
    except Exception as e:
        logger.error(f"检查迁移状态失败: {str(e)}", exc_info=True)
        return None
