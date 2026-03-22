#!/usr/bin/env python3
"""
服务端部署脚本
"""
import paramiko
import sys
import os
from pathlib import Path

# 服务器配置
SERVER_HOST = "10.7.8.120"
SERVER_USER = "root"
SERVER_PASSWORD = "Qch@2025"
PROJECT_PATH = r"E:\knowlegdge_base\python_project\command_executor"
SERVER_DEPLOY_PATH = "/opt/command_executor"

def ssh_connect():
    """创建SSH连接"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    return client

def run_command(client, command):
    """执行远程命令"""
    print(f"\n>>> {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')

    if output.strip():
        print(output.strip())
    if error.strip() and exit_code != 0:
        print(f"错误: {error.strip()}")

    return exit_code == 0

def upload_directory(client, local_dir, remote_dir):
    """上传整个目录"""
    sftp = client.open_sftp()
    local_path = Path(local_dir)

    try:
        # 创建远程目录
        try:
            sftp.stat(remote_dir)
        except IOError:
            sftp.mkdir(remote_dir)

        # 遍历本地目录
        for item in local_path.rglob("*"):
            if item.is_file():
                # 计算相对路径
                rel_path = item.relative_to(local_path)
                remote_file = f"{remote_dir}/{rel_path}".replace("\\", "/")
                remote_file_dir = str(Path(remote_file).parent).replace("\\", "/")

                # 创建远程目录
                try:
                    sftp.stat(remote_file_dir)
                except IOError:
                    # 递归创建目录
                    dirs = remote_file_dir.split('/')
                    for i in range(1, len(dirs)):
                        d = '/'.join(dirs[:i+1])
                        try:
                            sftp.stat(d)
                        except IOError:
                            try:
                                sftp.mkdir(d)
                            except:
                                pass

                # 上传文件
                print(f"  上传: {rel_path}")
                sftp.put(str(item), remote_file)

        print(f"目录上传完成: {local_dir} -> {remote_dir}")
        return True

    except Exception as e:
        print(f"上传失败: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("=" * 60)
    print("分布式命令执行系统 - 服务端部署")
    print("=" * 60)

    # 连接服务器
    print(f"\n连接到服务器 {SERVER_HOST}...")
    client = ssh_connect()
    print("连接成功!")

    # 检查系统
    print("\n检查系统信息...")
    run_command(client, "cat /etc/os-release | head -3")

    # 检查并安装Python3
    print("\n检查Python3...")
    run_command(client, "which python3 || echo '需要安装Python3'")

    # 检查pip
    print("\n检查pip...")
    run_command(client, "which pip3 || which pip || echo '需要安装pip'")

    # 创建部署目录
    print("\n创建部署目录...")
    run_command(client, f"mkdir -p {SERVER_DEPLOY_PATH}")

    # 上传服务端代码
    print("\n上传服务端代码...")
    upload_directory(client, os.path.join(PROJECT_PATH, "server"), f"{SERVER_DEPLOY_PATH}/server")
    upload_directory(client, os.path.join(PROJECT_PATH, "shared"), f"{SERVER_DEPLOY_PATH}/shared")

    # 安装依赖
    print("\n安装Python依赖...")
    run_command(client, f"cd {SERVER_DEPLOY_PATH}/server && pip3 install -r requirements.txt")

    # 配置防火墙
    print("\n配置防火墙...")
    run_command(client, "systemctl status firewalld >/dev/null 2>&1 && firewall-cmd --permanent --add-port=8765/tcp --add-port=8080/tcp && firewall-cmd --reload || echo '防火墙配置已跳过'")

    client.close()

    print("\n" + "=" * 60)
    print("部署完成!")
    print("=" * 60)
    print(f"\n部署路径: {SERVER_DEPLOY_PATH}")
    print(f"\n启动服务端:")
    print(f"  ssh {SERVER_USER}@{SERVER_HOST}")
    print(f"  cd {SERVER_DEPLOY_PATH}/server")
    print(f"  python3 main.py")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
