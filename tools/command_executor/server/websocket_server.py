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
from server.database import SessionManager, ClientManager, get_db, UserManager, TokenManager
from server.config import WS_PING_INTERVAL, WS_PING_TIMEOUT, USE_TLS, TLS_CERT, TLS_KEY, CLIENT_OFFLINE_TIMEOUT, CLIENT_CLEANUP_INTERVAL

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket服务端"""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
        self.pending_tasks: Dict[str, asyncio.Future] = {}  # task_id -> Future
        self.ssl_context = self._create_ssl_context() if USE_TLS else None
        self.cleanup_task = None  # 清理任务引用

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

    async def register_client(self, ws: WebSocketServerProtocol, client_id: str, hostname: str, os_info: str, username: str = None, access_token: str = None):
        """注册客户端"""
        # 验证用户身份（如果提供了用户名和Token）
        if username and access_token:
            db = next(get_db())
            try:
                # 验证Token
                user = TokenManager.verify_token(db, access_token)
                if not user or user.username != username:
                    logger.warning(f"[连接] 客户端认证失败 - ID: {client_id}, 用户: {username}")
                    await ws.close(1008, "认证失败：无效的Token或用户名不匹配")
                    return

                # 验证用户是否有权使用此客户端
                if not UserManager.can_user_use_client(db, username, client_id):
                    # 自动绑定：用户首次使用此客户端，自动分配权限
                    # 先检查并移除该客户端的其他绑定关系（防止一台设备绑定多个用户）
                    removed_count = UserManager.remove_client_bindings(db, client_id)
                    if removed_count > 0:
                        logger.info(f"[自动绑定] 已移除客户端 '{client_id}' 的 {removed_count} 个旧绑定关系（用户切换）")

                    logger.info(f"[自动绑定] 用户 '{username}' 首次使用客户端 '{client_id}'，正在自动绑定...")
                    success = UserManager.assign_client_to_user(db, username, client_id, granted_by="auto_bind")
                    if success:
                        logger.info(f"[自动绑定] 成功 - 用户: {username}, 客户端: {client_id}")
                    else:
                        logger.warning(f"[自动绑定] 失败 - 用户: {username}, 客户端: {client_id}")
                        await ws.close(1008, f"认证失败：无法自动绑定客户端 '{client_id}' 给用户 '{username}'")
                        return

                logger.info(f"[连接] 客户端认证成功 - ID: {client_id}, 用户: {username}")
            finally:
                db.close()
        else:
            # 没有提供认证信息，记录警告（向后兼容）
            logger.warning(f"[连接] 客户端未提供认证信息 - ID: {client_id}")

        # 注册客户端连接
        self.connected_clients[client_id] = ws
        db = next(get_db())
        try:
            ClientManager.register_or_update_client(db, client_id, hostname, os_info)
            logger.info(f"[连接] 客户端注册 - ID: {client_id}, 主机名: {hostname}, OS: {os_info}, 用户: {username or '未指定'}")
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

    async def disconnect_client(self, client_id: str, reason: str = "管理员强制断开"):
        """强制断开指定客户端的连接"""
        if client_id in self.connected_clients:
            try:
                ws = self.connected_clients[client_id]
                await ws.close(1008, reason)
                logger.info(f"[强制断开] 客户端 '{client_id}' 已被断开 - 原因: {reason}")
                return True
            except Exception as e:
                logger.error(f"[强制断开] 断开客户端 '{client_id}' 失败: {e}")
                return False
        return False

    async def check_deleted_clients(self):
        """检查并断开已被删除的在线客户端"""
        if not self.connected_clients:
            return

        db = next(get_db())
        try:
            # 获取所有在线客户端的client_id
            online_client_ids = list(self.connected_clients.keys())

            # 检查这些客户端是否在数据库中存在
            from server.database import ClientConnection
            for client_id in online_client_ids:
                client = db.query(ClientConnection).filter(
                    ClientConnection.client_id == client_id
                ).first()

                if not client:
                    # 客户端已被删除，强制断开连接
                    logger.info(f"[检测删除] 客户端 '{client_id}' 已从数据库删除，正在断开连接...")
                    await self.disconnect_client(client_id, "客户端已被管理员删除")

        except Exception as e:
            logger.error(f"[检测删除] 检查已删除客户端失败: {e}")
        finally:
            db.close()

    def cleanup_offline_clients(self):
        """清理离线超过阈值的客户端绑定"""
        from datetime import datetime, timedelta

        db = next(get_db())
        try:
            # 计算超时阈值时间
            threshold = datetime.now() - timedelta(minutes=CLIENT_OFFLINE_TIMEOUT)

            # 查询离线超过阈值的客户端
            query = """
                SELECT DISTINCT uc.client_id, u.username as bound_user
                FROM user_clients uc
                JOIN client_connections cc ON uc.client_id = cc.client_id
                JOIN users u ON uc.user_id = u.id
                WHERE cc.is_online = 0
                AND datetime(cc.last_seen) < ?
            """

            cursor = db.cursor()
            cursor.execute(query, (threshold.strftime('%Y-%m-%d %H:%M:%S'),))
            offline_clients = cursor.fetchall()

            if offline_clients:
                logger.info(f"[自动注销] 发现 {len(offline_clients)} 个客户端离线超过 {CLIENT_OFFLINE_TIMEOUT} 分钟")
                for client_id, username in offline_clients:
                    # 删除绑定关系
                    cursor.execute(
                        "DELETE FROM user_clients WHERE client_id = ?",
                        (client_id,)
                    )
                    logger.info(f"[自动注销] 已删除客户端 '{client_id}' 与用户 '{username}' 的绑定关系（离线超时）")

                db.commit()

        except Exception as e:
            logger.error(f"[自动注销] 清理离线客户端失败: {e}")
            db.rollback()
        finally:
            db.close()

    async def start_cleanup_task(self):
        """启动定期清理任务"""
        while True:
            try:
                await asyncio.sleep(CLIENT_CLEANUP_INTERVAL)
                self.cleanup_offline_clients()
                await self.check_deleted_clients()
            except asyncio.CancelledError:
                logger.info("[自动注销] 清理任务已取消")
                break
            except Exception as e:
                logger.error(f"[自动注销] 清理任务异常: {e}")

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
        """处理客户端连接（兼容 websockets 9.x）"""
        client_id = None
        try:
            # 等待客户端注册消息
            register_msg = await ws.recv()
            register = ClientRegister.from_json(register_msg)
            client_id = register.client_id

            # 注册客户端（包含用户名和Token验证）
            await self.register_client(
                ws,
                client_id,
                register.hostname,
                register.os_info,
                register.username,
                register.access_token
            )

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
        logger.info(f"[自动注销] 客户端离线超时: {CLIENT_OFFLINE_TIMEOUT} 分钟")
        logger.info(f"[自动注销] 清理间隔: {CLIENT_CLEANUP_INTERVAL} 秒")

        # 启动后台清理任务（兼容 Python 3.6）
        self.cleanup_task = asyncio.ensure_future(self.start_cleanup_task())

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
