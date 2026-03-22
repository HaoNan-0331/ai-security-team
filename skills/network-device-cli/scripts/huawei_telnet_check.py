#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华为设备 Telnet 巡检脚本
使用 socket 实现简单的 Telnet 客户端
"""

import socket
import time
import re
import json
import sys


class SimpleTelnetClient:
    """简单的 Telnet 客户端"""

    def __init__(self, host, port=23, timeout=30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.buffer = ""

    def connect(self):
        """建立连接"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"[ERROR] 连接失败: {str(e)}")
            return False

    def send(self, data):
        """发送数据"""
        if self.socket:
            self.socket.sendall(data)

    def recv_until(self, pattern, timeout=5):
        """接收数据直到匹配模式"""
        buffer = b""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = self.socket.recv(4096)
                if chunk:
                    buffer += chunk
                    if re.search(pattern.encode(), buffer):
                        return buffer.decode('ascii', errors='ignore')
            except socket.timeout:
                break
            except:
                break

        return buffer.decode('ascii', errors='ignore')

    def recv_all(self, timeout=2, idle_timeout=2):
        """接收所有可用数据"""
        buffer = b""
        start_time = time.time()
        last_data_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 设置短超时以便检测空闲
                self.socket.settimeout(0.5)
                chunk = self.socket.recv(4096)
                if chunk:
                    buffer += chunk
                    last_data_time = time.time()
                else:
                    if time.time() - last_data_time > idle_timeout:
                        break
            except socket.timeout:
                if time.time() - last_data_time > idle_timeout and len(buffer) > 0:
                    break
            except:
                break

        return buffer.decode('ascii', errors='ignore')

    def close(self):
        """关闭连接"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class HuaweiTelnetChecker:
    """华为设备 Telnet 巡检器"""

    def __init__(self, host, username, password, port=23, timeout=30):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.tn = None

    def connect(self):
        """建立 Telnet 连接"""
        try:
            print(f"[INFO] 正在通过 Telnet 连接到 {self.host}:{self.port}...")

            self.tn = SimpleTelnetClient(self.host, self.port, self.timeout)

            if not self.tn.connect():
                return False

            # 清空初始缓冲区
            try:
                self.tn.socket.settimeout(1)
                self.tn.socket.recv(4096)
            except:
                pass

            # 等待登录提示（华为设备可能有不同的提示）
            response = ""
            self.tn.socket.settimeout(10)
            while "Username:" not in response and "username:" not in response and "Login:" not in response:
                try:
                    chunk = self.tn.socket.recv(4096).decode('ascii', errors='ignore')
                    response += chunk
                except socket.timeout:
                    break

            print(f"[DEBUG] 收到登录提示")

            # 发送用户名
            self.tn.send(self.username.encode('ascii') + b"\n")

            # 等待密码提示
            response = ""
            self.tn.socket.settimeout(10)
            while "Password:" not in response and "password:" not in response:
                try:
                    chunk = self.tn.socket.recv(4096).decode('ascii', errors='ignore')
                    response += chunk
                except socket.timeout:
                    break

            print(f"[DEBUG] 收到密码提示")

            # 发送密码
            self.tn.send(self.password.encode('ascii') + b"\n")

            # 等待登录完成 - 华为设备可能需要较长时间
            print(f"[DEBUG] 等待登录完成...")
            time.sleep(3)

            # 检查是否认证失败
            response = ""
            self.tn.socket.settimeout(2)
            for _ in range(20):
                try:
                    chunk = self.tn.socket.recv(4096).decode('ascii', errors='ignore')
                    if chunk:
                        response += chunk
                except:
                    pass
                time.sleep(0.1)

            # 检查认证错误
            if "Authentication fail" in response or "Failed" in response or "denied" in response.lower():
                print(f"[ERROR] 认证失败，请检查用户名和密码")
                print(f"[DEBUG] 响应: {response[:200]}...")
                return False

            print(f"[DEBUG] 认证后响应: {response[:200] if response else '无响应'}...")

            # 检查是否登录成功（查找提示符）
            if re.search(r'<\w+>|\[\w+\]', response):
                print(f"[OK] 已连接")
                return True

            # 尝试发送回车以获取提示符
            print(f"[DEBUG] 尝试发送回车获取提示符...")
            self.tn.send(b"\n")
            time.sleep(1)

            response = ""
            self.tn.socket.settimeout(2)
            for _ in range(15):
                try:
                    chunk = self.tn.socket.recv(4096).decode('ascii', errors='ignore')
                    if chunk:
                        response += chunk
                except:
                    pass
                time.sleep(0.1)

            print(f"[DEBUG] 回车后响应: {response[:200] if response else '无响应'}...")

            if re.search(r'<\w+>|\[\w+\]', response):
                print(f"[OK] 已连接（发送回车后）")
                return True
            else:
                print(f"[ERROR] 登录失败，未检测到命令提示符")
                print(f"[DEBUG] 最终响应: {response[:500] if response else '无响应'}...")
                return False

        except Exception as e:
            print(f"[ERROR] 连接失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def execute_command(self, command, timeout=60):
        """执行单条命令"""
        result = {
            "command": command,
            "success": False,
            "output": "",
            "error": None
        }

        if not self.tn:
            result["error"] = "未建立连接"
            return result

        try:
            print(f"[INFO] 执行命令: {command}")

            # 发送命令
            self.tn.send(command.encode('ascii') + b"\n")

            # 读取输出
            output = ""
            start_time = time.time()
            last_data_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # 设置短超时
                    self.tn.socket.settimeout(0.5)

                    chunk = self.tn.socket.recv(4096)
                    if chunk:
                        chunk_text = chunk.decode('ascii', errors='ignore')
                        output += chunk_text
                        last_data_time = time.time()

                        # 处理分页
                        if "---- More ----" in chunk_text:
                            self.tn.send(b" ")
                            time.sleep(0.3)
                            continue

                        # 检测命令提示符
                        if re.search(r'<\w+>|\[\w+\]', chunk_text) and len(output) > 50:
                            time.sleep(0.5)
                            # 再次检查是否有新数据
                            try:
                                extra = self.tn.socket.recv(4096)
                                if not extra:
                                    break
                                output += extra.decode('ascii', errors='ignore')
                            except:
                                break

                    # 空闲超时检查
                    if time.time() - last_data_time > 2 and len(output) > 50:
                        break

                    time.sleep(0.1)

                except socket.timeout:
                    if time.time() - last_data_time > 2 and len(output) > 50:
                        break
                except:
                    if time.time() - last_data_time > 2 and len(output) > 50:
                        break
                    time.sleep(0.1)

            result["output"] = output
            result["success"] = True

            # 检查错误
            error_patterns = [r"% Error", r"% Incomplete", r"Unrecognized", r"Error:", r"Error: "]
            for pattern in error_patterns:
                if re.search(pattern, output, re.IGNORECASE):
                    result["success"] = False
                    result["error"] = f"命令执行错误: {pattern}"
                    break

        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
            import traceback
            traceback.print_exc()

        return result

    def execute_commands(self, commands):
        """批量执行命令"""
        results = []
        for cmd in commands:
            result = self.execute_command(cmd)
            results.append(result)
            if not result["success"]:
                print(f"[ERROR] 命令执行失败: {cmd}")
                break
        return results

    def disconnect(self):
        """断开连接"""
        try:
            if self.tn:
                self.tn.close()
            print("[INFO] 已断开连接")
        except:
            pass


def main():
    """主函数"""
    # 设备信息
    host = "10.7.8.252"
    username = "admin"
    password = "Qch@2025"
    port = 23

    # 巡检命令
    commands = [
        "display version",
        "display device",
        "display memory-usage",
        "display cpu-usage",
        "display interface brief",
        "display alarm active"
    ]

    # 创建巡检器
    checker = HuaweiTelnetChecker(host, username, password, port)

    try:
        # 连接设备
        if not checker.connect():
            sys.exit(1)

        # 执行巡检命令
        results = checker.execute_commands(commands)

        # 输出结果
        print("\n" + "=" * 60)
        print("华为设备巡检报告")
        print("=" * 60)

        for result in results:
            print(f"\n命令: {result['command']}")
            print(f"状态: {'成功' if result['success'] else '失败'}")
            if result['error']:
                print(f"错误: {result['error']}")
            print(f"输出预览:\n{result['output'][:500]}...")

        # 保存到文件
        output_file = f"inspection_{host}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] 结果已保存到: {output_file}")

    finally:
        checker.disconnect()


if __name__ == "__main__":
    main()
