#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华为设备专属执行器
支持华为(Huawei)设备的命令执行
集成经验库，自动处理已知问题，支持命令帮助查询
"""

import sys
import json
import time
import re
import argparse
import getpass
import paramiko
import telnetlib
from pathlib import Path
from typing import Dict, List, Any, Optional

# 导入基类和经验管理器
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from base_executor import BaseExecutor
from experience_manager import ExperienceManager


class HuaweiExecutor(BaseExecutor):
    """华为设备执行器 - 支持SSH和Telnet"""

    def __init__(self, host: str, username: str, password: str,
                 port: int = 22, timeout: int = 30, auto_help: bool = False,
                 protocol: str = "ssh"):
        """
        初始化华为执行器

        Args:
            host: 设备IP地址
            username: 用户名
            password: 密码
            port: 端口 (SSH默认22, Telnet默认23)
            timeout: 连接超时时间
            auto_help: 命令失败时自动查询帮助
            protocol: 协议类型 (ssh 或 telnet)
        """
        super().__init__(host, username, password, port, timeout, auto_help)
        self.device_type = "Huawei"
        self.protocol = protocol.lower()

        # Telnet连接对象
        self.tn_client = None

        # 经验管理器
        self.exp_manager = ExperienceManager()

        # 执行结果
        self.results = []

    def connect(self) -> bool:
        """建立连接 - 支持SSH和Telnet"""
        if self.protocol == "telnet":
            return self._connect_telnet()
        else:
            return self._connect_ssh()

    def _connect_ssh(self) -> bool:
        """建立SSH连接"""
        self.log(f"正在通过SSH连接到华为设备 {self.host}...", "INFO")

        try:
            experiences = self.exp_manager.get_relevant_experiences("Huawei", "connection")
            if experiences:
                self.log(f"找到 {len(experiences)} 条连接相关经验", "INFO")

            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.ssh_client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                auth_timeout=self.timeout,
                banner_timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )

            self.shell = self.ssh_client.invoke_shell()
            time.sleep(2)

            if self.shell.recv_ready():
                self.shell.recv(65535)

            self.log(f"已连接 (SSH shell模式)", "OK")
            return True

        except paramiko.AuthenticationException:
            self.log(f"连接失败: 认证失败", "ERROR")
            return False
        except Exception as e:
            self.log(f"连接失败: {str(e)}", "ERROR")
            return False

    def _connect_telnet(self) -> bool:
        """建立Telnet连接"""
        self.log(f"正在通过Telnet连接到华为设备 {self.host}...", "INFO")

        try:
            # 设置默认端口
            port = self.port if self.port != 22 else 23

            # 创建Telnet连接
            self.tn_client = telnetlib.Telnet(self.host, port, timeout=self.timeout)

            # 等待登录提示
            self.log("等待登录提示...", "INFO")
            response = self.tn_client.read_until(b"Username:", timeout=5).decode('ascii', errors='ignore')

            # 发送用户名
            self.tn_client.write(self.username.encode('ascii') + b"\n")

            # 等待密码提示
            response = self.tn_client.read_until(b"Password:", timeout=5).decode('ascii', errors='ignore')

            # 发送密码
            self.tn_client.write(self.password.encode('ascii') + b"\n")

            # 等待登录完成（等待提示符）
            time.sleep(2)
            response = self.tn_client.read_very_eager().decode('ascii', errors='ignore')

            # 检查是否登录成功（查找提示符）
            if re.search(r'<\w+>|\[\w+\]', response):
                self.log(f"已连接 (Telnet模式)", "OK")
                return True
            else:
                self.log(f"登录失败: 未检测到命令提示符", "ERROR")
                return False

        except Exception as e:
            self.log(f"连接失败: {str(e)}", "ERROR")
            return False

    def _handle_pagination(self, timeout: int = 60) -> str:
        """处理分页并返回完整输出 - 支持SSH和Telnet"""
        output = ""
        start_time = time.time()
        last_data_time = time.time()

        if self.protocol == "telnet":
            # Telnet模式处理分页
            while time.time() - start_time < timeout:
                try:
                    chunk = self.tn_client.read_very_eager().decode('ascii', errors='ignore')
                    if chunk:
                        output += chunk
                        last_data_time = time.time()

                        # 处理华为分页符
                        if "---- More ----" in chunk:
                            self.tn_client.write(b" ")
                            time.sleep(0.3)
                            continue

                        # 检测命令提示符
                        if re.search(r'<\w+>|\[\w+\]', chunk) and len(output) > 50:
                            time.sleep(0.5)
                            # 再次检查是否有新数据
                            try:
                                extra = self.tn_client.read_very_eager().decode('ascii', errors='ignore')
                                if not extra:
                                    break
                                output += extra
                            except:
                                break

                    if time.time() - last_data_time > 2 and len(output) > 50:
                        break

                    time.sleep(0.2)
                except:
                    if time.time() - last_data_time > 2 and len(output) > 50:
                        break
                    time.sleep(0.2)
            return output
        else:
            # SSH模式处理分页
            while time.time() - start_time < timeout:
                if self.shell.recv_ready():
                    chunk = self.shell.recv(65535).decode('utf-8', errors='ignore')
                    output += chunk
                    last_data_time = time.time()

                    if "---- More ----" in chunk:
                        self.shell.send(" ")
                        time.sleep(0.3)
                        continue

                    if (re.search(r'<\w+>|\[\S+\]', chunk) and len(output) > 50):
                        time.sleep(0.5)
                        if not self.shell.recv_ready():
                            break

                if time.time() - last_data_time > 3 and len(output) > 50:
                    break

                time.sleep(0.2)

            return output

    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """执行单条命令 - 支持SSH和Telnet"""
        result = {
            "command": command,
            "success": False,
            "output": "",
            "error": None,
            "help": None
        }

        if self.protocol == "telnet":
            if not self.tn_client:
                result["error"] = "未建立连接"
                return result
        else:
            if not self.shell:
                result["error"] = "未建立连接"
                return result

        try:
            if self.protocol == "telnet":
                self.tn_client.write(command.encode("ascii") + b"
")
            else:
                self.shell.send(command + "
")

            output = self._handle_pagination(timeout)

            result["output"] = output
            result["success"] = True

            error_patterns = [r"% Error", r"% Incomplete", r"Unrecognized", r"Error:", r"Error: "]
            for pattern in error_patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    result["success"] = False
                    result["error"] = f"命令执行错误: {pattern}"

                    if self.auto_help:
                        self.log(f"命令失败，自动查询帮助...", "INFO")
                        result["help"] = self.query_help(command)
                    break

        except Exception as e:
            result["error"] = str(e)
            result["success"] = False

        return result
    def execute_commands(self, commands: List[str], stop_on_error: bool = True) -> Dict[str, Any]:
        """批量执行命令"""
        self.log(f"开始执行 {len(commands)} 条命令", "INFO")

        summary = {
            "success": True,
            "total": len(commands),
            "executed": 0,
            "failed_at": None,
            "results": []
        }

        for idx, cmd in enumerate(commands, 1):
            self.log(f"[{idx}/{len(commands)}] {cmd}", "INFO")
            result = self.execute_command(cmd)
            summary["executed"] += 1
            summary["results"].append(result)

            if not result["success"]:
                summary["success"] = False
                summary["failed_at"] = idx
                self.log(f"命令执行失败，位置: {idx}", "ERROR")
                if stop_on_error:
                    break

        if summary["success"]:
            self.log(f"所有命令执行成功", "OK")

        return summary

    def disconnect(self):
        """断开连接 - 支持SSH和Telnet"""
        try:
            if self.protocol == "telnet" and self.tn_client:
                self.tn_client.close()
            else:
                if self.shell:
                    self.shell.close()
                if self.ssh_client:
                    self.ssh_client.close()
            self.log("已断开连接", "INFO")
        except:
            pass


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="华为设备专属执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python huawei_executor.py --host 192.168.1.1 --username admin --password xxx --commands "display version"
  python huawei_executor.py --host 192.168.1.1 --username admin --password xxx --query-help "undo nat"
  python huawei_executor.py --host 192.168.1.1 --username admin --password xxx --commands "display version" --auto-help
        """
    )

    # 连接参数（必填）
    parser.add_argument("--host", required=True, help="设备IP地址")
    parser.add_argument("--username", required=True, help="用户名")
    parser.add_argument("--password", help="密码（不指定则交互式输入）")
    parser.add_argument("--port", type=int, default=22, help="端口 (SSH默认22, Telnet默认23)")
    parser.add_argument("--protocol", default="ssh", choices=["ssh", "telnet"], help="连接协议 (默认: ssh)")
    parser.add_argument("--commands", nargs="+", help="要执行的命令列表")
    parser.add_argument("--commands-json", help="从JSON读取命令")
    parser.add_argument("--query-help", help="查询指定命令的帮助信息")
    parser.add_argument("--auto-help", action="store_true", help="命令失败时自动查询帮助")
    parser.add_argument("--timeout", type=int, default=30, help="超时时间")
    parser.add_argument("--continue-on-error", action="store_true", help="遇错继续")
    parser.add_argument("--output", help="输出到文件")

    args = parser.parse_args()

    # 获取密码
    password = args.password
    if not password:
        password = getpass.getpass("密码: ")

    # 根据协议设置默认端口
    port = args.port
    if args.protocol == "telnet" and port == 22:
        port = 23

    executor = HuaweiExecutor(
        host=args.host,
        username=args.username,
        password=password,
        port=port,
        timeout=args.timeout,
        auto_help=args.auto_help,
        protocol=args.protocol
    )

    try:
        if not executor.connect():
            sys.exit(1)

        if args.query_help:
            help_output = executor.query_help(args.query_help)
            print("\n" + "="*50)
            print(f"命令帮助: {args.query_help} ?")
            print("="*50)
            print(help_output)
            sys.exit(0)

        commands = None
        if args.commands_json:
            if args.commands_json == "-":
                import fileinput
                commands = json.loads("".join(fileinput.input(files=("-"))))
            else:
                try:
                    with open(args.commands_json, 'r') as f:
                        commands = json.load(f)
                except:
                    commands = json.loads(args.commands_json)
        elif args.commands:
            commands = args.commands
        else:
            parser.error("必须指定 --commands 或 --query-help")

        result = executor.execute_commands(commands, not args.continue_on_error)

        output_result = {
            "success": result["success"],
            "executed": result["executed"],
            "total": result["total"],
            "failed_at": result["failed_at"],
            "results": [{"command": r["command"], "success": r["success"],
                        "output": r["output"][:500] if r["output"] else "",
                        "error": r.get("error"), "help": r.get("help")}
                       for r in result["results"]]
        }

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_result, f, indent=2, ensure_ascii=False)
            print(f"[OK] 结果已保存到: {args.output}")
        else:
            print("\n" + "="*50)
            print(json.dumps(output_result, indent=2, ensure_ascii=False))

        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        print("\n[WARNING] 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        executor.disconnect()


if __name__ == "__main__":
    main()
