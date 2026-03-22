#!/usr/bin/env python3
"""
在 Linux 服务器上安装 Python3 和依赖
"""
import paramiko
import sys


def run_command(ssh, command):
    """执行命令并打印输出"""
    print(f"执行: {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')

    if output:
        print(output)
    if error:
        print(f"[ERROR]: {error}")

    return exit_code


def main():
    SERVER = "192.168.181.132"
    USER = "root"
    PASSWORD = "Qch@2025"

    print("=== 在 Linux 服务器上安装 Python3 ===")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER, username=USER, password=PASSWORD, timeout=30)

    # 检测系统版本
    print("\n[1/5] 检测系统版本...")
    run_command(client, "cat /etc/redhat-release")

    # 安装 EPEL 源
    print("\n[2/5] 安装 EPEL 源...")
    run_command(client, "yum install -y epel-release")

    # 安装 Python3
    print("\n[3/5] 安装 Python3...")
    run_command(client, "yum install -y python3 python3-pip")

    # 验证安装
    print("\n[4/5] 验证 Python3 安装...")
    run_command(client, "python3 --version && pip3 --version")

    # 安装项目依赖
    print("\n[5/5] 安装项目依赖...")
    run_command(client, "cd /opt/command_executor && pip3 install -r server/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple")

    print("\n=== 安装完成 ===")

    client.close()


if __name__ == "__main__":
    main()
