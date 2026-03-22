#!/usr/bin/env python3
"""
部署并启动服务端
"""
import paramiko

SERVER_HOST = "10.7.8.120"
SERVER_USER = "root"
SERVER_PASSWORD = "Qch@2025"
DEPLOY_PATH = "/opt/command_executor"

def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_HOST, username=SERVER_USER, password=SERVER_PASSWORD, timeout=30)
    return client

def run_command(client, command):
    print(f">>> {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='replace')
    error = stderr.read().decode('utf-8', errors='replace')

    if output.strip():
        print(output.strip())
    if error.strip() and exit_code != 0:
        print(f"错误: {error.strip()}")

    return exit_code == 0

client = ssh_connect()

print("=== 安装依赖并启动服务端 ===\n")

# 升级pip
print("[1/4] 升级pip...")
run_command(client, "python3 -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/")

# 安装依赖
print("\n[2/4] 安装Python依赖...")
run_command(client, f"cd {DEPLOY_PATH}/server && python3 -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/")

# 配置防火墙
print("\n[3/4] 配置防火墙...")
run_command(client, "firewall-cmd --permanent --add-port=8765/tcp --add-port=8080/tcp 2>/dev/null && firewall-cmd --reload 2>/dev/null || echo '防火墙配置完成或已跳过'")

# 启动服务端
print("\n[4/4] 启动服务端...")
run_command(client, f"cd {DEPLOY_PATH}/server && nohup python3 main.py > /var/log/command_executor.log 2>&1 &")

# 检查服务状态
print("\n=== 检查服务状态 ===")
run_command(client, "sleep 2 && netstat -tuln | grep -E '8765|8080'")
run_command(client, "ps aux | grep 'python3 main.py' | grep -v grep")

print("\n=== 部署完成 ===")
print(f"\n服务端地址: http://{SERVER_HOST}:8080")
print(f"WebSocket地址: ws://{SERVER_HOST}:8765")
print(f"\n查看日志: tail -f /var/log/command_executor.log")

client.close()
