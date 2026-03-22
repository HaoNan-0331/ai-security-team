# 服务端部署手册

## 目录
- [系统要求](#系统要求)
- [安装部署](#安装部署)
- [配置说明](#配置说明)
- [启动服务](#启动服务)
- [用户管理](#用户管理)
  - [自动绑定与用户切换](#自动绑定与用户切换)
- [维护管理](#维护管理)
- [故障排查](#故障排查)

---

## 系统要求

### 硬件要求
- CPU: 2核及以上
- 内存: 4GB及以上
- 硬盘: 20GB及以上

### 软件要求
- 操作系统: Linux / Windows / macOS
- Python: 3.6 或更高版本（已针对 Python 3.6 优化）
- 数据库:
  - SQLite（测试环境，无需安装）
  - PostgreSQL 12+（生产环境推荐）

---

## 安装部署

### 方式一：Windows 本地部署

#### 1. 安装 Python
下载并安装 Python 3.10+：https://www.python.org/downloads/

安装时勾选 **"Add Python to PATH"**

#### 2. 获取项目代码
```bash
cd E:\knowlegdge_base\python_project\command_executor
```

#### 3. 安装依赖
```bash
cd server
pip install -r requirements.txt
```

#### 4. 配置服务端
编辑 `server/config.py`：
```python
# 服务器配置
SERVER_HOST = "0.0.0.0"    # 监听所有网卡
SERVER_PORT = 8765         # WebSocket端口
API_PORT = 8080            # API端口

# 数据库配置（SQLite无需配置）
# 如需使用PostgreSQL，请填写以下信息：
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "command_executor"
DB_USER = "postgres"
DB_PASSWORD = "your_password"
```

### 方式二：Linux 服务器部署

#### 1. 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip postgresql postgresql-contrib -y

# CentOS/RHEL
sudo yum install python3 python3-pip postgresql-server -y
```

#### 2. 创建专用用户（推荐）
```bash
sudo useradd -m -s /bin/bash cmdexec
sudo su - cmdexec
```

#### 3. 上传项目代码
```bash
# 将项目上传到服务器
scp -r command_executor cmdexec@server_ip:/home/cmdexec/
```

#### 4. 安装 Python 依赖
```bash
cd ~/command_executor/server
pip3 install -r requirements.txt
```

#### 5. 配置 PostgreSQL（生产环境）
```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 psql 中执行：
CREATE DATABASE command_executor;
CREATE USER cmdexec_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE command_executor TO cmdexec_user;
\q
```

修改 `server/config.py` 中的数据库配置：
```python
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "command_executor"
DB_USER = "cmdexec_user"
DB_PASSWORD = "your_secure_password"
```

#### 6. 配置防火墙
```bash
# Ubuntu/Debian
sudo ufw allow 8765/tcp  # WebSocket端口
sudo ufw allow 8080/tcp  # API端口

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8765/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

---

### Python 3.6 兼容性说明（CentOS 7）

在 CentOS 7 等使用 Python 3.6 的系统中，需要进行额外配置：

#### 1. 安装 Python 3.6

如果系统没有 Python 3.6，可以通过以下方式安装：

```bash
# 方法1：使用 SCL 仓库（推荐）
yum install -y centos-release-scl
yum install -y rh-python36

# 创建软链接
ln -s /opt/rh/rh-python36/root/bin/python3 /usr/bin/python3
```

#### 2. 安装 pysqlite3

Python 3.6 自带的 sqlite3 模块可能不可用，需要安装 pysqlite3：

```bash
pip3 install pysqlite3-binary
```

#### 3. 使用兼容版本的依赖

系统已针对 Python 3.6 进行优化，依赖版本如下：

| 依赖 | 兼容版本 |
|------|----------|
| fastapi | 0.83.0 |
| uvicorn | 0.16.0 |
| websockets | 9.1 |
| sqlalchemy | 1.4.54 |
| pydantic | 1.9.2 |

使用默认的 requirements.txt 会自动安装兼容版本。

#### 4. 启动服务

```bash
# 方法1：直接运行
cd /opt/command_executor
nohup python3 server/main.py > logs/server.log 2>&1 &
nohup python3 -m uvicorn server.api_server:app --host 0.0.0.0 --port 8080 > logs/api.log 2>&1 &

# 方法2：使用管理脚本
./start.sh
```

---

## 配置说明

### 配置文件位置
```
server/config.py
```

### 配置参数详解

| 参数 | 默认值 | 说明 |
|------|--------|------|
| SERVER_HOST | 0.0.0.0 | 服务端监听地址，0.0.0.0表示监听所有网卡 |
| SERVER_PORT | 8765 | WebSocket服务端口 |
| API_PORT | 8080 | REST API服务端口 |
| DB_HOST | localhost | 数据库主机地址 |
| DB_PORT | 5432 | 数据库端口 |
| DB_NAME | command_executor | 数据库名称 |
| DB_USER | postgres | 数据库用户名 |
| DB_PASSWORD | postgres | 数据库密码 |
| USE_TLS | false | 是否启用TLS加密 |
| TLS_CERT | ./certs/server.crt | TLS证书路径 |
| TLS_KEY | ./certs/server.key | TLS私钥路径 |
| CLIENT_OFFLINE_TIMEOUT | 30 | 客户端离线超时时间（分钟），超过此时长会自动删除绑定 |
| CLIENT_CLEANUP_INTERVAL | 300 | 清理离线客户端的间隔（秒） |

---

## TLS 加密配置

### 概述

TLS（Transport Layer Security）加密可以保护客户端与服务端之间的通信安全。系统支持两种运行模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **非加密模式** (WS) | 数据明文传输 | 内网环境、测试环境 |
| **加密模式** (WSS) | 数据加密传输 | 公网环境、生产环境 |

**重要提示：** 服务端和客户端的TLS设置必须一致，否则无法连接。

### 方式一：启用 TLS 加密

#### 1. 生成自签名证书

```bash
# 创建证书目录
mkdir -p server/certs

# 生成自签名证书（有效期10年）
openssl req -x509 -newkey rsa:4096 -keyout server/certs/server.key -out server/certs/server.crt -days 3650 -nodes -subj "/CN=你的服务器IP"

# 示例：服务器IP为192.168.10.249
openssl req -x509 -newkey rsa:4096 -keyout server/certs/server.key -out server/certs/server.crt -days 3650 -nodes -subj "/CN=192.168.10.249"
```

#### 2. 修改服务端配置

编辑 `server/config.py`：

```python
# TLS配置（启用加密）
USE_TLS = True
TLS_CERT = "server/certs/server.crt"   # 证书文件路径
TLS_KEY = "server/certs/server.key"    # 私钥文件路径
```

#### 3. 重启服务端

```bash
# 查找并终止旧进程
ps aux | grep "server/main.py" | grep -v grep | awk '{print $2}' | xargs kill -9

# 启动新服务
cd /opt/command_executor
nohup python3 server/main.py > logs/server.log 2>&1 &

# 查看日志确认TLS已启用
tail -f logs/server.log
```

成功启动后会看到：
```
[TLS] 已加载证书 - server/certs/server.crt
WebSocket服务启动在 0.0.0.0:8765 - 协议: WSS (TLS加密)
```

#### 4. 配置客户端

客户端配置文件 `client_config.json`：

```json
{
  "server_host": "你的服务器IP",
  "server_port": 8765,
  "use_tls": true
}
```

### 方式二：关闭 TLS 加密

#### 1. 修改服务端配置

编辑 `server/config.py`：

```python
# TLS配置（关闭加密）
USE_TLS = False
TLS_CERT = "server/certs/server.crt"
TLS_KEY = "server/certs/server.key"
```

#### 2. 重启服务端

```bash
# 查找并终止旧进程
ps aux | grep "server/main.py" | grep -v grep | awk '{print $2}' | xargs kill -9

# 启动新服务
cd /opt/command_executor
nohup python3 server/main.py > logs/server.log 2>&1 &

# 查看日志确认TLS已关闭
tail -f logs/server.log
```

成功启动后会看到：
```
WebSocket服务启动在 0.0.0.0:8765 - 协议: WS (非加密)
```

#### 3. 配置客户端

客户端配置文件 `client_config.json`：

```json
{
  "server_host": "你的服务器IP",
  "server_port": 8765,
  "use_tls": false
}
```

### 快速切换脚本

创建一个便捷的切换脚本 `toggle_tls.sh`：

```bash
#!/bin/bash
# TLS 加密切换脚本

CONFIG_FILE="/opt/command_executor/server/config.py"

if [ "$1" == "on" ] || [ "$1" == "ON" ]; then
    echo "启用 TLS 加密..."
    sed -i 's/USE_TLS = False/USE_TLS = True/' "$CONFIG_FILE"
    echo "TLS 已启用，请重启服务端"
elif [ "$1" == "off" ] || [ "$1" == "OFF" ]; then
    echo "关闭 TLS 加密..."
    sed -i 's/USE_TLS = True/USE_TLS = False/' "$CONFIG_FILE"
    echo "TLS 已关闭，请重启服务端"
else
    echo "用法: $0 [on|off]"
    echo "  on  - 启用 TLS 加密"
    echo "  off - 关闭 TLS 加密"
fi
```

使用方法：
```bash
# 启用 TLS
./toggle_tls.sh on

# 关闭 TLS
./toggle_tls.sh off
```

### TLS 证书管理

#### 查看证书信息
```bash
openssl x509 -in server/certs/server.crt -text -noout
```

#### 查看证书有效期
```bash
openssl x509 -in server/certs/server.crt -noout -dates
```

#### 续签证书
```bash
# 备份旧证书
mv server/certs/server.crt server/certs/server.crt.bak
mv server/certs/server.key server/certs/server.key.bak

# 生成新证书
openssl req -x509 -newkey rsa:4096 -keyout server/certs/server.key -out server/certs/server.crt -days 3650 -nodes -subj "/CN=你的服务器IP"

# 重启服务
```

### 常见问题

**Q: 客户端连接失败，提示证书错误？**

A: 客户端已配置为支持自签名证书，确保客户端配置中 `use_tls` 设置为 `true`。

**Q: 如何检查服务端是否启用了 TLS？**

A: 查看服务端日志，确认协议类型：
- WSS (TLS加密) = 已启用
- WS (非加密) = 未启用

**Q: 生产环境建议使用什么证书？**

A: 生产环境建议使用 Let's Encrypt 免费证书或购买商业证书。自签名证书仅适合内网测试。

**Q: 可以同时开启加密和非加密端口吗？**

A: 当前版本不支持。服务端只能运行在一种模式下（加密或非加密）。

### 环境变量配置（可选）
可以通过环境变量覆盖配置文件：

```bash
# Linux
export SERVER_HOST="0.0.0.0"
export SERVER_PORT="8765"
export API_PORT="8080"
export DB_PASSWORD="your_password"

# Windows
set SERVER_HOST=0.0.0.0
set SERVER_PORT=8765
set API_PORT=8080
```

---

## 启动服务

### 开发环境启动
```bash
cd server
python main.py
```

### 生产环境启动（使用 systemd）

#### 创建 systemd 服务文件
```bash
sudo nano /etc/systemd/system/command-executor.service
```

添加以下内容：
```ini
[Unit]
Description=Command Executor Server
After=network.target postgresql.service

[Service]
Type=simple
User=cmdexec
WorkingDirectory=/home/cmdexec/command_executor/server
Environment="PATH=/usr/bin:/home/cmdexec/.local/bin"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启动和管理服务
```bash
# 重载配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start command-executor

# 设置开机自启
sudo systemctl enable command-executor

# 查看状态
sudo systemctl status command-executor

# 查看日志
sudo journalctl -u command-executor -f

# 停止服务
sudo systemctl stop command-executor

# 重启服务
sudo systemctl restart command-executor
```

### Windows 服务启动（可选）

使用 NSSM 将程序注册为 Windows 服务：

```bash
# 下载 NSSM: https://nssm.cc/download

# 安装服务
nssm install CommandExecutor "C:\Python314\python.exe" "E:\knowlegdge_base\python_project\command_executor\server\main.py"
nssm set CommandExecutor AppDirectory "E:\knowlegdge_base\python_project\command_executor\server"

# 启动服务
nssm start CommandExecutor
```

---

## 用户管理

系统 v2.0 引入了完整的用户认证机制，所有API调用都需要用户身份验证。

### 用户管理脚本

服务端提供了用户管理脚本 `server/manage_users.py`，用于管理用户和分配客户端权限。

#### 创建用户

```bash
cd /opt/command_executor
python3 server/manage_users.py add_user <username> <password>
```

**示例：**
```bash
python3 server/manage_users.py add_user alice SecurePass123
```

**输出：**
```
✅ 用户创建成功！
   用户名: alice
   API密钥: cmd_F1VdC0DKCUwXEsIKCAtA0MY5KLjADnWJmF3PZg4wAGk
   创建时间: 2026-01-26 09:33:50.731429
```

#### 分配客户端给用户

用户必须被明确授权才能使用特定客户端：

```bash
python3 server/manage_users.py assign_client <username> <client_id>
```

**示例：**
```bash
# 将客户端 64ECD56E 分配给用户 alice
python3 server/manage_users.py assign_client alice 64ECD56E
```

#### 查看所有用户

```bash
python3 server/manage_users.py list_users
```

**输出示例：**
```
共有 2 个用户：
------------------------------------------------------------
👤 用户名: alice
   状态: ✅ 激活
   API密钥: cmd_F1VdC0DKCUwXEsIKCAtA0MY5KLjADnWJmF3PZg4wAGk
   关联客户端数: 2
   客户端列表: 64ECD56E, 8011835E
   创建时间: 2026-01-26 09:33:50.731429
------------------------------------------------------------
👤 用户名: bob
   状态: ✅ 激活
   API密钥: cmd_XyZ123...
   关联客户端数: 1
   客户端列表: 8011835E
   创建时间: 2026-01-26 10:15:20.123456
------------------------------------------------------------
```

#### 查看用户的客户端列表

```bash
python3 server/manage_users.py user_clients <username>
```

#### 撤销客户端权限

```bash
python3 server/manage_users.py revoke_client <username> <client_id>
```

#### 重置用户密码

```bash
python3 server/manage_users.py reset_password <username> <new_password>
```

#### 显示用户API密钥

```bash
python3 server/manage_users.py show_apikey <username>
```

#### 删除用户

```bash
python3 server/manage_users.py delete_user <username>
```

### 自动绑定与用户切换

#### 工作原理

系统支持客户端自动绑定功能，当用户首次使用某个客户端时，系统会自动创建绑定关系。

**重要特性：设备独占模式**

为确保安全性和权限清晰，系统采用**设备独占模式**：
- 一台客户端设备同时只能绑定到一个用户
- 当用户B使用已绑定到用户A的设备登录时，系统会自动删除用户A的绑定，将设备重新绑定到用户B
- 日志会记录用户切换事件

#### 用户切换流程

```
1. 用户 dzj 使用客户端 5B15DB0C 登录
   → 系统检查发现该客户端未绑定
   → 自动创建绑定：5B15DB0C → dzj
   → 日志：[自动绑定] 成功 - 用户: dzj, 客户端: 5B15DB0C

2. 用户 whn 使用同一台客户端 5B15DB0C 登录
   → 系统检查发现该客户端已绑定到 dzj
   → 自动删除 dzj 的绑定
   → 日志：[自动绑定] 已移除客户端 '5B15DB0C' 的 1 个旧绑定关系（用户切换）
   → 创建新绑定：5B15DB0C → whn
   → 日志：[自动绑定] 成功 - 用户: whn, 客户端: 5B15DB0C

3. 结果：客户端 5B15DB0C 现在只属于 whn
```

#### 配置参数

在 `server/config.py` 中可以调整自动绑定相关配置：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| CLIENT_OFFLINE_TIMEOUT | 30 | 客户端离线超时时间（分钟），超过此时长会自动删除绑定 |
| CLIENT_CLEANUP_INTERVAL | 300 | 清理离线客户端的间隔（秒） |

#### 离线自动注销

系统会定期清理离线超过阈值的客户端绑定关系：

- **默认超时**：30分钟
- **清理逻辑**：客户端离线超过30分钟后，自动删除用户绑定
- **重新绑定**：客户端下次连接时会触发自动绑定，创建新的绑定关系

**日志示例：**
```
[自动注销] 发现 1 个客户端离线超过 30 分钟
[自动注销] 已删除客户端 '5B15DB0C' 与用户 'dzj' 的绑定关系（离线超时）
```

#### 查看用户切换日志

```bash
# 查看服务器日志中的用户切换记录
tail -f /opt/command_executor/logs/server.log | grep "用户切换"

# 查看所有自动绑定记录
tail -f /opt/command_executor/logs/server.log | grep "自动绑定"
```

#### 使用场景

自动绑定功能适用于以下场景：

1. **共享设备环境**：多人共用一台电脑，不同时段使用不同账号登录
2. **设备重新分配**：设备从旧用户转移给新用户
3. **临时借用**：临时使用他人的设备，自动获取设备权限
4. **自助服务**：用户无需管理员手动分配，首次使用即可自动获取权限

#### 注意事项

- **权限转移**：用户切换会导致原用户失去该设备的访问权限
- **审计需求**：所有用户切换都会记录日志，便于审计追踪
- **离线清理**：设备长时间离线会被自动解绑，需要重新登录建立绑定

### 用户管理最佳实践

#### 1. 用户角色分配

建议根据职责创建不同用户：

| 用户类型 | 权限范围 | 示例 |
|---------|---------|------|
| 网络管理员 | 所有网络设备客户端 | net_admin |
| 数据库管理员 | 所有数据库服务器客户端 | db_admin |
| 运维人员 | 特定业务系统的客户端 | ops_user01 |

#### 2. 客户端命名规范

建议使用有意义的客户端识别码：

- 按位置命名：`BJ-IDC-01`, `SH-IDC-02`
- 按用途命名：`SWITCH-CORE-01`, `ROUTER-BRANCH-01`
- 按设备类型：`HUAWEI-SW-001`, `CISCO-FW-001`

#### 3. 权限管理流程

1. **新员工入职**
   ```bash
   # 创建用户
   python3 server/manage_users.py add_user john DoePass123

   # 根据职责分配客户端
   python3 server/manage_users.py assign_client john BJ-IDC-01
   python3 server/manage_users.py assign_client john SWITCH-CORE-01
   ```

2. **员工离职或转岗**
   ```bash
   # 方法一：删除用户
   python3 server/manage_users.py delete_user john

   # 方法二：只撤销客户端权限，保留用户
   python3 server/manage_users.py revoke_client john BJ-IDC-01
   ```

3. **定期审计**
   ```bash
   # 每月审查用户列表
   python3 server/manage_users.py list_users

   # 检查每个用户的客户端权限是否合理
   python3 server/manage_users.py user_clients <username>
   ```

### API 认证

所有 API 调用都需要先登录获取 Token：

#### 登录获取 Token

```bash
curl -k -X POST https://192.168.10.249:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"SecurePass123"}'
```

**响应：**
```json
{
  "access_token": "Kx7j8mN3pQr...",
  "token_type": "bearer",
  "expires_in": 86400,
  "username": "alice",
  "api_key": "cmd_F1VdC0DKCUwXEsIKCAtA0MY5KLjADnWJmF3PZg4wAGk"
}
```

#### 使用 Token 调用 API

```bash
# 获取客户端列表
curl -k https://192.168.10.249:8080/api/clients \
  -H "Authorization: Bearer Kx7j8mN3pQr..."

# 执行命令
curl -k -X POST https://192.168.10.249:8080/api/local/execute \
  -H "Authorization: Bearer Kx7j8mN3pQr..." \
  -H "Content-Type: application/json" \
  -d '{"client_id":"64ECD56E","command":"display version"}'
```

**Token 有效期：** 24小时，过期后需要重新登录。

---

## 维护管理

### 日常监控

#### 查看在线客户端
```bash
curl http://localhost:8080/api/clients/online
```

#### 查看系统日志
```bash
# systemd
sudo journalctl -u command-executor -n 100 -f

# 直接运行时查看控制台输出
```

#### 数据库维护
```sql
-- 连接数据库
psql -U cmdexec_user -d command_executor

-- 查看会话统计
SELECT task_type, success, COUNT(*) as count
FROM sessions
GROUP BY task_type, success;

-- 查看客户端统计
SELECT is_online, COUNT(*) as count
FROM client_connections
GROUP BY is_online;

-- 查看最近会话
SELECT * FROM sessions
ORDER BY created_at DESC
LIMIT 20;
```

### 数据备份

#### SQLite 备份
```bash
cp server/server_data.db backups/server_data_$(date +%Y%m%d_%H%M%S).db
```

#### PostgreSQL 备份
```bash
pg_dump -U cmdexec_user command_executor > backups/command_executor_$(date +%Y%m%d).sql
```

### 自动清理任务
服务端会自动清理超过 90 天的会话记录，无需手动干预。

### 日志级别调整

编辑 `server/config.py`：
```python
LOG_LEVEL = "DEBUG"   # 开发环境
# LOG_LEVEL = "INFO"  # 生产环境
```

---

## 故障排查

### 问题1：服务端无法启动

**症状**：运行 `python main.py` 后立即退出

**排查步骤**：
```bash
# 1. 检查端口占用
netstat -tuln | grep -E "8765|8080"

# 2. 检查 Python 版本
python3 --version  # 需要 3.6+

# 3. 检查依赖安装
pip3 list | grep -E "fastapi|websockets|sqlalchemy"
```

**解决方案**：
- 终止占用端口的进程
- 确认 Python 版本符合要求
- 重新安装依赖

### 问题1.5：Python 3.6 特定问题

**症状**：`ModuleNotFoundError: No module named '_sqlite3'`

**解决方案**：
```bash
pip3 install pysqlite3-binary
```

**症状**：`AttributeError: module 'asyncio' has no attribute 'run'`

**解决方案**：系统已使用 `loop.run_until_complete()` 兼容 Python 3.6，确保使用最新代码。

**症状**：`TypeError: client_handler() takes 2 positional arguments but 3 were given`

**解决方案**：确保 `server/websocket_server.py` 中 `client_handler` 方法签名正确：
```python
async def client_handler(self, ws: WebSocketServerProtocol, path: str):
```

### 问题2：客户端无法连接

**症状**：客户端提示"连接失败"

**排查步骤**：
```bash
# 1. 检查防火墙
sudo ufw status

# 2. 检查服务端监听
netstat -tuln | grep 8765

# 3. 测试端口连通性
telnet server_ip 8765
```

**解决方案**：
```bash
# 开放防火墙端口
sudo ufw allow 8765/tcp

# 检查 config.py 中的 SERVER_HOST 配置
# 应该设置为 "0.0.0.0" 而不是 "127.0.0.1"
```

### 问题3：数据库连接失败

**症状**：日志提示"数据库连接错误"

**排查步骤**：
```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 测试连接
psql -U cmdexec_user -d command_executor -h localhost
```

**解决方案**：
```bash
# 启动 PostgreSQL
sudo systemctl start postgresql

# 验证数据库和用户
sudo -u postgres psql
\l  # 列出数据库
\du  # 列出用户
```

### 问题4：API 返回 500 错误

**症状**：调用 API 时返回 Internal Server Error

**排查步骤**：
```bash
# 查看详细错误日志
sudo journalctl -u command-executor -n 50

# 检查数据库表是否正常创建
python -c "from server.database import init_database; init_database()"
```

### 问题5：内存占用过高

**症状**：服务端进程内存持续增长

**解决方案**：
```bash
# 1. 清理旧会话数据
python -c "from server.database import SessionManager, get_db; db = next(get_db()); print(f'Deleted: {SessionManager.cleanup_old_sessions(db)}')"

# 2. 重启服务
sudo systemctl restart command-executor
```

---

## 安全建议

### 1. 使用 TLS 加密
详见上方 [TLS 加密配置](#tls-加密配置) 章节。

### 2. 数据库安全
- 使用强密码
- 限制数据库只允许本地连接
- 定期更新数据库版本

### 3. 网络安全
- 使用防火墙限制访问
- 考虑使用 VPN 或专线
- 定期检查访问日志

### 4. 更新维护
- 定期更新 Python 依赖：`pip install -r requirements.txt --upgrade`
- 关注安全公告
- 及时修复漏洞

---

## 附录

### 端口说明
| 端口 | 协议 | 说明 |
|------|------|------|
| 8765 | WebSocket | 客户端连接端口 |
| 8080 | HTTP | REST API 端口 |

### 目录结构
```
server/
├── main.py              # 主入口
├── config.py            # 配置文件
├── database.py          # 数据库操作
├── websocket_server.py  # WebSocket服务
├── api_server.py        # REST API
├── requirements.txt     # 依赖列表
└── server_data.db       # SQLite数据库（测试用）
```

### 联系支持
如遇问题，请查看日志文件或联系技术支持。
