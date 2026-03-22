"""
REST API服务端
提供API接口供用户调用
"""
import uuid
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn

from shared.models import SSHParams, HTTPParams
from server.database import SessionManager, ClientManager, get_db, UserManager, TokenManager
from server.websocket_server import get_ws_server
from server.auth import LoginRequest, LoginResponse, get_current_user, verify_client_access, login_user
from server.config import USE_TLS, TLS_CERT, TLS_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ==================== 请求/响应模型 ====================

class SSHRequest(BaseModel):
    """SSH执行请求"""
    client_id: str
    host: str
    port: int = 22
    username: str
    password: str
    command: str
    timeout: int = 30


class HTTPRequest(BaseModel):
    """HTTP请求"""
    client_id: str
    url: str
    method: str = "GET"
    headers: dict = {}
    body: Optional[str] = None
    timeout: int = 30


class LocalRequest(BaseModel):
    """本地命令执行请求"""
    client_id: str
    command: str
    timeout: int = 30
    encoding: Optional[str] = None


class TelnetRequest(BaseModel):
    """Telnet执行请求"""
    client_id: str
    host: str
    port: int = 23
    username: Optional[str] = None
    password: Optional[str] = None
    command: str = ""
    timeout: int = 30
    login_prompt: str = "login:"
    password_prompt: str = "Password:"
    shell_prompt: Optional[str] = None


class TaskResponse(BaseModel):
    """任务响应"""
    session_id: str
    message: str


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    client_id: str
    task_type: str
    request_data: dict
    response_data: Optional[dict]
    success: bool
    error_message: Optional[str]
    created_at: str


class ClientInfo(BaseModel):
    """客户端信息"""
    client_id: str
    hostname: str
    os_info: str
    is_online: bool
    last_seen: str
    first_connected: str


class ExecuteResult(BaseModel):
    """执行结果"""
    success: bool
    stdout: str
    stderr: str
    exit_code: int


# ==================== FastAPI应用 ====================

app = FastAPI(
    title="Command Executor API",
    description="分布式命令执行系统API - 需要认证",
    version="2.0.0"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 安全HTTP头中间件 ====================

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """添加安全HTTP响应头"""
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return response


# ==================== 公开API路由（无需认证）====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Command Executor API",
        "version": "2.0.0",
        "status": "running",
        "auth_required": True
    }


@app.post("/api/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    用户登录获取Token

    使用用户名和密码登录，获取访问Token。
    Token有效期为24小时，所有后续API调用需要在Header中携带：
    Authorization: Bearer <token>
    """
    db = next(get_db())
    try:
        return await login_user(login_data, db)
    finally:
        db.close()


# ==================== 需要认证的API路由 ====================

@app.post("/api/ssh/execute", response_model=TaskResponse)
async def execute_ssh(
    request: SSHRequest,
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    执行SSH命令（需要认证）

    通过指定的客户端远程执行SSH命令。
    用户必须有权限使用指定的客户端。
    """
    # 验证用户对客户端的访问权限
    if not UserManager.can_user_use_client(db, username, request.client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权使用客户端 '{request.client_id}'"
        )

    # 检查客户端是否在线
    client = ClientManager.get_client(db, request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"客户端不存在: {request.client_id}")
    if not client.is_online:
        raise HTTPException(status_code=400, detail=f"客户端不在线: {request.client_id}")

    # 创建任务
    session_id = str(uuid.uuid4())

    from shared.models import TaskMessage
    task = TaskMessage(
        task_id=session_id,
        client_id=request.client_id,
        task_type="ssh",
        data={
            "host": request.host,
            "port": request.port,
            "username": request.username,
            "password": request.password,
            "command": request.command,
            "timeout": request.timeout
        }
    )

    # 创建会话记录
    SessionManager.create_session(
        db,
        session_id,
        request.client_id,
        "ssh",
        task.data
    )

    # 发送任务到客户端
    ws_server = get_ws_server()
    success = await ws_server.send_task_to_client(request.client_id, task)

    if not success:
        raise HTTPException(status_code=500, detail="发送任务失败")

    return TaskResponse(
        session_id=session_id,
        message="任务已发送，等待执行结果"
    )


@app.post("/api/http/execute", response_model=TaskResponse)
async def execute_http(
    request: HTTPRequest,
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    执行HTTP请求（需要认证）

    通过指定的客户端发送HTTP请求。
    用户必须有权限使用指定的客户端。
    """
    # 验证用户对客户端的访问权限
    if not UserManager.can_user_use_client(db, username, request.client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权使用客户端 '{request.client_id}'"
        )

    # 检查客户端是否在线
    client = ClientManager.get_client(db, request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"客户端不存在: {request.client_id}")
    if not client.is_online:
        raise HTTPException(status_code=400, detail=f"客户端不在线: {request.client_id}")

    # 验证HTTP方法
    valid_methods = ["GET", "POST", "PUT", "DELETE"]
    if request.method.upper() not in valid_methods:
        raise HTTPException(status_code=400, detail=f"无效的HTTP方法: {request.method}")

    # 创建任务
    session_id = str(uuid.uuid4())

    from shared.models import TaskMessage
    task = TaskMessage(
        task_id=session_id,
        client_id=request.client_id,
        task_type="http",
        data={
            "url": request.url,
            "method": request.method.upper(),
            "headers": request.headers,
            "body": request.body,
            "timeout": request.timeout
        }
    )

    # 创建会话记录
    SessionManager.create_session(
        db,
        session_id,
        request.client_id,
        "http",
        task.data
    )

    # 发送任务到客户端
    ws_server = get_ws_server()
    success = await ws_server.send_task_to_client(request.client_id, task)

    if not success:
        raise HTTPException(status_code=500, detail="发送任务失败")

    return TaskResponse(
        session_id=session_id,
        message="任务已发送，等待执行结果"
    )


@app.post("/api/local/execute", response_model=TaskResponse)
async def execute_local_command(
    request: LocalRequest,
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    执行客户端本地命令（需要认证）

    用于系统巡检、配置查看、故障诊断等。
    用户必须有权限使用指定的客户端。
    """
    # 验证用户对客户端的访问权限
    if not UserManager.can_user_use_client(db, username, request.client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权使用客户端 '{request.client_id}'"
        )

    # 检查客户端是否在线
    client = ClientManager.get_client(db, request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"客户端不存在: {request.client_id}")
    if not client.is_online:
        raise HTTPException(status_code=400, detail=f"客户端不在线: {request.client_id}")

    # 创建任务
    session_id = str(uuid.uuid4())

    from shared.models import TaskMessage
    task = TaskMessage(
        task_id=session_id,
        client_id=request.client_id,
        task_type="local",
        data={
            "command": request.command,
            "timeout": request.timeout,
            "encoding": request.encoding
        }
    )

    # 创建会话记录
    SessionManager.create_session(
        db,
        session_id,
        request.client_id,
        "local",
        task.data
    )

    # 发送任务到客户端
    ws_server = get_ws_server()
    success = await ws_server.send_task_to_client(request.client_id, task)

    if not success:
        raise HTTPException(status_code=500, detail="发送任务失败")

    return TaskResponse(
        session_id=session_id,
        message="本地命令任务已发送"
    )


@app.post("/api/telnet/execute", response_model=TaskResponse)
async def execute_telnet(
    request: TelnetRequest,
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    执行Telnet命令（需要认证）

    通过指定的客户端执行Telnet命令。
    适用于不支持SSH的旧设备。
    用户必须有权限使用指定的客户端。
    """
    # 验证用户对客户端的访问权限
    if not UserManager.can_user_use_client(db, username, request.client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权使用客户端 '{request.client_id}'"
        )

    # 检查客户端是否在线
    client = ClientManager.get_client(db, request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"客户端不存在: {request.client_id}")
    if not client.is_online:
        raise HTTPException(status_code=400, detail=f"客户端不在线: {request.client_id}")

    # 创建任务
    session_id = str(uuid.uuid4())

    from shared.models import TaskMessage
    task = TaskMessage(
        task_id=session_id,
        client_id=request.client_id,
        task_type="telnet",
        data={
            "host": request.host,
            "port": request.port,
            "username": request.username,
            "password": request.password,
            "command": request.command,
            "timeout": request.timeout,
            "login_prompt": request.login_prompt,
            "password_prompt": request.password_prompt,
            "shell_prompt": request.shell_prompt
        }
    )

    # 创建会话记录
    SessionManager.create_session(
        db,
        session_id,
        request.client_id,
        "telnet",
        task.data
    )

    # 发送任务到客户端
    ws_server = get_ws_server()
    success = await ws_server.send_task_to_client(request.client_id, task)

    if not success:
        raise HTTPException(status_code=500, detail="发送任务失败")

    return TaskResponse(
        session_id=session_id,
        message="Telnet任务已发送"
    )


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取会话详情（需要认证）"""
    session = SessionManager.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    # 验证用户对客户端的访问权限
    if not UserManager.can_user_use_client(db, username, session.client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权访问客户端 '{session.client_id}' 的数据"
        )

    return SessionResponse(
        session_id=session.session_id,
        client_id=session.client_id,
        task_type=session.task_type,
        request_data=session.request_data,
        response_data=session.response_data,
        success=session.success,
        error_message=session.error_message,
        created_at=session.created_at.isoformat()
    )


@app.get("/api/sessions/client/{client_id}", response_model=List[SessionResponse])
async def get_client_sessions(
    client_id: str,
    limit: int = 100,
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取客户端的会话历史（需要认证）"""
    # 验证用户对客户端的访问权限
    if not UserManager.can_user_use_client(db, username, client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权访问客户端 '{client_id}' 的数据"
        )

    sessions = SessionManager.get_client_sessions(db, client_id, limit)
    return [
        SessionResponse(
            session_id=s.session_id,
            client_id=s.client_id,
            task_type=s.task_type,
            request_data=s.request_data,
            response_data=s.response_data,
            success=s.success,
            error_message=s.error_message,
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]


@app.get("/api/clients", response_model=List[ClientInfo])
async def list_clients(
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取当前用户有权限使用的客户端列表（需要认证）"""
    # 获取用户允许使用的客户端ID列表
    allowed_client_ids = UserManager.get_user_clients(db, username)

    # 获取所有客户端并过滤
    all_clients = ClientManager.get_all_clients(db)
    filtered_clients = [
        c for c in all_clients if c.client_id in allowed_client_ids
    ]

    return [
        ClientInfo(
            client_id=c.client_id,
            hostname=c.hostname,
            os_info=c.os_info,
            is_online=c.is_online,
            last_seen=c.last_seen.isoformat(),
            first_connected=c.first_connected.isoformat()
        )
        for c in filtered_clients
    ]


@app.get("/api/clients/online", response_model=List[ClientInfo])
async def list_online_clients(
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取当前用户有权限使用的在线客户端列表（需要认证）"""
    # 获取用户允许使用的客户端ID列表
    allowed_client_ids = UserManager.get_user_clients(db, username)

    # 获取在线客户端并过滤
    online_clients = ClientManager.get_online_clients(db)
    filtered_clients = [
        c for c in online_clients if c.client_id in allowed_client_ids
    ]

    return [
        ClientInfo(
            client_id=c.client_id,
            hostname=c.hostname,
            os_info=c.os_info,
            is_online=c.is_online,
            last_seen=c.last_seen.isoformat(),
            first_connected=c.first_connected.isoformat()
        )
        for c in filtered_clients
    ]


@app.get("/api/clients/{client_id}", response_model=ClientInfo)
async def get_client_info(
    client_id: str,
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取客户端详情（需要认证）"""
    # 验证用户对客户端的访问权限
    if not UserManager.can_user_use_client(db, username, client_id):
        raise HTTPException(
            status_code=403,
            detail=f"您无权访问客户端 '{client_id}'"
        )

    client = ClientManager.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"客户端不存在: {client_id}")

    return ClientInfo(
        client_id=client.client_id,
        hostname=client.hostname,
        os_info=client.os_info,
        is_online=client.is_online,
        last_seen=client.last_seen.isoformat(),
        first_connected=client.first_connected.isoformat()
    )


@app.get("/api/user/info")
async def get_user_info(
    username: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取当前用户信息（需要认证）"""
    user = UserManager.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取用户的客户端列表
    client_ids = UserManager.get_user_clients(db, username)

    return {
        "username": user.username,
        "api_key": user.api_key,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "allowed_clients": client_ids,
        "clients_count": len(client_ids)
    }


def run_api_server(host: str = "0.0.0.0", port: int = 8080):
    """运行API服务器"""
    import asyncio

    # SSL 配置
    ssl_kwargs = {}
    if USE_TLS:
        import os
        cert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), TLS_CERT)
        key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), TLS_KEY)

        if os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_kwargs = {
                "ssl_keyfile": key_path,
                "ssl_certfile": cert_path
            }
            logger.info(f"API服务启用TLS加密，证书: {cert_path}")
        else:
            logger.warning(f"TLS证书文件不存在，将以HTTP模式运行")

    # 使用Config和Server方式启动，兼容Python 3.6在线程中运行
    config = uvicorn.Config(app, host=host, port=port, log_level="info", **ssl_kwargs)
    server = uvicorn.Server(config)

    # 获取当前事件循环并运行
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())
