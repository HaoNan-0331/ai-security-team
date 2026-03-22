#!/usr/bin/env python3
"""
服务端部署到 Linux 服务器脚本
使用 paramiko 进行 SSH 连接和文件传输
"""
import paramiko
import os
import sys
from pathlib import Path

# 服务器配置
SERVER_HOST = "192.168.181.132"
SERVER_USER = "root"
SERVER_PASSWORD = "Qch@2025"
REMOTE_DIR = "/opt/command_executor"

# 项目目录
PROJECT_DIR = Path(__file__).parent


def create_ssh_client():
    """创建 SSH 客户端"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        SERVER_HOST,
        username=SERVER_USER,
        password=SERVER_PASSWORD,
        timeout=30
    )
    return client


def upload_file(sftp, local_path, remote_path):
    """上传单个文件"""
    try:
        sftp.put(str(local_path), remote_path)
        print(f"  [OK] {local_path.name}")
        return True
    except Exception as e:
        print(f"  [FAIL] {local_path.name}: {e}")
        return False


def execute_command(ssh, command):
    """执行远程命令"""
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return exit_code, output, error


def main():
    print("=== 开始部署服务端到 Linux 服务器 ===")
    print(f"目标服务器: {SERVER_HOST}")
    print()

    try:
        # 创建 SSH 连接
        print("[1/6] 连接到服务器...")
        ssh = create_ssh_client()
        sftp = ssh.open_sftp()
        print("  [OK] 连接成功\n")

        # 创建远程目录
        print("[2/6] 创建远程目录...")
        dirs = [
            REMOTE_DIR,
            f"{REMOTE_DIR}/server",
            f"{REMOTE_DIR}/shared",
            f"{REMOTE_DIR}/logs"
        ]
        for d in dirs:
            execute_command(ssh, f"mkdir -p {d}")
        print("  [OK] 目录创建成功\n")

        # 上传服务端文件
        print("[3/6] 上传服务端文件...")
        server_files = [
            "server/main.py",
            "server/websocket_server.py",
            "server/api_server.py",
            "server/database.py",
            "server/config.py",
            "server/requirements.txt"
        ]

        for file in server_files:
            local_path = PROJECT_DIR / file
            remote_path = f"{REMOTE_DIR}/{file}"
            upload_file(sftp, local_path, remote_path)
        print()

        # 上传共享模块
        print("[4/6] 上传共享模块...")
        shared_files = ["shared/models.py"]
        for file in shared_files:
            local_path = PROJECT_DIR / file
            remote_path = f"{REMOTE_DIR}/{file}"
            upload_file(sftp, local_path, remote_path)
        print()

        # 安装 Python 依赖
        print("[5/6] 安装 Python 依赖...")
        cmd = f"cd {REMOTE_DIR} && pip3 install -r server/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
        exit_code, output, error = execute_command(ssh, cmd)
        if exit_code == 0:
            print("  [OK] 依赖安装成功\n")
        else:
            print(f"  [FAIL] 依赖安装失败: {error}\n")

        # 停止已运行的服务
        print("[6/6] 启动服务端...")
        execute_command(ssh, f"pkill -f 'python.*{REMOTE_DIR}/server/main.py' || true")
        import time
        time.sleep(2)

        # 创建并启动服务
        start_cmd = f"""cd {REMOTE_DIR} && nohup python3 server/main.py > logs/server.log 2>&1 & echo $! > logs/server.pid"""
        exit_code, output, error = execute_command(ssh, start_cmd)

        # 获取 PID
        exit_code, pid_output, _ = execute_command(ssh, f"cat {REMOTE_DIR}/logs/server.pid")

        print("  [OK] 服务端已启动")
        print(f"  PID: {pid_output.strip()}\n")

        # 关闭连接
        sftp.close()
        ssh.close()

        print("=== 部署完成 ===")
        print(f"查看日志: ssh {SERVER_USER}@{SERVER_HOST} 'tail -f {REMOTE_DIR}/logs/server.log'")
        print(f"停止服务: ssh {SERVER_USER}@{SERVER_HOST} 'cat {REMOTE_DIR}/logs/server.pid | xargs kill'")

    except Exception as e:
        print(f"\n[FAIL] 部署失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
