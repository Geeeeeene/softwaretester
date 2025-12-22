"""数据库会话管理"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 创建数据库引擎
# 添加连接池配置和超时设置
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    # SQLite特定配置
    connect_args = {
        "timeout": 30,  # 连接超时（秒）- 增加到30秒
        "check_same_thread": False,  # 允许多线程访问
    }

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    echo=False,  # 设置为True可以看到SQL语句（调试用）
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 最大溢出连接数
    pool_timeout=30,  # 获取连接的超时时间（秒）
    connect_args=connect_args,
)

# 为SQLite添加连接事件监听，优化性能
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """设置SQLite优化参数"""
        try:
            cursor = dbapi_conn.cursor()
            # 启用WAL模式（Write-Ahead Logging），提高并发性能
            cursor.execute("PRAGMA journal_mode=WAL")
            # 设置同步模式为NORMAL（比FULL快，但安全性稍低）
            cursor.execute("PRAGMA synchronous=NORMAL")
            # 设置缓存大小（64MB，负值表示KB）
            cursor.execute("PRAGMA cache_size=-65536")
            # 启用外键检查
            cursor.execute("PRAGMA foreign_keys=ON")
            # 设置忙等待超时（30秒，单位毫秒）
            cursor.execute("PRAGMA busy_timeout=30000")
            # 设置临时文件存储在内存中（提高性能）
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
            logger.debug("SQLite优化参数已设置: WAL模式, NORMAL同步, 64MB缓存")
        except Exception as e:
            logger.warning(f"设置SQLite优化参数失败: {e}")

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
