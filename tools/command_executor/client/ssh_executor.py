"""
SSH执行模块
使用paramiko执行SSH命令
"""
import paramiko
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SSHExecutor:
    """SSH命令执行器"""

    @staticmethod
    def execute(
        host: str,
        port: int,
        username: str,
        password: str,
        command: str,
        timeout: int = 30
    ) -> Tuple[bool, str, str, int]:
        """
        执行SSH命令

        返回: (成功, stdout, stderr, 退出码)
        """
        client = None
        try:
            # 创建SSH客户端
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 连接服务器
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False
            )

            # 执行命令
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

            # 获取输出
            stdout_str = stdout.read().decode('utf-8', errors='replace')
            stderr_str = stderr.read().decode('utf-8', errors='replace')
            exit_code = stdout.channel.recv_exit_status()

            success = exit_code == 0

            logger.info(f"SSH命令执行完成: host={host}, command={command[:50]}, exit_code={exit_code}")

            return success, stdout_str, stderr_str, exit_code

        except paramiko.AuthenticationException:
            logger.error(f"SSH认证失败: {username}@{host}")
            return False, "", "认证失败", -1

        except paramiko.SSHException as e:
            logger.error(f"SSH连接错误: {e}")
            return False, "", f"SSH错误: {str(e)}", -1

        except TimeoutError:
            logger.error(f"SSH连接超时: {host}:{port}")
            return False, "", "连接超时", -1

        except Exception as e:
            logger.error(f"SSH执行错误: {e}")
            return False, "", f"执行错误: {str(e)}", -1

        finally:
            if client:
                client.close()
