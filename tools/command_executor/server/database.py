"""
服务端数据库操作
使用SQLAlchemy + SQLite（测试环境）
"""
# Python 3.6 兼容性补丁 - 使用 pysqlite3 替代 sqlite3
import sys
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import uuid
import hashlib
import secrets

from server.config import SESSION_HISTORY_RETENTION_DAYS

# 使用SQLite数据库
# 支持通过环境变量 DB_PATH 指定数据库路径（打包环境推荐使用绝对路径）
# 例如: DB_PATH=/opt/command-executor-server/data/server_data.db
_db_path_env = os.environ.get("DB_PATH", "")
if _db_path_env:
    DB_PATH = Path(_db_path_env)
else:
    DB_PATH = Path(__file__).parent / "server_data.db"

# 确保数据库目录存在
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建引擎
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== 数据库模型 ====================

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    api_key = Column(String(128), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联的客户端
    clients = relationship("UserClient", back_populates="user", cascade="all, delete-orphan")


class UserClient(Base):
    """用户-客户端关联表"""
    __tablename__ = "user_clients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    client_id = Column(String(100), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by = Column(String(100), default="system", nullable=False)

    # 关联用户
    user = relationship("User", back_populates="clients")


class APIToken(Base):
    """API令牌表"""
    __tablename__ = "api_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(128), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)


class Session(Base):
    """会话记录表"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    client_id = Column(String(100), index=True, nullable=False)
    task_type = Column(String(50), nullable=False)  # ssh / http
    request_data = Column(JSON, nullable=False)
    response_data = Column(JSON, nullable=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ClientConnection(Base):
    """客户端连接状态表"""
    __tablename__ = "client_connections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(100), unique=True, index=True, nullable=False)
    hostname = Column(String(255), nullable=False)
    os_info = Column(String(255), nullable=False)
    is_online = Column(Boolean, default=True, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    first_connected = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # 关联用户


# ==================== 数据库初始化 ====================

def init_database():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    print(f"数据库已创建: {DB_PATH}")


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 会话操作 ====================

class SessionManager:
    """会话管理器"""

    @staticmethod
    def create_session(
        db: Session,
        session_id: str,
        client_id: str,
        task_type: str,
        request_data: dict
    ) -> Session:
        """创建会话记录"""
        session = Session(
            session_id=session_id,
            client_id=client_id,
            task_type=task_type,
            request_data=request_data,
            success=False
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def update_session_result(
        db: Session,
        session_id: str,
        success: bool,
        response_data: dict,
        error_message: str = None
    ):
        """更新会话结果"""
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            session.success = success
            session.response_data = response_data
            session.error_message = error_message
            db.commit()

    @staticmethod
    def get_client_sessions(
        db: Session,
        client_id: str,
        limit: int = 100
    ) -> List[Session]:
        """获取客户端的会话记录"""
        return db.query(Session)\
            .filter(Session.client_id == client_id)\
            .order_by(Session.created_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[Session]:
        """根据session_id获取会话"""
        return db.query(Session).filter(Session.session_id == session_id).first()

    @staticmethod
    def cleanup_old_sessions(db: Session):
        """清理过期的会话记录"""
        cutoff_date = datetime.utcnow() - timedelta(days=SESSION_HISTORY_RETENTION_DAYS)
        deleted = db.query(Session)\
            .filter(Session.created_at < cutoff_date)\
            .delete()
        db.commit()
        return deleted


# ==================== 客户端操作 ====================

class ClientManager:
    """客户端管理器"""

    @staticmethod
    def register_or_update_client(
        db: Session,
        client_id: str,
        hostname: str,
        os_info: str
    ) -> ClientConnection:
        """注册或更新客户端"""
        client = db.query(ClientConnection)\
            .filter(ClientConnection.client_id == client_id)\
            .first()

        if client:
            # 更新现有客户端
            client.hostname = hostname
            client.os_info = os_info
            client.is_online = True
            client.last_seen = datetime.utcnow()
        else:
            # 创建新客户端记录
            client = ClientConnection(
                client_id=client_id,
                hostname=hostname,
                os_info=os_info,
                is_online=True,
                last_seen=datetime.utcnow()
            )
            db.add(client)

        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def set_client_offline(db: Session, client_id: str):
        """设置客户端离线"""
        client = db.query(ClientConnection)\
            .filter(ClientConnection.client_id == client_id)\
            .first()
        if client:
            client.is_online = False
            db.commit()

    @staticmethod
    def update_last_seen(db: Session, client_id: str):
        """更新客户端最后活跃时间"""
        client = db.query(ClientConnection)\
            .filter(ClientConnection.client_id == client_id)\
            .first()
        if client:
            client.last_seen = datetime.utcnow()
            db.commit()

    @staticmethod
    def get_online_clients(db: Session) -> List[ClientConnection]:
        """获取所有在线客户端"""
        return db.query(ClientConnection)\
            .filter(ClientConnection.is_online == True)\
            .all()

    @staticmethod
    def get_client(db: Session, client_id: str) -> Optional[ClientConnection]:
        """获取客户端信息"""
        return db.query(ClientConnection)\
            .filter(ClientConnection.client_id == client_id)\
            .first()

    @staticmethod
    def get_all_clients(db: Session) -> List[ClientConnection]:
        """获取所有客户端"""
        return db.query(ClientConnection).all()

    @staticmethod
    def delete_client(db: Session, client_id: str) -> bool:
        """删除客户端记录"""
        client = db.query(ClientConnection)\
            .filter(ClientConnection.client_id == client_id)\
            .first()
        if client:
            db.delete(client)
            db.commit()
            return True
        return False

    @staticmethod
    def delete_offline_clients(db: Session) -> int:
        """删除所有离线客户端"""
        deleted = db.query(ClientConnection)\
            .filter(ClientConnection.is_online == False)\
            .delete()
        db.commit()
        return deleted


# ==================== 用户管理 ====================

class UserManager:
    """用户管理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def generate_api_key() -> str:
        """生成API密钥"""
        return "cmd_" + secrets.token_urlsafe(32)

    @staticmethod
    def generate_token() -> str:
        """生成访问令牌"""
        return secrets.token_urlsafe(64)

    @staticmethod
    def create_user(db: Session, username: str, password: str) -> Optional[User]:
        """创建用户"""
        # 检查用户是否已存在
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return None

        user = User(
            username=username,
            password_hash=UserManager.hash_password(password),
            api_key=UserManager.generate_api_key()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def verify_user(db: Session, username: str, password: str) -> Optional[User]:
        """验证用户凭据"""
        user = db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
        if user and user.password_hash == UserManager.hash_password(password):
            return user
        return None

    @staticmethod
    def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
        """通过API密钥获取用户"""
        return db.query(User).filter(
            User.api_key == api_key,
            User.is_active == True
        ).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def assign_client_to_user(db: Session, username: str, client_id: str, granted_by: str = "system") -> bool:
        """将客户端分配给用户"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False

        # 检查是否已分配
        existing = db.query(UserClient).filter(
            UserClient.user_id == user.id,
            UserClient.client_id == client_id
        ).first()
        if existing:
            return True  # 已分配

        # 创建新的关联
        user_client = UserClient(
            user_id=user.id,
            client_id=client_id,
            granted_by=granted_by
        )
        db.add(user_client)
        db.commit()
        return True

    @staticmethod
    def get_user_clients(db: Session, username: str) -> List[str]:
        """获取用户允许使用的客户端列表"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return []

        user_clients = db.query(UserClient).filter(UserClient.user_id == user.id).all()
        return [uc.client_id for uc in user_clients]

    @staticmethod
    def can_user_use_client(db: Session, username: str, client_id: str) -> bool:
        """检查用户是否可以使用指定客户端"""
        allowed_clients = UserManager.get_user_clients(db, username)
        return client_id in allowed_clients

    @staticmethod
    def revoke_client_access(db: Session, username: str, client_id: str) -> bool:
        """撤销用户对客户端的访问权限"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False

        deleted = db.query(UserClient).filter(
            UserClient.user_id == user.id,
            UserClient.client_id == client_id
        ).delete()
        db.commit()
        return deleted > 0

    @staticmethod
    def remove_client_bindings(db: Session, client_id: str) -> int:
        """移除客户端的所有绑定关系（用于用户切换场景）"""
        deleted = db.query(UserClient).filter(
            UserClient.client_id == client_id
        ).delete()
        db.commit()
        return deleted

    @staticmethod
    def revoke_tokens_for_client(db: Session, client_id: str) -> int:
        """撤销与客户端绑定的用户的所有Token（通过client_id查找绑定的用户）"""
        # 查找与该客户端绑定的所有用户
        user_clients = db.query(UserClient).filter(UserClient.client_id == client_id).all()
        user_ids = [uc.user_id for uc in user_clients]

        if not user_ids:
            return 0

        # 撤销这些用户的所有Token
        deleted = db.query(APIToken).filter(
            APIToken.user_id.in_(user_ids),
            APIToken.is_revoked == False
        ).update({"is_revoked": True}, synchronize_session=False)
        db.commit()
        return deleted

    @staticmethod
    def list_all_users(db: Session) -> List[User]:
        """列出所有用户"""
        return db.query(User).all()


# ==================== Token管理 ====================

class TokenManager:
    """Token管理器"""

    @staticmethod
    def create_token(db: Session, user_id: str, expires_hours: int = 24) -> APIToken:
        """创建访问令牌"""
        # 清理该用户的旧令牌
        db.query(APIToken).filter(
            APIToken.user_id == user_id,
            APIToken.is_revoked == False
        ).delete()

        # 创建新令牌
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        token = APIToken(
            token=UserManager.generate_token(),
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def verify_token(db: Session, token: str) -> Optional[User]:
        """验证令牌并返回用户"""
        token_record = db.query(APIToken).filter(
            APIToken.token == token,
            APIToken.is_revoked == False
        ).first()

        if not token_record:
            return None

        # 检查是否过期
        if token_record.expires_at < datetime.utcnow():
            token_record.is_revoked = True
            db.commit()
            return None

        # 更新最后使用时间
        token_record.last_used = datetime.utcnow()
        db.commit()

        # 获取用户
        user = db.query(User).filter(
            User.id == token_record.user_id,
            User.is_active == True
        ).first()
        return user

    @staticmethod
    def revoke_token(db: Session, token: str) -> bool:
        """撤销令牌"""
        token_record = db.query(APIToken).filter(APIToken.token == token).first()
        if token_record:
            token_record.is_revoked = True
            db.commit()
            return True
        return False
