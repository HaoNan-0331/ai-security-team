# API 完整规范

## 基础信息

| 项目 | 说明 |
|------|------|
| Base URL | `https://{server_ip}:8080` |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | Bearer Token |
| 令牌有效期 | 24小时 |
| TLS协议 | TLS 1.2 |

## 认证接口

### 登录获取令牌

```
POST /api/login
```

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 86400,
  "username": "string",
  "api_key": "string"
}
```

**状态码**:
- 200: 成功
- 422: 用户名或密码错误

---

## 客户端管理接口

### 获取所有客户端

```
GET /api/clients
Authorization: Bearer {token}
```

**响应**:
```json
[
  {
    "client_id": "A1B2C3D4",
    "hostname": "DESKTOP-ABC123",
    "os_info": "Windows 10",
    "is_online": true,
    "last_seen": "2026-01-23T08:58:41.918331",
    "first_connected": "2026-01-23T08:54:21.269303"
  }
]
```

### 获取在线客户端

```
GET /api/clients/online
Authorization: Bearer {token}
```

**响应**: 同上，仅返回在线客户端

### 获取客户端详情

```
GET /api/clients/{client_id}
Authorization: Bearer {token}
```

**响应**:
```json
{
  "client_id": "A1B2C3D4",
  "hostname": "DESKTOP-ABC123",
  "os_info": "Windows 10",
  "is_online": true,
  "last_seen": "2026-01-23T08:58:41.918331",
  "first_connected": "2026-01-23T08:54:21.269303"
}
```

---

## 命令执行接口

### 执行SSH命令

```
POST /api/ssh/execute
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "client_id": "string",      // 必填：客户端识别码
  "host": "string",           // 必填：SSH主机地址
  "port": 22,                 // 可选：SSH端口，默认22
  "username": "string",       // 必填：SSH用户名
  "password": "string",       // 必填：SSH密码
  "command": "string",        // 必填：要执行的命令
  "timeout": 30               // 可选：超时时间（秒），默认30
}
```

**响应**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务已发送，等待执行结果"
}
```

### 执行Telnet命令

```
POST /api/telnet/execute
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "client_id": "string",          // 必填：客户端识别码
  "host": "string",               // 必填：Telnet主机地址
  "port": 23,                     // 可选：Telnet端口，默认23
  "username": "string",           // 可选：登录用户名
  "password": "string",           // 可选：登录密码
  "command": "string",            // 必填：要执行的命令
  "timeout": 30,                  // 可选：超时时间（秒），默认30
  "login_prompt": "login:",       // 可选：登录提示符
  "password_prompt": "Password:", // 可选：密码提示符
  "shell_prompt": null            // 可选：Shell提示符
}
```

**响应**: 同SSH

### 执行HTTP请求

```
POST /api/http/execute
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "client_id": "string",      // 必填：客户端识别码
  "url": "string",            // 必填：请求URL
  "method": "GET",            // 必填：HTTP方法 (GET/POST/PUT/DELETE)
  "headers": {},              // 可选：请求头
  "body": "string",           // 可选：请求体
  "timeout": 30               // 可选：超时时间（秒），默认30
}
```

**响应**: 同SSH

### 执行本地命令

```
POST /api/local/execute
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "client_id": "string",      // 必填：客户端识别码
  "command": "string",        // 必填：要执行的命令
  "timeout": 30,              // 可选：超时时间（秒），默认30
  "encoding": "gbk"           // 可选：输出编码，Windows默认gbk，Linux默认utf-8
}
```

**响应**: 同SSH

---

## 结果查询接口

### 查询任务结果

```
GET /api/sessions/{session_id}
Authorization: Bearer {token}
```

**响应**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "A1B2C3D4",
  "task_type": "ssh",
  "request_data": {
    "host": "192.168.1.1",
    "command": "show version"
  },
  "response_data": {
    "stdout": "Device Model: XYZ-1000\nSoftware Version: 1.0.0",
    "stderr": "",
    "exit_code": 0
  },
  "success": true,
  "error_message": null,
  "created_at": "2026-01-23T08:59:01.744250"
}
```

**字段说明**:
- `task_type`: 任务类型 (ssh/http/telnet/local)
- `success`: 是否执行成功
- `response_data.stdout`: 标准输出
- `response_data.stderr`: 标准错误
- `response_data.exit_code`: 退出码（SSH/Local）或HTTP状态码

### 查询客户端历史

```
GET /api/sessions/client/{client_id}?limit=100
Authorization: Bearer {token}
```

**查询参数**:
- `limit`: 返回数量，默认100

**响应**:
```json
[
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_id": "A1B2C3D4",
    "task_type": "ssh",
    "success": true,
    "created_at": "2026-01-23T08:59:01.744250"
  }
]
```

---

## 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| 状态码 | 说明 | 处理方式 |
|--------|------|----------|
| 401 | 未授权（令牌无效或过期） | 重新登录获取Token |
| 403 | 禁止访问（无权使用该客户端） | 联系管理员分配权限 |
| 404 | 资源不存在 | 检查client_id或session_id |
| 422 | 请求参数错误 | 检查请求体格式 |
| 500 | 服务器内部错误 | 查看服务端日志 |

---

## 调用示例

### curl 示例

```bash
# 1. 登录
curl -k -X POST https://192.168.10.249:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecurePass123"}'

# 2. 执行SSH命令
curl -k -X POST https://192.168.10.249:8080/api/ssh/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "client_id": "A1B2C3D4",
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "command": "show version"
  }'

# 3. 查询结果
curl -k https://192.168.10.249:8080/api/sessions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Python 示例

```python
import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DistributedExecutorAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        response = requests.post(
            f"{self.base_url}/api/login",
            json={"username": username, "password": password},
            verify=False
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return True
        return False

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_clients(self):
        response = requests.get(
            f"{self.base_url}/api/clients",
            headers=self._headers(),
            verify=False
        )
        return response.json()

    def execute_ssh(self, client_id, host, username, password, command, timeout=30):
        response = requests.post(
            f"{self.base_url}/api/ssh/execute",
            headers=self._headers(),
            json={
                "client_id": client_id,
                "host": host,
                "port": 22,
                "username": username,
                "password": password,
                "command": command,
                "timeout": timeout
            },
            verify=False
        )
        return response.json()

    def execute_local(self, client_id, command, encoding="gbk", timeout=30):
        response = requests.post(
            f"{self.base_url}/api/local/execute",
            headers=self._headers(),
            json={
                "client_id": client_id,
                "command": command,
                "encoding": encoding,
                "timeout": timeout
            },
            verify=False
        )
        return response.json()

    def get_result(self, session_id, timeout=60, interval=2):
        start = time.time()
        while time.time() - start < timeout:
            response = requests.get(
                f"{self.base_url}/api/sessions/{session_id}",
                headers=self._headers(),
                verify=False
            )
            result = response.json()
            if result.get("response_data") is not None:
                return result
            time.sleep(interval)
        raise TimeoutError(f"任务执行超时: {session_id}")

# 使用示例
api = DistributedExecutorAPI("https://192.168.10.249:8080")
if api.login("admin", "SecurePass123"):
    # 执行本地命令
    result = api.execute_local("A1B2C3D4", "systeminfo", "gbk")
    session = api.get_result(result["session_id"])
    print(session["response_data"]["stdout"])
```
