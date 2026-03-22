"""
本地命令执行模块
纯粹的执行器 - 不做任何权限检查，只负责执行命令并返回结果
"""

import subprocess
import platform
import logging
import time
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class LocalExecutor:
    """本地命令执行器 - 纯粹执行器"""

    def __init__(self):
        """初始化执行器"""
        self.platform = platform.system()
        logger.info(f"本地命令执行器初始化 - 平台: {self.platform}")

    @staticmethod
    def _get_default_encoding() -> str:
        """获取当前平台默认编码"""
        if platform.system() == "Windows":
            return "gbk"  # Windows CMD 默认 GBK
        return "utf-8"

    @staticmethod
    def execute(
        command: str,
        timeout: int = 30,
        encoding: Optional[str] = None
    ) -> Tuple[bool, str, str, int]:
        """
        执行本地命令

        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
            encoding: 输出编码（None 则自动检测平台默认编码）

        Returns:
            (成功, stdout, stderr, 退出码)
        """
        # 确定编码
        output_encoding = encoding or LocalExecutor._get_default_encoding()

        logger.info(f"执行本地命令 - 平台: {platform.system()}, 命令: {command[:100]}...")

        try:
            if platform.system() == "Windows":
                success, stdout, stderr, exit_code = LocalExecutor._execute_windows(
                    command, timeout, output_encoding
                )
            else:
                success, stdout, stderr, exit_code = LocalExecutor._execute_posix(
                    command, timeout, output_encoding
                )

            logger.info(
                f"本地命令执行完成 - 退出码: {exit_code}, "
                f"输出长度: {len(stdout)}, 错误长度: {len(stderr)}"
            )

            return success, stdout, stderr, exit_code

        except Exception as e:
            logger.error(f"本地命令执行异常 - {e}")
            return False, "", str(e), -1

    @staticmethod
    def _execute_windows(
        command: str,
        timeout: int,
        encoding: str
    ) -> Tuple[bool, str, str, int]:
        """执行 Windows 命令"""
        try:
            process = subprocess.Popen(
                ["cmd", "/c", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=False  # 使用字节模式，手动解码
            )

            try:
                # 等待结果（带超时）
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)

                # 解码输出
                stdout = stdout_bytes.decode(encoding, errors='replace')
                stderr = stderr_bytes.decode(encoding, errors='replace')
                exit_code = process.returncode

                return exit_code == 0, stdout, stderr, exit_code

            except subprocess.TimeoutExpired:
                # 超时，强制终止
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
                stdout = stdout_bytes.decode(encoding, errors='replace') if stdout_bytes else ""
                stderr = f"命令执行超时 ({timeout}秒)"
                return False, stdout, stderr, -1

        except FileNotFoundError:
            return False, "", "命令未找到", -1
        except Exception as e:
            return False, "", f"执行错误: {str(e)}", -1

    @staticmethod
    def _execute_posix(
        command: str,
        timeout: int,
        encoding: str
    ) -> Tuple[bool, str, str, int]:
        """执行 Linux/macOS 命令"""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=False
            )

            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)

                stdout = stdout_bytes.decode(encoding, errors='replace')
                stderr = stderr_bytes.decode(encoding, errors='replace')
                exit_code = process.returncode

                return exit_code == 0, stdout, stderr, exit_code

            except subprocess.TimeoutExpired:
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
                stdout = stdout_bytes.decode(encoding, errors='replace') if stdout_bytes else ""
                stderr = f"命令执行超时 ({timeout}秒)"
                return False, stdout, stderr, -1

        except Exception as e:
            return False, "", f"执行错误: {str(e)}", -1


# 便捷函数（保持与 ssh_executor 一致的接口）
def execute(
    host: str,
    port: int,
    username: str,
    password: str,
    command: str,
    timeout: int = 30
) -> Tuple[bool, str, str, int]:
    """
    执行本地命令

    注意：参数设计与 SSHExecutor 保持一致，但本地执行不需要 host/port/username/password
    这些参数会被忽略

    Returns:
        (成功, stdout, stderr, 退出码)
    """
    # 只使用 command 和 timeout 参数
    return LocalExecutor.execute(command, timeout)
