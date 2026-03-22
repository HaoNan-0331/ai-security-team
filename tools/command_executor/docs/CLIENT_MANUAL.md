# 客户端使用手册

## 目录
- [系统要求](#系统要求)
- [安装部署](#安装部署)
- [配置说明](#配置说明)
- [用户认证](#用户认证)
- [启动客户端](#启动客户端)
- [识别码管理](#识别码管理)
- [维护管理](#维护管理)
- [故障排查](#故障排查)

---

## 系统要求

### 硬件要求
- CPU: 1核及以上
- 内存: 2GB及以上
- 硬盘: 5GB及以上

### 软件要求
- 操作系统: Windows / Linux / macOS
- Python: 3.6 或更高版本

### 网络要求
- 能够访问服务端的 IP 和端口
- 稳定的网络连接

---

## 安装部署

### Windows 系统安装

#### 1. 安装 Python
下载并安装 Python 3.10+：https://www.python.org/downloads/

安装时勾选 **"Add Python to PATH"**

#### 2. 获取项目代码
将 `command_executor` 文件夹复制到目标位置，例如：
```
C:\Program Files\command_executor\
```

#### 3. 安装依赖
打开命令提示符（CMD）或 PowerShell：
```bash
cd C:\Program Files\command_executor\client
pip install -r requirements.txt
```

### Linux 系统安装

#### 方式1：独立可执行文件部署（推荐，无需 Python 环境）

**适用场景**：目标机器没有安装 Python 或不想安装 Python 依赖

##### 1. 获取部署包

下载 `command-executor-client-linux-x86_64.tar.gz` 部署包（14MB）

##### 2. 解压并安装

```bash
# 解压
tar -xzf command-executor-client-linux-x86_64.tar.gz
cd /path/to/command-executor-client-linux-x86_64

# 运行安装脚本（推荐）
sudo ./install.sh
```

安装脚本会自动：
- 将程序复制到 `/opt/command-executor-client/`
- 安装 systemd 服务
- 创建命令行快捷方式 `cec`

##### 3. 配置和启动

```bash
# 方式1：直接运行测试
./command-executor-client

# 方式2：使用快捷方式（如果已安装）
cec

# 方式3：作为系统服务运行
sudo systemctl start command-executor-client
sudo systemctl enable command-executor-client  # 开机自启
```

##### 4. 管理服务

```bash
# 查看状态
sudo systemctl status command-executor-client

# 查看日志
sudo journalctl -u command-executor-client -f

# 停止服务
sudo systemctl stop command-executor-client

# 重启服务
sudo systemctl restart command-executor-client
```

##### 5. 卸载

```bash
# 运行卸载脚本
sudo ./uninstall.sh
```

**系统要求**：
- Linux x86_64 架构
- 兼容发行版：CentOS 7+、RHEL 7+、Rocky Linux、AlmaLinux、Fedora、Debian 10+、Ubuntu 18.04+
- **无需**安装 Python 或任何依赖

#### 方式2：Python 源码运行（需要 Python 环境）

##### 1. 安装 Python
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip -y

# CentOS/RHEL
sudo yum install python3 python3-pip -y
```

##### 2. 获取项目代码
```bash
# 创建目录
sudo mkdir -p /opt/command_executor
cd /opt/command_executor

# 上传或解压项目文件
```

##### 3. 安装依赖
```bash
cd /opt/command_executor/client
pip3 install -r requirements.txt
```

##### 4. 设置执行权限（可选）
```bash
chmod +x start_client.sh
```

##### 5. 启动客户端
```bash
# 使用启动脚本
./start_client.sh

# 或直接运行
python3 main.py
```

---

## 配置说明

### 首次配置

客户端首次运行时会自动进入配置向导：

```bash
cd client
python main.py
```

按照提示输入：
```
=== 客户端首次配置 ===
请输入服务端连接信息:
提示: 输入 'q' 可返回主菜单

服务端IP地址: 192.168.1.100
服务端端口: 8765
使用TLS加密? (y/n): n

✅ 配置已保存!
```

**配置说明**：
- 所有输入项都有格式校验
- 输入格式错误时会提示，需要重新输入
- 输入 `q` 可随时取消配置并返回主菜单
- IP 地址支持 IPv4 格式（如 192.168.1.1）和主机名（如 localhost）

### 配置文件说明

配置文件位置：`client/client_config.json`

```json
{
  "server_host": "192.168.1.100",
  "server_port": 8765,
  "use_tls": false
}
```

### 修改配置

#### 方式1：通过客户端菜单

```bash
python main.py
# 选择 "2. 修改配置"
```

修改配置菜单：
```
=== 修改客户端配置 ===
当前配置:
  服务端地址: 192.168.1.100:8765
  使用TLS: 否

请选择要修改的项:
1. 修改服务端地址
2. 修改端口号
3. 修改TLS设置
0. 返回主菜单

请选择 [0-3]:
```

**修改说明**：
- 选择对应数字进入修改项
- 输入 `q` 可取消当前修改
- 修改后立即生效并保存

#### 方式2：直接编辑配置文件
```bash
# Windows
notepad client_config.json

# Linux
nano client_config.json
```

编辑后保存即可，无需重启客户端。

### 高级配置选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| server_host | 服务端IP地址或域名 | 127.0.0.1 |
| server_port | 服务端WebSocket端口 | 8765 |
| use_tls | 是否使用TLS加密连接 | false |

---

## 用户认证

### 什么是用户认证

从 v2.0 版本开始，客户端引入了用户认证机制：

- **用户身份验证**：客户端启动时需要输入用户名和密码
- **访问令牌**：登录成功后获取临时访问令牌（24小时有效期）
- **客户端权限**：用户只能使用已被分配给他们的客户端
- **API认证**：所有API调用都需要携带有效的访问令牌

### 认证流程

#### 步骤1：用户创建（由管理员操作）

用户创建由服务端管理员通过管理脚本完成：

```bash
# 在服务端运行
cd server
python manage_users.py add_user testuser Test@12345
```

#### 步骤2：分配客户端（由管理员操作）

管理员将特定客户端分配给用户：

```bash
python manage_users.py assign_client testuser A1B2C3D4
```

#### 步骤3：客户端登录认证

客户端启动时会提示输入用户名和密码：

```bash
python main.py
```

```
╔═══════════════════════════════════════════════════════╗
║        分布式命令执行系统 - 客户端 v1.0                 ║
╚═══════════════════════════════════════════════════════╝

═════════════════════════════════════════════════════════
  客户端识别码: A1B2C3D4
═════════════════════════════════════════════════════════

请输入用户名: testuser
请输入密码: ********

正在验证用户身份...
✅ 登录成功！正在连接到服务端...
```

#### 步骤4：连接服务端

客户端携带访问令牌连接到服务端，服务端验证：
- 令牌是否有效
- 用户是否被分配了该客户端

验证通过后客户端正常工作。

### 认证示例

#### 示例1：首次登录

```
$ python main.py

请输入用户名: john
请输入密码: ********

正在验证用户身份...
⚠️  登录失败：用户名或密码错误
请重试...

请输入用户名: john
请输入密码: ************

✅ 登录成功！正在连接到服务端...
服务端地址: 192.168.1.100:8765
使用TLS: True

[连接] 客户端已注册 - ID: A1B2C3D4, 用户: john
[连接] 等待服务端任务...
```

#### 示例2：无权限使用客户端

```
请输入用户名: alice
请输入密码: ********

✅ 登录成功！正在连接到服务端...

[连接] 认证失败：用户 'alice' 无权使用客户端 'A1B2C3D4'
[错误] 连接被服务端拒绝
```

**解决方案**：联系管理员为用户分配该客户端。

### 访问令牌说明

| 属性 | 说明 |
|------|------|
| 获取方式 | 通过 `/api/login` 接口登录获取 |
| 有效期 | 24小时 |
| 存储位置 | 客户端内存，不持久化存储 |
| 传递方式 | WebSocket连接注册消息中携带 |
| 安全性 | 使用加密连接（TLS）传输 |

### API调用认证

如果直接调用服务端API，需要使用访问令牌：

```bash
# 1. 获取访问令牌
curl -X POST http://server:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Test@12345"}'

# 响应：{"access_token": "xxxxxxxxxx", "token_type": "bearer"}

# 2. 使用令牌调用API
curl -X POST http://server:8080/api/ssh/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer xxxxxxxxxx" \
  -d '{
    "client_id": "A1B2C3D4",
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "command": "show version"
  }'
```

### 常见认证问题

#### 问题1：登录提示"连接失败"

**症状**：输入用户名密码后提示"连接失败"

**原因**：
- 无法访问服务端API接口（8080端口）
- 网络不通
- 服务端未启动

**解决方案**：
```bash
# 检查网络连通性
ping 192.168.1.100

# 检查API端口是否开放
telnet 192.168.1.100 8080

# 确认服务端是否运行
# （联系管理员检查）
```

#### 问题2：登录成功但连接时提示"无权使用客户端"

**原因**：管理员未将当前客户端分配给该用户

**解决方案**：
- 联系管理员分配客户端
- 确认客户端识别码是否正确

#### 问题3：连接一段时间后断开

**原因**：访问令牌24小时后过期

**解决方案**：
- 重启客户端重新登录
- 确保24小时内至少重启一次客户端

---

## 启动客户端

### Windows 系统

#### 方式1：双击启动脚本
双击 `start_client.bat`

#### 方式2：命令行启动
```bash
cd client
python main.py
```

#### 方式3：后台运行
```bash
# 使用 pythonw 运行（无窗口）
cd client
pythonw run_client.py
```

### Linux 系统

#### 方式1：直接运行
```bash
cd /opt/command_executor/client
python3 main.py
```

#### 方式2：使用 systemd 服务（推荐）

创建服务文件：
```bash
sudo nano /etc/systemd/system/command-executor-client.service
```

添加以下内容：
```ini
[Unit]
Description=Command Executor Client
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/command_executor/client
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
# 重载配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start command-executor-client

# 设置开机自启
sudo systemctl enable command-executor-client

# 查看状态
sudo systemctl status command-executor-client

# 查看日志
sudo journalctl -u command-executor-client -f
```

#### 方式3：使用 screen 或 tmux
```bash
# screen
screen -S cmdexec_client
cd /opt/command_executor/client
python3 main.py
# 按 Ctrl+A 然后按 D 退出屏幕

# 恢复屏幕
screen -r cmdexec_client

# tmux
tmux new -s cmdexec_client
cd /opt/command_executor/client
python3 main.py
# 按 Ctrl+B 然后按 D 退出会话

# 恢复会话
tmux attach -t cmdexec_client
```

### 启动界面示例

```
╔═══════════════════════════════════════════════════════╗
║        分布式命令执行系统 - 客户端 v1.0                 ║
╚═══════════════════════════════════════════════════════╝

═════════════════════════════════════════════════════════
  客户端识别码: A1B2C3D4
═════════════════════════════════════════════════════════

正在连接到服务端...
服务端地址: 192.168.1.100:8765
使用TLS: False

按 Ctrl+C 停止客户端

2026-01-23 16:58:41 - INFO - 正在连接到服务端: ws://192.168.1.100:8765
2026-01-23 16:58:41 - INFO - 客户端已注册: A1B2C3D4 (DESKTOP-ABC123)
2026-01-23 16:58:41 - INFO - 等待服务端任务...
```

---

## 识别码管理

### 什么是识别码

识别码是客户端的唯一标识符，用于服务端识别和路由任务。

### 查看识别码

#### 方式1：启动时查看
客户端启动时会显示识别码：
```
客户端识别码: A1B2C3D4
```

#### 方式2：通过菜单查看
```bash
python main.py
# 选择 "3. 查看识别码"
```

#### 方式3：查看识别码文件
识别码存储在 `client/.client_id` 文件中：
```bash
cat .client_id
```

### 识别码格式

- 长度：8个字符
- 格式：大写字母和数字组合
- 示例：`A1B2C3D4`

### 重置识别码

如果需要重新生成识别码：

```bash
# 删除识别码文件
rm .client_id

# 重新启动客户端
python main.py
```

### 使用识别码

识别码用于API调用时的 `client_id` 参数：
```bash
curl -X POST http://server:8080/api/ssh/execute \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "A1B2C3D4",
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "command": "show version"
  }'
```

---

## 维护管理

### 日常监控

#### 查看连接状态
客户端日志会显示连接状态：
```
INFO - 正在连接到服务端: ws://192.168.1.100:8765
INFO - 客户端已注册: A1B2C3D4
INFO - 等待服务端任务...
```

#### 查看本地历史记录
客户端历史存储在 `client/client_history.db`（SQLite）

```bash
# 查询最近10条记录
sqlite3 client_history.db "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10;"
```

### 数据清理

客户端会自动清理超过 6 个月的历史记录。

手动清理：
```bash
# 删除历史数据库
rm client_history.db
# 客户端启动时会自动重建
```

### 配置备份

```bash
# 备份配置和识别码
cp client_config.json client_config.json.backup
cp .client_id .client_id.backup
```

### 日志级别调整

编辑 `client/main.py`：
```python
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 查看详细日志
    # level=logging.INFO,  # 正常日志
    format="%(asctime)s - %(levelname)s - %(message)s"
)
```

---

## 故障排查

### 问题1：客户端无法启动

**症状**：运行 `python main.py` 后报错

**排查步骤**：
```bash
# 1. 检查 Python 版本
python --version  # 需要 3.10+

# 2. 检查依赖安装
pip list | grep -E "websockets|paramiko|requests"

# 3. 检查文件完整性
ls -la main.py config.py
```

**解决方案**：
```bash
# 重新安装依赖
pip install -r requirements.txt

# 确保 Python 路径正确
which python
```

### 问题2：无法连接到服务端

**症状**：日志显示"连接失败"或"连接超时"

**排查步骤**：
```bash
# 1. 检查网络连通性
ping 192.168.1.100

# 2. 检查端口是否开放
telnet 192.168.1.100 8765

# 3. 检查配置文件
cat client_config.json
```

**解决方案**：
- 检查服务端是否运行
- 检查防火墙设置
- 验证服务端IP和端口是否正确
- 确认网络是否可达

### 问题3：连接后频繁断线

**症状**：客户端连接后经常断开重连

**可能原因**：
1. 网络不稳定
2. 服务端重启
3. 防火墙中断长连接

**解决方案**：
- 检查网络质量
- 查看服务端日志
- 调整防火墙超时设置
- 客户端会自动重连，无需干预

### 问题4：任务执行失败

**症状**：服务端发送任务但客户端执行失败

**排查步骤**：
```bash
# 查看客户端日志
tail -f /var/log/command-executor-client.log

# 或查看控制台输出
```

**常见错误**：
- SSH连接失败：检查目标设备是否可达
- 认证失败：检查用户名密码
- 命令超时：增加超时时间
- 命令错误：验证命令语法

### 问题5：识别码丢失

**症状**：重启后识别码变化

**原因**：`.client_id` 文件丢失

**解决方案**：
```bash
# 检查识别码文件是否存在
ls -la .client_id

# 如果丢失，恢复备份
cp .client_id.backup .client_id
```

---

## 附录

### 功能特性

| 功能 | 说明 |
|------|------|
| 自动重连 | 连接断开后自动尝试重连 |
| 任务串行执行 | 同一时间只执行一个任务 |
| 本地历史记录 | 自动保存最近6个月的执行记录 |
| 跨平台 | 支持 Windows、Linux、macOS |

### 支持的任务类型

| 类型 | 说明 |
|------|------|
| SSH | 执行远程SSH命令 |
| HTTP | 发送HTTP/HTTPS请求 |
| Telnet | 执行Telnet命令（适用于旧设备） |
| Local | 执行客户端本地命令（系统巡检、配置查看等） |

### 目录结构
```
client/
├── main.py              # 主入口
├── config.py            # 配置管理
├── database.py          # 本地数据库
├── websocket_client.py  # WebSocket客户端
├── ssh_executor.py      # SSH执行
├── http_executor.py     # HTTP请求
├── telnet_executor.py   # Telnet执行
├── local_executor.py    # 本地命令执行
├── requirements.txt     # 依赖列表
├── client_config.json   # 配置文件
├── .client_id          # 识别码文件
└── client_history.db    # 历史数据库
```

### 端口说明
客户端作为连接发起方，无需开放端口。

### 注意事项

1. **安全性**
   - 保护好识别码，避免泄露
   - 定期更新依赖版本
   - 不要在公共网络使用明文传输

2. **性能**
   - 单个客户端同时只执行一个任务
   - 如需更高并发，可部署多个客户端

3. **兼容性**
   - SSH 支持 SSHv2 协议
   - HTTP 支持 HTTP/1.1 和 HTTP/2
   - 本地命令支持 Windows CMD、Linux Shell、macOS Terminal

---

## 常见问题 FAQ

**Q: 客户端可以同时连接多个服务端吗？**
A: 不可以，一个客户端只能连接一个服务端。如需连接多个，可运行多个客户端实例。

**Q: 识别码会重复吗？**
A: 不会，识别码使用 UUID 生成，全局唯一。

**Q: 客户端占用多少资源？**
A: 正常情况下 CPU <1%，内存 <50MB。

**Q: 如何卸载客户端？**
A: 停止客户端进程，删除项目文件夹即可。

**Q: 客户端支持代理吗？**
A: 当前版本不支持，后续版本可能会添加。

**Q: 本地命令执行有权限限制吗？**
A: 客户端是纯粹执行器，不做权限检查。调用方应自行控制执行命令的合法性和安全性。

**Q: 支持执行哪些本地命令？**
A: 支持客户端系统支持的所有命令（Windows CMD、Linux Shell 等）。
