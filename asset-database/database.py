"""
数据库配置和会话管理
支持SQLite WAL模式实现并发访问安全
"""
import os
import threading
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool

from models import Base


# 数据库URL配置
def get_database_url() -> str:
    """获取数据库URL"""
    # 优先使用环境变量
    db_url = os.environ.get('DATABASE_URL')

    if db_url:
        return db_url

    # 默认使用SQLite
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, 'assets.db')

    return f'sqlite:///{db_path}'


DATABASE_URL = get_database_url()


def create_db_engine(db_url: str = None):
    """
    创建数据库引擎，启用并发访问优化

    Args:
        db_url: 数据库URL，不提供则使用默认配置

    Returns:
        SQLAlchemy引擎
    """
    url = db_url or DATABASE_URL

    if url.startswith('sqlite'):
        engine = create_engine(
            url,
            connect_args={
                'check_same_thread': False,  # 允许多线程访问
                'timeout': 30,                # 30秒连接超时
            },
            poolclass=NullPool,           # 禁用连接池，避免多进程问题
            pool_pre_ping=True,           # 连接前检查可用性
            echo=False,                   # 不打印SQL
        )

        # 启用WAL模式和优化设置
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            # 启用WAL模式，支持并发读
            cursor.execute("PRAGMA journal_mode=WAL")
            # 设置忙等待超时（毫秒）
            cursor.execute("PRAGMA busy_timeout=30000")
            # 启用外键约束
            cursor.execute("PRAGMA foreign_keys=ON")
            # 同步模式设置（NORMAL在WAL模式下安全且更快）
            cursor.execute("PRAGMA synchronous=NORMAL")
            # 缓存大小（页数，负数表示KB）
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB缓存
            cursor.close()

        # 每次从连接池获取连接时重新设置PRAGMA
        @event.listens_for(engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

    else:
        # PostgreSQL/MySQL等其他数据库
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )

    return engine


# 全局引擎和会话工厂
_engine = None
_session_factory = None
_engine_lock = threading.Lock()


def get_engine():
    """获取全局引擎实例（线程安全）"""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:  # 双重检查
                _engine = create_db_engine()
    return _engine


def get_session_factory():
    """获取会话工厂"""
    global _session_factory
    if _session_factory is None:
        _session_factory = scoped_session(
            sessionmaker(
                bind=get_engine(),
                autocommit=False,
                autoflush=False,
            )
        )
    return _session_factory


@contextmanager
def get_db_session():
    """
    获取数据库会话的上下文管理器

    Usage:
        with get_db_session() as session:
            asset = session.query(Asset).first()
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(engine=None):
    """
    初始化数据库，创建所有表

    Args:
        engine: 数据库引擎，不提供则使用默认引擎
    """
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)


def drop_all_tables(engine=None):
    """
    删除所有表（危险操作，仅用于测试）

    Args:
        engine: 数据库引擎
    """
    if engine is None:
        engine = get_engine()
    Base.metadata.drop_all(engine)


# 便捷访问
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
