"""
WebSocket服务端
处理客户端连接和任务分发
"""
import asyncio
import logging
import ssl
from pathlib import Path
from typing import Dict
import websockets
from websockets.server import WebSocketServerProtocol

from shared.models import TaskMessage, TaskResult, ClientRegister
from server.database import SessionManager, ClientManager, get_db
from server.config import WS_PING_INTERVAL, WS_PING_TIMEOUT, USE_TLS, TLS_CERT, TLS_KEY

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket服务端"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
        self.pending_tasks: Dict[str, asyncio.Future] = {}
        self.ssl_context = self._create_ssl_context() if USE_TLS else None

    def _create_ssl_context(self):
        """创建SSL上下文"""
        cert_path = Path(TLS_CERT)
        key_path = Path(TLS_KEY)

        if not cert_path.exists():
            raise FileNotFoundError(f"TLS证书文件不存在: {cert_path}")
        if not key_path.exists():
            raise FileNotFoundError(f"TLS私钥文件不存在: {key_path}")

        # 创建SSL上下文
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(str(cert_path), str(key_path))

        logger.info(f"[TLS] 已加载证书 - {cert_path}")
        return ssl_context

    async def register_client(self, ws: WebSocketServerProtocol, client_id: str, hostname: str, os_info: str):
        """注册客户端"""
        self.connected_clients[client_id] = ws
        db = next(get_db())
        try:
            ClientManager.register_or_update_client(db, client_id, hostname, os_info)
            logger.info(f"[连接] 客户端注册 - ID: {client_id}, 主机名: {hostname}, OS: {os_info}")
            logger.info(f"[连接] 当前在线客户端数: {len(self.connected_clients)}")
        finally:
            db.close()

    async def unregister_client(self, client_id: str):
        """注销客户端"""
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        db = next(get_db())
        try:
            ClientManager.set_client_offline(db, client_id)
            logger.info(f"[连接] 客户端下线 - ID: {client_id}")
            logger.info(f"[连接] 当前在线客户端数: {len(self.connected_clients)}")
        finally:
            db.close()

    async def send_task_to_client(self, client_id: str, task: TaskMessage) -> bool:
        """发送任务给客户端"""
        if client_id not in self.connected_clients:
            logger.warning(f"[任务] 客户端不在线 - ID: {client_id}")
            return False

        try:
            ws = self.connected_clients[client_id]
            await ws.send(task.to_json())
            logger.info(f"[任务] 发送任务 - ID: {task.task_id}, 客户端: {client_id}, 类型: {task.task_type}")
            return True
        except Exception as e:
            logger.error(f"[任务] 发送失败 - ID: {task.task_id}, 客户端: {client_id}, 错误: {e}")
            await self.unregister_client(client_id)
            return False

    async def wait_for_result(self, task_id: str, timeout: int = 300) -> TaskResult:
        """等待任务执行结果"""
        future = asyncio.Future()
        self.pending_tasks[task_id] = future
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"[任务] 超时 - ID: {task_id}")
            raise
        finally:
            self.pending_tasks.pop(task_id, None)

    def handle_task_result(self, result: TaskResult):
        """处理任务结果"""
        if result.task_id in self.pending_tasks:
            future = self.pending_tasks[result.task_id]
            if not future.done():
                future.set_result(result)
            logger.info(f"[任务] 收到结果 - ID: {result.task_id}, 成功: {result.success}, 退出码: {result.exit_code}")
            if not result.success and result.stderr:
                logger.warning(f"[任务] 错误信息 - ID: {result.task_id}, 错误: {result.stderr[:200]}")

        # 保存到数据库
        db = next(get_db())
        try:
            SessionManager.update_session_result(
                db,
                result.task_id,
                result.success,
                {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}
            )
        finally:
            db.close()

    async def handle_client_message(self, ws: WebSocketServerProtocol, client_id: str, message: str):
        """处理客户端消息"""
        try:
            data = message

            # 处理任务结果
            if "task_id" in data and "stdout" in data:
                result = TaskResult.from_json(message)
                self.handle_task_result(result)
            else:
                logger.warning(f"未知消息格式: {message[:100]}")

        except Exception as e:
            logger.error(f"处理客户端消息失败: {e}")

    async def client_handler(self, ws: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        client_id = None
        try:
            # 等待客户端注册消息
            register_msg = await ws.recv()
            register = ClientRegister.from_json(register_msg)
            client_id = register.client_id

            await self.register_client(ws, client_id, register.hostname, register.os_info)

            # 保持连接并处理消息
            async for message in ws:
                await self.handle_client_message(ws, client_id, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端连接断开: {client_id}")
        except Exception as e:
            logger.error(f"客户端处理错误: {e}")
        finally:
            if client_id:
                await self.unregister_client(client_id)

    async def start(self):
        """启动WebSocket服务"""
        protocol = "WSS (TLS加密)" if self.ssl_context else "WS (非加密)"
        logger.info(f"WebSocket服务启动在 {self.host}:{self.port} - 协议: {protocol}")

        # 构建服务参数
        if self.ssl_context:
            # TLS加密模式
            async with websockets.serve(
                self.client_handler,
                self.host,
                self.port,
                ping_interval=WS_PING_INTERVAL,
                ping_timeout=WS_PING_TIMEOUT,
                ssl=self.ssl_context
            ):
                await asyncio.Future()  # 永久运行
        else:
            # 普通模式
            async with websockets.serve(
                self.client_handler,
                self.host,
                self.port,
                ping_interval=WS_PING_INTERVAL,
                ping_timeout=WS_PING_TIMEOUT
            ):
                await asyncio.Future()  # 永久运行


# 全局WebSocket服务器实例（使用类变量以便跨线程访问）
class _WSServerHolder:
    _instance: WebSocketServer = None

    @classmethod
    def set_instance(cls, instance: WebSocketServer):
        cls._instance = instance

    @classmethod
    def get_instance(cls) -> WebSocketServer:
        return cls._instance


def get_ws_server() -> WebSocketServer:
    """获取WebSocket服务器实例"""
    return _WSServerHolder.get_instance()


def set_ws_server(instance: WebSocketServer):
    """设置WebSocket服务器实例"""
    _WSServerHolder.set_instance(instance)
