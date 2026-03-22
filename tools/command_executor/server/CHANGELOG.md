# 服务端版本更新记录

## 版本历史

### v2.1.0 (2026-01-30)

#### 新增功能
- **Telnet API** - 新增 `/api/telnet/execute` 接口
  - 支持通过 API 执行 Telnet 命令
  - 适用于不支持 SSH 的旧设备
  - 支持自定义登录提示符、密码提示符

- **Telnet 数据模型** - 新增 `TelnetParams` 数据类
  - 定义 Telnet 执行参数
  - 支持超时配置

#### 功能改进
- **HTTPS/TLS 配置** - 修复 API 服务器 HTTPS 配置问题
  - 在 `run_api_server()` 中正确配置 SSL 证书
  - 支持通过环境变量控制 TLS 启用/禁用
  - 自动检测证书文件存在性

- **用户认证** - 完善用户认证机制
  - 创建 root 默认用户
  - 修复密码哈希算法不一致问题
  - 支持用户权限管理

#### 技术更新
- API 服务器启动配置优化：
  ```python
  # 新增 SSL 证书配置
  if USE_TLS:
      ssl_kwargs = {
          "ssl_keyfile": key_path,
          "ssl_certfile": cert_path
      }
  uvicorn.run(app, host=host, port=port, **ssl_kwargs)
  ```

#### 文件变更
- 修改文件：
  - `api_server.py` - 添加 SSL 配置和 Telnet API 接口
  - `config.py` - TLS 配置变量引用

- 新增文件：
  - `CHANGELOG.md` - 版本更新记录

#### Bug 修复
- 修复 API 服务器 HTTPS 连接失败问题
- 修复用户登录时密码验证失败问题
- 修复 TLS 证书路径解析问题

---

### v2.0.0 (2026-01-26)

#### 新增功能
- **REST API 服务** - 基于 FastAPI 的 RESTful API
  - 用户登录认证 (`/api/login`)
  - SSH 命令执行 (`/api/ssh/execute`)
  - HTTP 请求执行 (`/api/http/execute`)
  - 本地命令执行 (`/api/local/execute`)
  - 会话查询 (`/api/sessions/{id}`)
  - 客户端管理 (`/api/clients`)

- **WebSocket 服务** - 与客户端保持长连接
  - 支持 TLS 加密 (WSS)
  - 自动任务分发
  - 实时结果收集

- **用户管理** - 完整的用户权限系统
  - 用户创建、删除
  - 客户端分配
  - 权限控制
  - JWT Token 认证

- **数据库管理** - 基于 SQLAlchemy 的数据持久化
  - 用户管理
  - 客户端管理
  - 会话历史
  - Token 管理

#### 安全特性
- TLS 1.2 加密通信
- 自签名证书支持
- JWT Token 认证（24小时有效期）
- 用户-客户端权限绑定

#### 技术栈
- Python 3.6+ (兼容 CentOS 7)
- FastAPI (Web 框架)
- Uvicorn (ASGI 服务器)
- WebSocket (异步通信)
- SQLAlchemy (ORM)
- SQLite (数据库)

#### API 文档
- Swagger UI 自动生成 (`/docs`)
- OpenAPI 规范 (`/openapi.json`)

---

## 版本说明

### 版本命名规则
- **主版本号 (Major)**: 重大架构变更，不保证向下兼容
- **次版本号 (Minor)**: 新增功能，保持向下兼容
- **修订号 (Patch)**: Bug 修复，小改进

### 部署说明
- 服务端需要 Python 3.6 或更高版本
- 默认端口：
  - WebSocket: 8765 (WSS)
  - REST API: 8080 (HTTPS)
- 依赖包：见 `requirements.txt`

### 配置文件
- 主配置：`server/config.py`
- TLS 证书：`server/certs/server.crt`, `server/certs/server.key`
- 数据库：`server/server_data.db`

### 环境变量
| 变量 | 说明 | 默认值 |
|------|------|--------|
| `USE_TLS` | 启用 TLS | `true` |
| `TLS_CERT` | 证书路径 | `server/certs/server.crt` |
| `TLS_KEY` | 密钥路径 | `server/certs/server.key` |
| `SERVER_HOST` | 服务端地址 | `0.0.0.0` |
| `SERVER_PORT` | WebSocket 端口 | `8765` |
| `API_PORT` | API 端口 | `8080` |

---

## 升级指南

### 从 v2.0.0 升级到 v2.1.0

1. **备份现有数据**
   ```bash
   cp server/server_data.db server/server_data.db.backup
   ```

2. **更新代码文件**
   - 替换 `api_server.py`
   - 替换 `shared/models.py`

3. **更新依赖**
   ```bash
   pip install -r server/requirements.txt
   ```

4. **重启服务**
   ```bash
   # 停止服务
   pkill -f 'python3 server/main.py'

   # 启动服务
   cd /opt/command_executor
   nohup python3 server/main.py > logs/server.log 2>&1 &
   ```

5. **验证升级**
   ```bash
   # 检查 API 服务
   curl -k https://localhost:8080/docs

   # 检查 Telnet API
   curl -k -X POST https://localhost:8080/api/telnet/execute \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"xxx","host":"xxx","port":23,"command":"show version"}'
   ```
