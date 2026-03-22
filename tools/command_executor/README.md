# 分布式命令执行系统

一个基于 Python 的分布式命令执行系统，支持通过客户端远程执行 SSH 命令、HTTP 请求、Telnet 命令和本地命令。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         分布式命令执行系统                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   用户/API ──► 服务端 ◄────WebSocket长连接────► 客户端              │
│                 │                                     │             │
│            REST API                            ┌──────┴──────┐      │
│         (FastAPI 8080)                        │              │      │
│                                              SSH执行器      HTTP执行器│
│               │                           (Paramiko)      (Requests)  │
│                                              Telnet执行器             │
│               │                           (telnetlib3)               │
│               ▼                              │              │         │
│          SQLite数据库                     本地命令执行器              │
│        (会话历史/客户端信息)                 (subprocess)            │
│                                              │              │         │
│                                              └──────┬──────┘         │
│                                                     │                 │
│                                                     ▼                 │
│                                              目标设备/服务器          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 功能特性

### 服务端
- **用户认证系统**（Token 认证，有效期 24 小时）
- **TLS/SSL 加密通信**（HTTPS + WSS）
- WebSocket 长连接管理（端口 8765）
- REST API 接口（端口 8080）
- 客户端在线状态管理
- 会话历史记录（保留 90 天）
- 自动清理过期数据

### 客户端
- **用户登录认证**（用户名/密码登录获取 Token）
- **TLS 加密通信支持**（TLSv1.2 协议，兼容旧版服务器）
- 自动重连机制（5秒间隔）
- SSH 命令执行（支持华为、H3C、思科等网络设备）
- HTTP 请求（GET/POST/PUT/DELETE）
- **Telnet 命令执行（适用于不支持 SSH 的旧设备）**
- 本地命令执行（Windows/Linux）
- 本地历史记录（保留 180 天）
- 识别码认证
- **支持打包为独立可执行文件**（Windows exe / Linux binary，使用 PyInstaller）

## 技术栈

| 组件 | 技术 |
|------|------|
| 服务端 | Python 3.6+, FastAPI, WebSocket, SQLite |
| 客户端 | Python 3.12+, WebSocket, Paramiko, Requests, Telnetlib3 |
| 通信协议 | WSS (WebSocket Secure) + HTTPS (TLS 1.2) |
| 认证方式 | JWT Token (有效期 24 小时) |
| 打包工具 | PyInstaller |

> **注意**：
> - 服务端已针对 Python 3.6 进行兼容性优化，可在 CentOS 7 等环境中运行
> - 客户端使用 Python 3.12 打包，兼容 Windows 10/11
> - 通信使用 TLS 1.2 加密，确保数据传输安全

## 目录结构

```
command_executor/
├── shared/              # 共享模块
│   ├── models.py        # 数据模型
│   └── models_py36.py   # Python 3.6 兼容版本
├── server/              # 服务端
│   ├── main.py          # 主入口
│   ├── config.py        # 配置
│   ├── database.py      # 数据库操作
│   ├── websocket_server.py  # WebSocket服务
│   ├── api_server.py    # REST API
│   └── requirements.txt # 依赖
├── client/              # 客户端
│   ├── main.py          # 主入口
│   ├── config.py        # 配置管理
│   ├── database.py      # 本地数据库
│   ├── websocket_client.py  # WebSocket客户端
│   ├── ssh_executor.py  # SSH执行
│   ├── http_executor.py # HTTP请求
│   ├── telnet_executor.py # Telnet执行
│   ├── local_executor.py # 本地命令执行
│   └── requirements.txt # 依赖
├── docs/                # 文档
│   ├── SERVER_MANUAL.md
│   ├── CLIENT_MANUAL.md
│   └── API_MANUAL.md
├── dist/                # 打包输出
│   ├── CommandExecutorClient.exe  # 客户端可执行文件
│   └── run_client.bat             # 客户端启动脚本
├── build_client.spec    # 客户端打包配置
├── client_exe_entry.py  # 客户端打包入口
├── deploy_server_ssh.py # SSH部署脚本
├── README.md            # 本文档
└── command_executor.md  # 项目详细分析
```

## 快速开始

### 1. 安装依赖

**服务端：**
```bash
cd server
pip install -r requirements.txt
```

**客户端：**
```bash
cd client
pip install -r requirements.txt
```

### 2. 启动服务端

**Windows：**
```bash
# 方式1：使用脚本
start_server.bat

# 方式2：手动启动
cd server
python main.py
```

**Linux：**
```bash
cd /opt/command_executor
python3 server/main.py
```

服务端将启动：
- **WebSocket 服务**：`wss://0.0.0.0:8765` (TLS 加密)
- **API 服务**：`https://0.0.0.0:8080` (TLS 加密)

### 3. 启动客户端

**方式一：Windows 独立可执行文件（推荐）**
```bash
# 直接运行
dist\CommandExecutorClient.exe

# 或使用批处理文件（可查看错误信息）
dist\run_client.bat
```

**方式二：Linux 独立可执行文件（推荐，无需 Python）**
```bash
# 解压部署包
tar -xzf command-executor-client-linux-x86_64.tar.gz

# 运行安装脚本
sudo ./install.sh

# 启动服务
sudo systemctl start command-executor-client
sudo systemctl enable command-executor-client  # 开机自启
```

详细说明请参考：[客户端使用手册](docs/CLIENT_MANUAL.md)

**方式三：Python 源码运行**
```bash
cd client
python main.py
```

首次运行需要：
1. **配置服务端地址**
   - 服务端IP（如：192.168.31.249）
   - WebSocket 端口（默认：8765）
   - API 端口（默认：8080）
   - 是否启用 TLS（推荐：是）

2. **用户登录**
   - 输入用户名
   - 输入密码
   - 登录成功后显示客户端识别码

### 4. 部署到 Linux 服务器

使用自动部署脚本：
```bash
python deploy_server_ssh.py
```

或手动部署：
```bash
# 1. 复制文件到服务器
scp -r server shared root@192.168.181.132:/opt/command_executor/

# 2. 安装依赖
ssh root@192.168.181.132 "cd /opt/command_executor && pip3 install -r server/requirements.txt"

# 3. 开放防火墙端口
ssh root@192.168.181.132 "firewall-cmd --zone=public --add-port=8765/tcp --permanent && firewall-cmd --zone=public --add-port=8080/tcp --permanent && firewall-cmd --reload"

# 4. 启动服务
ssh root@192.168.181.132 "cd /opt/command_executor && nohup python3 server/main.py > logs/server.log 2>&1 &"
```

## API 使用示例

### 用户登录（获取 Token）

```bash
# 登录获取访问 Token
curl -X POST https://server:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# 响应示例
{
  "access_token": "your_token_here",
  "token_type": "bearer",
  "expires_in": 86400,
  "username": "your_username"
}
```

### 执行 SSH 命令（需要 Token）

```bash
curl -X POST https://server:8080/api/ssh/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "client_id": "64ECD56E",
    "host": "192.168.1.1",
    "port": 22,
    "username": "admin",
    "password": "password",
    "command": "show version",
    "timeout": 30
  }'
```

### 执行 HTTP 请求（需要 Token）

```bash
curl -X POST https://server:8080/api/http/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "client_id": "64ECD56E",
    "url": "https://api.example.com/users",
    "method": "GET",
    "headers": {"Authorization": "Bearer token"},
    "timeout": 30
  }'
```

### 执行 Telnet 命令（需要 Token）

```bash
curl -X POST https://server:8080/api/telnet/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "client_id": "64ECD56E",
    "host": "192.168.1.1",
    "port": 23,
    "username": "admin",
    "password": "password",
    "command": "show version",
    "timeout": 30
  }'
```

### 查询任务结果

```bash
curl http://localhost:8080/api/sessions/{session_id}
```

### 获取在线客户端列表

```bash
curl http://localhost:8080/api/clients/online
```

## API 接口清单

| 接口 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/login` | POST | 否 | 用户登录获取 Token |
| `/api/ssh/execute` | POST | **是** | 执行 SSH 命令 |
| `/api/http/execute` | POST | **是** | 执行 HTTP 请求 |
| `/api/telnet/execute` | POST | **是** | 执行 Telnet 命令 |
| `/api/local/execute` | POST | **是** | 执行本地命令 |
| `/api/sessions/{session_id}` | GET | **是** | 获取会话详情 |
| `/api/sessions/client/{client_id}` | GET | **是** | 获取客户端会话历史 |
| `/api/clients` | GET | **是** | 获取所有客户端 |
| `/api/clients/online` | GET | **是** | 获取在线客户端 |
| `/api/clients/{client_id}` | GET | **是** | 获取客户端详情 |

> **注意**：除 `/api/login` 外，所有接口都需要在 Header 中携带 `Authorization: Bearer <token>`

## API 文档

启动服务端后访问：
- **HTTP 模式**：`http://localhost:8080/docs`
- **HTTPS 模式**：`https://server:8080/docs` （推荐）

查看完整 API 文档（Swagger UI）。

## 详细文档

- [项目详细分析](command_executor.md) - 项目架构、模块关系、通信协议详解
- [服务端部署手册](docs/SERVER_MANUAL.md) - 服务端安装、配置、部署和维护
- [客户端使用手册](docs/CLIENT_MANUAL.md) - 客户端安装、配置和使用
- [API 调用手册](docs/API_MANUAL.md) - API 接口详细说明和调用示例

## 配置说明

### 服务端配置 (`server/config.py`)

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| SERVER_HOST | 服务端监听地址 | 0.0.0.0 |
| SERVER_PORT | WebSocket端口 | 8765 |
| API_PORT | API端口 | 8080 |
| **USE_TLS** | **是否启用TLS** | **True** |
| **TLS_CERT** | **TLS证书路径** | **server/certs/server.crt** |
| **TLS_KEY** | **TLS私钥路径** | **server/certs/server.key** |
| SESSION_HISTORY_RETENTION_DAYS | 会话保留天数 | 90 |
| LOG_LEVEL | 日志级别 | INFO |

### 客户端配置

配置文件 `client/client_config.json`：

```json
{
  "server_host": "192.168.31.249",
  "server_port": 8765,
  "api_port": 8080,
  "use_tls": true,
  "log_level": "INFO",
  "log_max_bytes": 10485760,
  "log_backup_count": 5
}
```

**重要配置项说明：**
- `use_tls`: **强烈建议设置为 true**，启用 TLS 加密通信
- `server_host`: 服务端 IP 地址或域名
- `api_port`: API 服务端口（默认 8080）

## 数据保留策略

| 数据类型 | 保留时间 | 存储位置 |
|----------|----------|----------|
| 服务端会话 | 90天 | SQLite |
| 客户端会话 | 180天 | SQLite |

## 端口说明

| 端口 | 协议 | 服务 | 说明 |
|------|------|------|------|
| **8765** | WSS | WebSocket 客户端长连接 | TLS 加密 |
| **8080** | HTTPS | REST API 接口 | TLS 加密 |

## 安全建议

1. **✅ 生产环境必须启用 TLS**：已默认启用，使用 TLS 1.2 加密
2. **✅ 使用强密码**：用户密码应包含大小写字母、数字和特殊字符
3. **✅ Token 有效期管理**：Token 有效期 24 小时，过期需重新登录
4. **使用防火墙**：限制服务端端口访问，仅允许可信 IP 访问
5. **定期备份**：备份重要数据库文件和配置
6. **日志审计**：定期检查服务端日志，监控异常访问
7. **证书管理**：定期更新 TLS 证书（自签名证书有效期 10 年）

## 故障排查

### 客户端无法连接服务端

1. 检查服务端是否运行：
   ```bash
   netstat -an | findstr "8765 8080"
   ```
2. 检查防火墙设置，确保端口已开放
3. 验证配置文件中的服务端地址和 TLS 设置
4. 测试网络连通性：`ping {server_ip}`
5. 检查服务端日志：`tail -f /tmp/server.log`

### 登录失败

1. 检查用户名和密码是否正确
2. 确认服务端已启动且端口监听正常
3. 检查客户端配置的 `use_tls` 是否与服务端一致
4. 查看客户端日志获取详细错误信息

### SSL/TLS 握手失败

1. 确认服务端和客户端的 `use_tls` 配置一致
2. 检查证书文件是否存在：`ls -l server/certs/`
3. 客户端使用 Python 3.12+ 已配置 TLS 1.2 兼容性
4. 如遇 OpenSSL 3.0 兼容性问题，客户端已自动处理

### WebSocket 连接断开

1. 检查服务端日志中的错误信息
2. 确认数据库架构是否包含 `user_id` 列
3. 检查网络是否稳定，避免频繁断线
4. 查看客户端日志：`cat client/logs/client_YYYYMMDD.log`

### Python 3.6 兼容性问题

在 CentOS 7 等使用 Python 3.6 的环境中可能遇到以下问题：

1. **SQLite3 模块缺失**：
   - 症状：`ModuleNotFoundError: No module named '_sqlite3'`
   - 解决：安装 `pysqlite3-binary`：`pip3 install pysqlite3-binary`

2. **asyncio.run() 不支持**：
   - 症状：`AttributeError: module 'asyncio' has no attribute 'run'`
   - 解决：系统已使用 `loop.run_until_complete()` 兼容 Python 3.6

3. **websockets 参数问题**：
   - 症状：`TypeError: client_handler() takes 2 positional arguments but 3 were given`
   - 解决：确保使用兼容版本的代码

## 许可证

MIT License



● 项目完整文件分析

  📁 根目录文件
  ┌─────────────────────┬──────────────────────────────────────────────────────────────┐
  │        文件         │                             作用                             │
  ├─────────────────────┼──────────────────────────────────────────────────────────────┤
  │ README.md           │ 项目主文档 - 包含架构图、功能特性、快速开始指南              │
  ├─────────────────────┼──────────────────────────────────────────────────────────────┤
  │ start_server.bat    │ Windows服务端启动脚本 - 检查Python环境、安装依赖、启动服务   │
  ├─────────────────────┼──────────────────────────────────────────────────────────────┤
  │ start_client.bat    │ Windows客户端启动脚本 - 检查Python环境、安装依赖、启动客户端 │
  ├─────────────────────┼──────────────────────────────────────────────────────────────┤
  │ client_exe_entry.py │ 客户端打包入口 - PyInstaller打包后exe的入口点                │
  └─────────────────────┴──────────────────────────────────────────────────────────────┘
  ---
  📁 client/ 目录
  ┌─────────────────────┬───────────────────────────────────────────────────────────────────┐
  │        文件         │                               作用                                │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ main.py             │ 客户端主入口 - 交互式CLI、用户登录、配置管理、命令执行统一入口    │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ websocket_client.py │ WebSocket客户端 - 与服务端保持长连接、处理消息收发、自动重连      │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ config.py           │ 配置管理 - 读写/验证客户端配置文件（服务器地址、端口、TLS等）     │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ database.py         │ 本地SQLite数据库 - 存储客户端执行历史（保留180天）                │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ ssh_executor.py     │ SSH命令执行器 - 使用Paramiko执行远程命令（支持华为/H3C/思科设备） │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ http_executor.py    │ HTTP请求执行器 - 使用Requests执行GET/POST/PUT/DELETE请求          │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ telnet_executor.py  │ Telnet命令执行器 - 使用telnetlib3执行Telnet命令（旧设备支持）      │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ local_executor.py   │ 本地命令执行器 - 使用subprocess执行本地系统命令                   │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ requirements.txt    │ 客户端依赖包（websockets、requests、paramiko、colorama等）        │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ .client_id          │ 客户端唯一识别码文件（8位十六进制字符串）                         │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ client_config.json  │ 客户端配置文件示例                                                │
  ├─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ logs/.gitkeep       │ 日志目录占位文件                                                  │
  └─────────────────────┴───────────────────────────────────────────────────────────────────┘
  ---
  📁 server/ 目录
  ┌─────────────────────────┬────────────────────────────────────────────────────────────────┐
  │          文件           │                              作用                              │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ main.py                 │ 服务端主入口 - 并发启动WebSocket服务（8765）和API服务（8080）  │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ websocket_server.py     │ WebSocket服务器 - 管理客户端连接、任务分发、结果收集           │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ api_server.py           │ REST API服务 - FastAPI应用，提供认证和命令执行接口             │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ config.py               │ 服务端配置管理 - 端口、TLS、日志、数据保留期等配置             │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ database.py             │ 数据库操作 - SQLAlchemy ORM，管理用户/客户端/会话/令牌数据     │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ auth.py                 │ 认证模块 - JWT令牌验证、用户认证、权限检查                     │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ manage_users.py         │ 用户管理CLI工具 - 添加/删除用户、分配/撤销客户端权限、重置密码 │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ database_py36.py        │ Python 3.6兼容版数据库模块（CentOS 7兼容）                     │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ websocket_server_tls.py │ TLS加密版WebSocket服务器                                       │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ generate_cert.bat       │ TLS证书生成脚本                                                │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ TLS配置说明.txt         │ TLS配置文档                                                    │
  ├─────────────────────────┼────────────────────────────────────────────────────────────────┤
  │ requirements.txt        │ 服务端依赖包（fastapi、uvicorn、sqlalchemy、python-jose等）    │
  └─────────────────────────┴────────────────────────────────────────────────────────────────┘
  ---
  📁 shared/ 目录
  ┌────────────────┬──────────────────────────────────────────────────────────────────────┐
  │      文件      │                                 作用                                 │
  ├────────────────┼──────────────────────────────────────────────────────────────────────┤
  │ models.py      │ 通信数据模型 - TaskMessage、TaskResult、ClientRegister等Pydantic模型 │
  ├────────────────┼──────────────────────────────────────────────────────────────────────┤
  │ models_py36.py │ Python 3.6兼容版数据模型                                             │
  └────────────────┴──────────────────────────────────────────────────────────────────────┘
  ---
  📁 docs/ 目录
  ┌──────────────────┬─────────────────────────────┐
  │       文件       │            作用             │
  ├──────────────────┼─────────────────────────────┤
  │ CLIENT_MANUAL.md │ 客户端使用手册              │
  ├──────────────────┼─────────────────────────────┤
  │ SERVER_MANUAL.md │ 服务端部署手册              │
  ├──────────────────┼─────────────────────────────┤
  │ API_MANUAL.md    │ API调用手册（含多语言示例） │
  ├──────────────────┼─────────────────────────────┤
  │ BUILD_MANUAL.md  │ 客户端打包说明              │
  └──────────────────┴─────────────────────────────┘
  ---
  📁 其他文件
  ┌────────────────────────────┬──────────────────────────────────────┐
  │            文件            │                 作用                 │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ auth_update.zip            │ 认证系统更新包（用于远程服务器更新） │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ deploy.py                  │ 部署脚本                             │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ deploy_server_ssh.py       │ SSH自动部署到Linux服务器             │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ deploy_server_to_linux.ps1 │ PowerShell部署脚本                   │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ deploy_python3_portable.py │ Python便携版部署                     │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ install_python.py          │ Python安装脚本                       │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ install_python3_linux.py   │ Linux Python安装脚本                 │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ login.py                   │ 登录脚本                             │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ login.ps1                  │ PowerShell登录脚本                   │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ user_client_manager.py     │ 用户客户端管理工具                   │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ build_client.spec          │ PyInstaller打包配置                  │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ build_client.bat           │ 客户端构建脚本                       │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ dist/                      │ 打包输出目录                         │
  └────────────────────────────┴──────────────────────────────────────┘
  ---
  系统架构关系图

  ┌─────────────────────────────────────────────────────────────┐
  │                        用户/浏览器                          │
  └──────────────────────────┬──────────────────────────────────┘
                             │ HTTPS
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                      服务端 (server/)                       │
  ├─────────────────────────────────────────────────────────────┤
  │  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
  │  │ api_server  │    │ websocket_   │    │  database    │  │
  │  │  :8080      │◄──►│  server      │◄──►│  (SQLite)    │  │
  │  │ (FastAPI)   │    │  :8765       │    │              │  │
  │  └──────┬──────┘    └──────┬───────┘    └──────────────┘  │
  │         │                  │                                 │
  │         │ auth.py          │ manage_users.py                │
  │         ▼                  ▼                                 │
  │  用户认证 ←────────── 用户管理                              │
  └─────────────────────────────────────────────────────────────┘
                             │ WSS + TLS
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                      客户端 (client/)                       │
  ├─────────────────────────────────────────────────────────────┤
  │  ┌──────────────┐   ┌──────────────────────────────────┐  │
  │  │  websocket_  │   │  命令执行器                       │  │
  │  │   client     │──►│  ├── ssh_executor.py (远程设备)  │  │
  │  │              │   │  ├── http_executor.py (API调用)  │  │
  │  │              │   │  ├── telnet_executor.py (旧设备) │  │
  │  └──────────────┘   │  └── local_executor.py (本地)    │  │
  │         │           └──────────────────────────────────┘  │
  │         ▼                      ▼                           │
  │  config.py ←───────── database.py (本地历史)               │
  └─────────────────────────────────────────────────────────────┘

  核心数据流

  认证流程：用户登录 → JWT令牌 → API请求 → 权限验证 → 执行命令

  命令执行流程：API接收请求 → WebSocket分发任务 → 客户端执行 → 返回结果 → 记录历史