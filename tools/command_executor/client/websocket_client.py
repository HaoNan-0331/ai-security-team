"""
WebSocket客户端
连接到服务端并接收任务
"""
import asyncio
import logging
import platform
import socket
import ssl
import sys
import uuid
from pathlib import Path
import websockets.client
from websockets.client import WebSocketClientProtocol

from shared.models import TaskMessage, TaskResult, ClientRegister
from client.config import ConfigManager, get_app_dir, get_device_fingerprint
from client.database import db
from client.ssh_executor import SSHExecutor
from client.http_executor import HTTPExecutor
from client.local_executor import LocalExecutor
from client.telnet_executor import TelnetExecutor

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket客户端"""

    def __init__(self, access_token: str = None, username: str = None):
        self.config = ConfigManager.load_config()
        self.client_id = self._generate_client_id()
        self.running = False
        self.access_token = access_token  # API访问Token
        self.username = username  # 登录用户名
        self.ssl_context = self._create_ssl_context() if self.config.use_tls else None

    def _create_ssl_context(self):
        """创建SSL上下文（自签名证书兼容，增强与旧版本服务器的兼容性）"""
        # 使用 TLS 1.2 协议以提高与旧版本服务器的兼容性
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # 尝试设置密码套件为更宽松的配置
        try:
            ssl_context.set_ciphers('HIGH:!DH:!aNULL')
        except (ssl.SSLError, AttributeError):
            pass

        logger.info("[TLS] 已配置SSL上下文（允许自签名证书，使用TLS 1.2）")
        return ssl_context

    def _generate_client_id(self) -> str:
        """生成客户端识别码（与设备绑定）"""
        # 获取当前设备指纹
        current_fingerprint = get_device_fingerprint()
        logger.info(f"[设备] 当前设备指纹: {current_fingerprint}")

        # 客户端信息文件存储格式: 设备指纹|识别码
        client_info_file = get_app_dir() / ".client_id"

        if client_info_file.exists():
            with open(client_info_file, "r") as f:
                content = f.read().strip()
                parts = content.split("|")
                if len(parts) == 2:
                    stored_fingerprint, stored_client_id = parts
                    if stored_fingerprint == current_fingerprint:
                        logger.info(f"[设备] 设备未变化，使用原识别码: {stored_client_id}")
                        return stored_client_id
                    else:
                        logger.warning(f"[设备] 检测到设备变化!")
                        logger.warning(f"[设备] 原设备指纹: {stored_fingerprint}")
                        logger.warning(f"[设备] 新设备指纹: {current_fingerprint}")

        # 设备变化或首次运行，生成新识别码
        new_client_id = str(uuid.uuid4())[:8].upper()
        # 保存设备指纹和识别码
        with open(client_info_file, "w") as f:
            f.write(f"{current_fingerprint}|{new_client_id}")

        logger.info(f"[设备] 已生成新识别码: {new_client_id}")
        return new_client_id

    def get_client_id(self) -> str:
        """获取客户端ID"""
        return self.client_id

    def get_system_info(self) -> tuple:
        """获取系统信息"""
        hostname = socket.gethostname()
        os_info = f"{platform.system()} {platform.release()}"
        return hostname, os_info

    async def execute_task(self, task: TaskMessage) -> TaskResult:
        """执行任务"""
        logger.info(f"[任务] 开始执行 - ID: {task.task_id}, 类型: {task.task_type}")

        try:
            if task.task_type == "ssh":
                data = task.data
                logger.info(f"[任务] SSH执行 - 目标: {data['host']}:{data['port']}, 用户: {data['username']}, 命令: {data['command'][:50]}...")
                return await self._execute_ssh(task)
            elif task.task_type == "http":
                data = task.data
                logger.info(f"[任务] HTTP请求 - URL: {data['url']}, 方法: {data['method']}")
                return await self._execute_http(task)
            elif task.task_type == "local":
                data = task.data
                logger.info(f"[任务] 本地命令 - 命令: {data['command'][:100]}...")
                return await self._execute_local(task)
            elif task.task_type == "telnet":
                data = task.data
                logger.info(f"[任务] Telnet执行 - 目标: {data['host']}:{data['port']}, 命令: {data['command'][:50]}...")
                return await self._execute_telnet(task)
            else:
                logger.warning(f"[任务] 未知类型: {task.task_type}")
                return TaskResult(
                    task_id=task.task_id,
                    client_id=task.client_id,
                    success=False,
                    stdout="",
                    stderr=f"未知任务类型: {task.task_type}",
                    exit_code=-1
                )

        except Exception as e:
            logger.error(f"[任务] 执行异常 - ID: {task.task_id}, 错误: {e}")
            return TaskResult(
                task_id=task.task_id,
                client_id=task.client_id,
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1
            )

    async def _execute_ssh(self, task: TaskMessage) -> TaskResult:
        """执行SSH任务"""
        data = task.data

        # 在线程池中执行SSH命令（阻塞操作）
        loop = asyncio.get_event_loop()
        success, stdout, stderr, exit_code = await loop.run_in_executor(
            None,
            SSHExecutor.execute,
            data["host"],
            data["port"],
            data["username"],
            data["password"],
            data["command"],
            data.get("timeout", 30)
        )

        return TaskResult(
            task_id=task.task_id,
            client_id=task.client_id,
            success=success,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code
        )

    async def _execute_http(self, task: TaskMessage) -> TaskResult:
        """执行HTTP任务"""
        data = task.data

        # 在线程池中执行HTTP请求（阻塞操作）
        loop = asyncio.get_event_loop()
        success, response_body, error_msg, status_code = await loop.run_in_executor(
            None,
            HTTPExecutor.execute,
            data["url"],
            data["method"],
            data.get("headers"),
            data.get("body"),
            data.get("timeout", 30)
        )

        # 将状态码作为"退出码"
        return TaskResult(
            task_id=task.task_id,
            client_id=task.client_id,
            success=success,
            stdout=response_body,
            stderr=error_msg,
            exit_code=status_code
        )

    async def _execute_local(self, task: TaskMessage) -> TaskResult:
        """执行本地命令任务"""
        data = task.data

        # 在线程池中执行本地命令（阻塞操作）
        loop = asyncio.get_event_loop()
        success, stdout, stderr, exit_code = await loop.run_in_executor(
            None,
            LocalExecutor.execute,
            data["command"],
            data.get("timeout", 30),
            data.get("encoding")
        )

        return TaskResult(
            task_id=task.task_id,
            client_id=task.client_id,
            success=success,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code
        )

    async def _execute_telnet(self, task: TaskMessage) -> TaskResult:
        """执行Telnet任务"""
        data = task.data

        # 在线程池中执行Telnet命令（阻塞操作）
        loop = asyncio.get_event_loop()
        success, stdout, stderr, exit_code = await loop.run_in_executor(
            None,
            TelnetExecutor.execute,
            data["host"],
            data["port"],
            data.get("username"),
            data.get("password"),
            data["command"],
            data.get("timeout", 30),
            data.get("login_prompt", "login:"),
            data.get("password_prompt", "Password:"),
            data.get("shell_prompt")
        )

        return TaskResult(
            task_id=task.task_id,
            client_id=task.client_id,
            success=success,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code
        )

    async def handle_task(self, ws: WebSocketClientProtocol, task: TaskMessage):
        """处理任务"""
        # 保存到本地数据库
        db.save_session(
            task.task_id,
            task.task_type,
            task.data,
            None,
            False
        )

        # 执行任务
        result = await self.execute_task(task)

        # 更新本地数据库
        db.save_session(
            task.task_id,
            task.task_type,
            task.data,
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code
            },
            result.success,
            result.stderr if not result.success else None
        )

        # 发送结果回服务端
        await ws.send(result.to_json())
        logger.info(f"[任务] 结果已发送 - ID: {task.task_id}, 成功: {result.success}, 退出码: {result.exit_code}")

    async def connect(self):
        """连接到服务端"""
        self.running = True

        # 构建WebSocket URL
        protocol = "wss" if self.config.use_tls else "ws"
        ws_url = f"{protocol}://{self.config.server_host}:{self.config.server_port}"

        logger.info(f"[连接] 正在连接服务端 - URL: {ws_url}")

        # 准备连接参数
        connect_kwargs = {
            "ping_interval": 30,
            "ping_timeout": 10
        }

        # 如果使用TLS，添加SSL上下文
        if self.ssl_context:
            connect_kwargs["ssl"] = self.ssl_context

        try:
            async with websockets.client.connect(
                ws_url,
                **connect_kwargs
            ) as ws:
                # 发送注册消息（包含用户名和Token）
                hostname, os_info = self.get_system_info()
                register = ClientRegister(
                    client_id=self.client_id,
                    hostname=hostname,
                    os_info=os_info,
                    username=self.username,
                    access_token=self.access_token
                )
                await ws.send(register.to_json())
                logger.info(f"[连接] 客户端已注册 - ID: {self.client_id}, 用户: {self.username}, 主机: {hostname}, OS: {os_info}")

                # 接收并处理任务
                async for message in ws:
                    try:
                        task = TaskMessage.from_json(message)
                        await self.handle_task(ws, task)
                    except Exception as e:
                        logger.error(f"[任务] 处理消息异常 - 错误: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("[连接] 与服务端连接断开")
        except Exception as e:
            logger.error(f"[连接] 连接异常 - 错误: {e}")
        finally:
            self.running = False

    async def run(self):
        """运行客户端（带自动重连）"""
        retry_delay = 5

        while True:
            try:
                await self.connect()
            except KeyboardInterrupt:
                logger.info("[连接] 客户端正在关闭...")
                break
            except Exception as e:
                logger.error(f"[连接] 客户端异常 - 错误: {e}")

            # 如果不是手动中断，等待后重连
            if self.running:
                logger.info(f"[连接] 等待 {retry_delay} 秒后重连...")
                await asyncio.sleep(retry_delay)

    def get_client_id(self) -> str:
        """获取客户端识别码"""
        return self.client_id
