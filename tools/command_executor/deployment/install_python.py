#!/usr/bin/env python3
"""
在服务器上安装Python3 - 使用阿里云镜像
"""
import paramiko

SERVER_HOST = "10.7.8.120"
SERVER_USER = "root"
SERVER_PASSWORD = "Qch@2025"

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

print("=== 在CentOS 7上安装Python3 (使用阿里云镜像) ===\n")

# 备份并更换yum源为阿里云
print("[1/6] 更换yum源为阿里云...")
run_command(client, "mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup 2>/dev/null || echo '已备份'")
run_command(client, "wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo || curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo")

# 清理并重建缓存
print("\n[2/6] 清理并重建缓存...")
run_command(client, "yum clean all")
run_command(client, "yum makecache")

# 安装EPEL
print("\n[3/6] 安装EPEL...")
run_command(client, "yum install -y epel-release")

# 更换EPEL源为阿里云
print("\n[4/6] 更换EPEL源...")
run_command(client, "wget -O /etc/yum.repos.d/epel-7.repo http://mirrors.aliyun.com/repo/epel-7.repo || curl -o /etc/yum.repos.d/epel-7.repo http://mirrors.aliyun.com/repo/epel-7.repo")

# 安装Python3
print("\n[5/6] 安装Python3...")
run_command(client, "yum install -y python36")

# 创建软链接
print("\n[6/6] 创建软链接...")
run_command(client, "ln -sf /usr/bin/python3.6 /usr/bin/python3")
run_command(client, "ln -sf /usr/bin/pip3.6 /usr/bin/pip3 2>/dev/null || echo 'pip3未安装，稍后安装'")

# 验证
print("\n=== 验证安装 ===")
run_command(client, "python3 --version")

# 安装pip
print("\n=== 安装pip ===")
run_command(client, "python3 -m ensurepip --upgrade 2>/dev/null || yum install -y python36-pip")

client.close()

print("\n=== Python3安装完成 ===")
