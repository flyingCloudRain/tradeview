"""
数据库会话管理
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# 创建数据库引擎（PostgreSQL）
db_url = settings.DATABASE_URL

# 查询超时设置（秒）
QUERY_TIMEOUT = 30

# PostgreSQL 连接参数
connect_args = {}
engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,  # 连接池获取连接超时
    echo=False,
)

# 为 PostgreSQL 添加查询超时事件监听
@event.listens_for(engine, "connect")
def set_postgres_timeout(dbapi_conn, connection_record):
    """设置 PostgreSQL 查询超时"""
    with dbapi_conn.cursor() as cursor:
        cursor.execute(f"SET statement_timeout = {QUERY_TIMEOUT * 1000}")  # 毫秒

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

