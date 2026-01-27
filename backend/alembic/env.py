"""
Alembic环境配置
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 导入配置和模型
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 导入 settings（可能会抛出 ValueError 如果 DATABASE_URL 未设置）
# 但我们先尝试从其他来源获取 DATABASE_URL
try:
    from app.config import settings
except ValueError:
    # 如果 settings 导入失败，先尝试从环境变量或 alembic.ini 获取
    settings = None

# 确定数据库URL的优先级：环境变量 > alembic.ini > settings
database_url = os.getenv("DATABASE_URL")

# 如果没有环境变量，尝试从 alembic.ini 读取
if not database_url:
    database_url = config.get_main_option("sqlalchemy.url")
    # 如果是占位符或无效值，清空以便后续从 settings 读取
    if database_url == "driver://user:pass@localhost/dbname":
        database_url = None

# 如果前两者都没有，尝试从 settings 读取
if not database_url:
    if settings:
        database_url = settings.DATABASE_URL
    else:
        # 如果 settings 也没有，提供友好的错误信息
        raise ValueError(
            "DATABASE_URL 环境变量未设置。\n"
            "请执行以下操作之一：\n"
            "1. 设置环境变量: export DATABASE_URL='postgresql://...'\n"
            "2. 在 alembic.ini 中配置 sqlalchemy.url\n"
            "3. 使用: source backend/setup_env.sh"
        )

# 设置数据库URL到 alembic config
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# 导入模型（在设置数据库URL之后）
from app.database.base import Base
from app.models import *  # 导入所有模型

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

