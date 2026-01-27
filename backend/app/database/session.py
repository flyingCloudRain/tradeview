"""
数据库会话管理
仅支持 PostgreSQL/Supabase 数据库
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings

# 创建数据库引擎（PostgreSQL/Supabase）
db_url = settings.DATABASE_URL

# 验证数据库URL是否为PostgreSQL
if not db_url.lower().startswith('postgresql://'):
    raise ValueError(
        f"不支持的数据库类型。当前项目仅支持 PostgreSQL/Supabase 数据库。\n"
        f"请设置 DATABASE_URL 环境变量为 Supabase PostgreSQL 连接字符串。\n"
        f"当前值: {db_url[:50]}..."
    )

# 查询超时设置（秒）
QUERY_TIMEOUT = 30

# PostgreSQL/Supabase 连接参数
connect_args = {}

# 优化连接池配置：
# - pool_size: 基础连接池大小，增加以支持更多并发请求和定时任务
# - max_overflow: 超出pool_size后可以创建的额外连接数
# - pool_timeout: 获取连接的超时时间
# 注意：定时任务使用独立线程执行，需要足够的连接数避免阻塞
engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # 连接前ping，确保连接有效
    pool_size=15,  # 增加基础连接池大小（从10增加到15）
    max_overflow=25,  # 增加最大溢出连接数（从20增加到25），支持更多并发
    pool_timeout=10,  # 连接池获取连接超时
    pool_recycle=3600,  # 连接回收时间（1小时），避免长时间连接导致的数据库连接超时
    echo=False,
)

# 为 PostgreSQL 添加查询超时事件监听
@event.listens_for(engine, "connect")
def set_postgres_timeout(dbapi_conn, connection_record):
    """设置 PostgreSQL 查询超时"""
    try:
        # PostgreSQL的cursor支持上下文管理器
        if hasattr(dbapi_conn, 'cursor') and 'psycopg' in str(type(dbapi_conn)):
            with dbapi_conn.cursor() as cursor:
                cursor.execute(f"SET statement_timeout = {QUERY_TIMEOUT * 1000}")  # 毫秒
    except Exception:
        pass  # 忽略错误

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

