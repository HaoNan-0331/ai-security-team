"""
Telnet执行模块
使用telnetlib3执行Telnet命令
"""
import logging
import asyncio
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# 尝试导入 telnetlib3，如果不存在则使用内置的 telnetlib
try:
    import telnetlib3
    USE_TELNETLIB3 = True
except ImportError:
    try:
        import telnetlib
        USE_TELNETLIB3 = False
    except ImportError:
        USE_TELNETLIB3 = False
        logger.warning("未找到 telnetlib3 或 telnetlib，请安装: pip install telnetlib3")


class TelnetExecutor:
    """Telnet命令执行器"""

    @staticmethod
    async def execute_async(
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        command: str = "",
        timeout: int = 30,
        login_prompt: str = "login:",
        password_prompt: str = "Password:",
        shell_prompt: str = None
    ) -> Tuple[bool, str, str, int]:
        """
        异步执行Telnet命令（使用telnetlib3）

        返回: (成功, stdout, stderr, 退出码)
        """
        reader = None
        writer = None

        try:
            # 连接到Telnet服务器
            reader, writer = await asyncio.wait_for(
                telnetlib3.open_connection(host, port),
                timeout=timeout
            )

            output = []
            errors = []

            # 如果需要认证
            if username:
                # 等待登录提示
                try:
                    response = await asyncio.wait_for(
                        reader.readuntil(login_prompt.encode()),
                        timeout=5
                    )
                    output.append(response.decode('utf-8', errors='replace'))

                    # 发送用户名
                    writer.write(f"{username}\n")
                    await writer.drain()

                    # 等待密码提示
                    response = await asyncio.wait_for(
                        reader.readuntil(password_prompt.encode()),
                        timeout=5
                    )
                    output.append(response.decode('utf-8', errors='replace'))

                    # 发送密码
                    writer.write(f"{password}\n")
                    await writer.drain()

                except asyncio.TimeoutError:
                    errors.append("登录超时")

            # 等待shell提示符（如果指定）
            if shell_prompt:
                try:
                    response = await asyncio.wait_for(
                        reader.readuntil(shell_prompt.encode()),
                        timeout=5
                    )
                    output.append(response.decode('utf-8', errors='replace'))
                except asyncio.TimeoutError:
                    pass  # 某些设备可能没有明确的shell提示符

            # 发送命令
            if command:
                writer.write(f"{command}\n")
                await writer.drain()

                # 等待响应（等待一段时间让命令执行完成）
                await asyncio.sleep(1)

                # 读取所有可用输出
                try:
                    response = await asyncio.wait_for(
                        reader.read(1024 * 10),
                        timeout=timeout - 5
                    )
                    # telnetlib3 返回字符串，不需要 decode
                    if isinstance(response, bytes):
                        output.append(response.decode('utf-8', errors='replace'))
                    else:
                        output.append(response)
                except asyncio.TimeoutError:
                    pass

            # 关闭连接
            writer.close()
            await writer.wait_closed()

            stdout_str = "".join(output)
            stderr_str = "".join(errors)

            # Telnet没有标准的退出码，根据是否有错误判断
            success = len(errors) == 0

            logger.info(f"Telnet命令执行完成: host={host}, command={command[:50]}, success={success}")

            return success, stdout_str, stderr_str, 0 if success else -1

        except asyncio.TimeoutError:
            logger.error(f"Telnet连接超时: {host}:{port}")
            return False, "", "连接超时", -1

        except ConnectionRefusedError:
            logger.error(f"Telnet连接被拒绝: {host}:{port}")
            return False, "", "连接被拒绝", -1

        except Exception as e:
            logger.error(f"Telnet执行错误: {e}")
            return False, "", f"执行错误: {str(e)}", -1

        finally:
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass

    @staticmethod
    def execute(
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        command: str = "",
        timeout: int = 30,
        login_prompt: str = "login:",
        password_prompt: str = "Password:",
        shell_prompt: str = None
    ) -> Tuple[bool, str, str, int]:
        """
        同步执行Telnet命令（兼容接口）

        返回: (成功, stdout, stderr, 退出码)
        """
        if USE_TELNETLIB3:
            # 使用异步版本
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    TelnetExecutor.execute_async(
                        host, port, username, password, command,
                        timeout, login_prompt, password_prompt, shell_prompt
                    )
                )
                return result
            finally:
                loop.close()

        else:
            # 使用telnetlib（Python内置，但已弃用）
            try:
                import telnetlib

                tn = None
                output = []
                errors = []

                try:
                    # 连接到Telnet服务器
                    tn = telnetlib.Telnet(host, port, timeout)

                    # 如果需要认证
                    if username:
                        # 等待登录提示
                        tn.read_until(login_prompt.encode(), timeout=5)
                        output.append(tn.read_very_eager().decode('utf-8', errors='replace'))

                        # 发送用户名
                        tn.write(f"{username}\n".encode('utf-8'))

                        # 等待密码提示
                        tn.read_until(password_prompt.encode(), timeout=5)
                        output.append(tn.read_very_eager().decode('utf-8', errors='replace'))

                        # 发送密码
                        tn.write(f"{password}\n".encode('utf-8'))

                    # 等待shell提示符（如果指定）
                    if shell_prompt:
                        try:
                            tn.read_until(shell_prompt.encode(), timeout=5)
                            output.append(tn.read_very_eager().decode('utf-8', errors='replace'))
                        except:
                            pass

                    # 发送命令
                    if command:
                        tn.write(f"{command}\n".encode('utf-8'))

                        # 等待响应
                        response = tn.read_until(command.encode(), timeout=timeout)
                        output.append(response.decode('utf-8', errors='replace'))

                        # 再读取一些输出
                        try:
                            response = tn.read_very_eager()
                            if response:
                                output.append(response.decode('utf-8', errors='replace'))
                        except:
                            pass

                    # 关闭连接
                    tn.close()

                    stdout_str = "".join(output)
                    stderr_str = "".join(errors)

                    success = len(errors) == 0

                    logger.info(f"Telnet命令执行完成: host={host}, command={command[:50]}, success={success}")

                    return success, stdout_str, stderr_str, 0 if success else -1

                except Exception as e:
                    logger.error(f"Telnet执行错误: {e}")
                    return False, "", f"执行错误: {str(e)}", -1

                finally:
                    if tn:
                        try:
                            tn.close()
                        except:
                            pass

            except ImportError:
                logger.error("未安装 telnetlib3，请执行: pip install telnetlib3")
                return False, "", "缺少依赖库: telnetlib3", -1
