#!/usr/bin/env python3
"""
上传可移植的 Python3 到 Linux 服务器
"""
import paramiko
import sys
import os
from pathlib import Path


def main():
    SERVER = "192.168.181.132"
    USER = "root"
    PASSWORD = "Qch@2025"
    REMOTE_DIR = "/opt/command_executor"

    print("=== 部署可移植 Python3 到服务器 ===")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print("连接到服务器...")
        client.connect(SERVER, username=USER, password=PASSWORD, timeout=30)
        sftp = client.open_sftp()
        print("连接成功\n")

        # 创建目录
        print("[1/3] 创建 Python3 目录...")
        stdin, stdout, stderr = client.exec_command(f"mkdir -p {REMOTE_DIR}/python3")
        stdout.read()
        print("  [OK] 目录创建完成\n")

        # 下载可移植的 Python3 (使用嵌入式版本)
        print("[2/3] 下载可移植的 Python3...")
        download_cmd = f"cd {REMOTE_DIR}/python3 && wget https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz --no-check-certificate"
        stdin, stdout, stderr = client.exec_command(download_cmd)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()

        if exit_code == 0:
            print("  [OK] Python3 源码下载完成\n")
        else:
            print(f"  [FAIL] 下载失败\n")

            # 尝试另一种方法 - 使用yum安装最小版本的python3
            print("[2/3] 尝试使用 yum 安装 Python3...")
            install_cmd = "yum install -y python3 --enablerepo=* --disablerepo=base,updates,extras"
            stdin, stdout, stderr = client.exec_command(install_cmd)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            print(output[-500:])

        # 检查安装结果
        print("[3/3] 验证 Python3 安装...")
        stdin, stdout, stderr = client.exec_command("python3 --version 2>&1")
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode()

        if exit_code == 0:
            print(f"  [OK] Python3 已安装: {output.strip()}\n")

            # 安装 pip
            print("安装 pip...")
            stdin, stdout, stderr = client.exec_command("python3 -m ensurepip --upgrade 2>&1 || curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && python3 /tmp/get-pip.py")
            output = stdout.read().decode()
            print(output[-500:])

            # 创建 pip3 软链接
            stdin, stdout, stderr = client.exec_command("ln -sf /usr/local/bin/pip3 /usr/bin/pip3 2>/dev/null || ln -sf /usr/bin/pip3 /usr/bin/pip")
            stdout.read()

            # 验证
            stdin, stdout, stderr = client.exec_command("pip3 --version 2>&1")
            output = stdout.read().decode()
            print(f"pip3: {output.strip()}\n")
        else:
            print(f"  [FAIL] Python3 未安装\n")

        sftp.close()
        client.close()

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
