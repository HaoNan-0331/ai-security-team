"""
API认证模块
提供用户登录、Token验证等认证功能
"""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

from server.database import get_db, Session, UserManager, TokenManager

# HTTP Bearer认证方案
security = HTTPBearer()


# ==================== 请求/响应模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    username: str
    api_key: str


# ==================== 认证依赖 ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> str:
    """
    获取当前认证用户
    从Authorization头中提取并验证Token
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证凭据")

    token = credentials.credentials
    user = TokenManager.verify_token(db, token)

    if not user:
        raise HTTPException(status_code=401, detail="无效或过期的Token")

    return user.username


async def verify_client_access(username: str, client_id: str, db: Session = Depends(get_db)):
    """
    验证用户是否有权使用指定客户端
    """
    if not UserManager.can_user_use_client(db, username, client_id):
        raise HTTPException(
            status_code=403,
            detail=f"用户 '{username}' 无权使用客户端 '{client_id}'"
        )


def get_db_session():
    """获取数据库会话依赖"""
    yield from get_db()


# ==================== 登录端点 ====================

async def login_user(login_data: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    用户登录获取Token

    Args:
        login_data: 登录凭据
        db: 数据库会话

    Returns:
        LoginResponse: 包含Token和API密钥

    Raises:
        HTTPException: 认证失败时
    """
    # 验证用户凭据
    user = UserManager.verify_user(db, login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    # 创建访问令牌（24小时有效）
    token_record = TokenManager.create_token(db, user.id, expires_hours=24)

    return LoginResponse(
        access_token=token_record.token,
        token_type="bearer",
        expires_in=24 * 3600,
        username=user.username,
        api_key=user.api_key
    )


# ==================== 权限检查装饰器 ====================

def require_auth(username: str = Depends(get_current_user)):
    """
    要求认证的装饰器
    依赖注入，自动验证Token并返回用户名
    """
    return username


def require_client_access(client_id: str, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    要求客户端访问权限的装饰器
    验证用户是否有权使用指定的客户端
    """
    if not UserManager.can_user_use_client(db, username, client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权使用客户端 '{client_id}'"
        )
    return username, client_id
