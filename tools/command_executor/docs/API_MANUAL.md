# API 调用手册

## 目录
- [API 概述](#api-概述)
- [快速开始](#快速开始)
- [认证说明](#认证说明)
- [API 接口](#api-接口)
- [调用示例](#调用示例)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## API 概述

### 基本信息

| 项目 | 说明 |
|------|------|
| Base URL | `https://your-server:8080` (TLS 加密已启用) |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | Bearer Token (需先登录获取) |
| 令牌有效期 | 24小时 |
| 兼容性 | Python 3.6+ |
| TLS协议 | TLS 1.2 |

> ⚠️ **重要提示**：
> - 系统已强制启用 TLS 加密，所有 API 调用必须使用 HTTPS
> - 使用 curl 时需要添加 `-k` 参数跳过自签名证书验证
> - Python 等编程语言需要配置 SSL 上下文以允许自签名证书

### API 列表

| 接口 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/login` | POST | 否 | 用户登录获取访问令牌 |
| `/api/ssh/execute` | POST | 是 | 执行SSH命令 |
| `/api/http/execute` | POST | 是 | 执行HTTP请求 |
| `/api/telnet/execute` | POST | 是 | 执行Telnet命令 |
| `/api/local/execute` | POST | 是 | 执行客户端本地命令 |
| `/api/sessions/{id}` | GET | 是 | 查询任务结果 |
| `/api/sessions/client/{id}` | GET | 是 | 查询客户端历史 |
| `/api/clients` | GET | 是 | 获取所有客户端 |
| `/api/clients/online` | GET | 是 | 获取在线客户端 |
| `/api/clients/{id}` | GET | 是 | 获取客户端详情 |
| `/docs` | GET | 否 | API 文档（Swagger UI） |

---

## 快速开始

### 1. 获取访问令牌

首先调用登录接口获取访问令牌：

```bash
curl -k -X POST https://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

> 💡 **说明**：`-k` 参数用于跳过自签名证书验证。生产环境中建议使用正式CA签发的证书并移除此参数。

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 2. 获取客户端识别码

启动客户端后，记录显示的识别码（或使用管理员分配的客户端ID）：
```
客户端识别码: A1B2C3D4
```

### 3. 执行第一个任务

```bash
# 执行HTTP请求（携带访问令牌）
curl -k -X POST https://localhost:8080/api/http/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "client_id": "A1B2C3D4",
    "url": "https://httpbin.org/get",
    "method": "GET"
  }'
```

返回：
```json
{
  "session_id": "70a69a2c-9e69-4a6d-8d65-4f4da35d57e9",
  "message": "任务已发送，等待执行结果"
}
```

### 4. 查询结果

```bash
curl -k https://localhost:8080/api/sessions/70a69a2c-9e69-4a6d-8d65-4f4da35d57e9 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 认证说明

### 认证机制

从 v2.0 版本开始，API 使用基于令牌的认证机制：

1. **用户登录**：调用 `/api/login` 接口，使用用户名和密码获取访问令牌
2. **携带令牌**：所有API调用必须在 HTTP Header 中携带访问令牌
3. **权限验证**：服务端验证令牌有效性以及用户对客户端的使用权限
4. **令牌过期**：访问令牌有效期为 24 小时，过期后需重新登录

### 登录接口

**接口**：`POST /api/login`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**响应**：

```json
{
  "access_token": "xxxxxxxxxx",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 使用访问令牌

在所有需要认证的API调用中，添加以下 HTTP Header：

```
Authorization: Bearer <access_token>
```

示例：

```bash
curl -k -X POST https://localhost:8080/api/ssh/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token_here" \
  -d '{
    "client_id": "A1B2C3D4",
    "host": "192.168.1.1",
    "username": "admin",
    "password": "password",
    "command": "show version"
  }'
```

### 权限说明

- 用户只能使用管理员分配给他们的客户端
- 尝试使用未分配的客户端会返回 `403 Forbidden` 错误
- 令牌过期后返回 `401 Unauthorized` 错误

### 错误处理

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 401 | 未提供认证凭据或令牌无效 | 检查 Authorization Header 或重新登录 |
| 403 | 无权使用指定客户端 | 联系管理员分配客户端权限 |
| 422 | 用户名或密码错误 | 检查登录凭据 |

---

## API 接口

### 1. 执行 SSH 命令

**接口**：`POST /api/ssh/execute`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| client_id | string | 是 | 客户端识别码 |
| host | string | 是 | SSH主机地址 |
| port | integer | 是 | SSH端口，默认22 |
| username | string | 是 | SSH用户名 |
| password | string | 是 | SSH密码 |
| command | string | 是 | 要执行的命令 |
| timeout | integer | 否 | 超时时间（秒），默认30 |

**请求示例**：
```json
{
  "client_id": "A1B2C3D4",
  "host": "192.168.1.1",
  "port": 22,
  "username": "admin",
  "password": "password123",
  "command": "show version",
  "timeout": 30
}
```

**响应示例**：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务已发送，等待执行结果"
}
```

---

### 2. 执行 Telnet 命令

**接口**：`POST /api/telnet/execute`

**说明**：执行 Telnet 命令，适用于不支持 SSH 的旧设备。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| client_id | string | 是 | 客户端识别码 |
| host | string | 是 | Telnet主机地址 |
| port | integer | 是 | Telnet端口，默认23 |
| username | string | 否 | 登录用户名（可选） |
| password | string | 否 | 登录密码（可选） |
| command | string | 是 | 要执行的命令 |
| timeout | integer | 否 | 超时时间（秒），默认30 |
| login_prompt | string | 否 | 登录提示符，默认"login:" |
| password_prompt | string | 否 | 密码提示符，默认"Password:" |
| shell_prompt | string | 否 | Shell提示符（可选） |

**请求示例**：
```json
{
  "client_id": "A1B2C3D4",
  "host": "192.168.1.1",
  "port": 23,
  "username": "admin",
  "password": "password123",
  "command": "show version",
  "timeout": 30,
  "login_prompt": "login:",
  "password_prompt": "Password:",
  "shell_prompt": null
}
```

**响应示例**：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440003",
  "message": "Telnet任务已发送"
}
```

---

### 3. 执行 HTTP 请求

**接口**：`POST /api/http/execute`

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| client_id | string | 是 | 客户端识别码 |
| url | string | 是 | 请求URL |
| method | string | 是 | HTTP方法：GET/POST/PUT/DELETE |
| headers | object | 否 | 请求头 |
| body | string | 否 | 请求体 |
| timeout | integer | 否 | 超时时间（秒），默认30 |

**请求示例**：
```json
{
  "client_id": "A1B2C3D4",
  "url": "https://api.example.com/users",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer token123"
  },
  "body": "{\"name\":\"test\"}",
  "timeout": 30
}
```

**响应示例**：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "message": "任务已发送，等待执行结果"
}
```

---

### 4. 执行客户端本地命令

**接口**：`POST /api/local/execute`

**说明**：在客户端本地执行命令，用于系统巡检、配置查看、故障诊断等

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| client_id | string | 是 | 客户端识别码 |
| command | string | 是 | 要执行的命令 |
| timeout | integer | 否 | 超时时间（秒），默认30 |
| encoding | string | 否 | 输出编码，Windows默认gbk，Linux默认utf-8 |

**请求示例**：
```json
{
  "client_id": "A1B2C3D4",
  "command": "systeminfo",
  "timeout": 30,
  "encoding": "gbk"
}
```

**响应示例**：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440002",
  "message": "本地命令任务已发送"
}
```

**注意事项**：
- 客户端是纯粹执行器，不做权限检查
- 调用方应自行控制执行内容的合法性和安全性
- Windows 命令建议使用 `encoding: "gbk"`
- 可以执行任何客户端系统支持的命令

---

### 5. 查询任务结果

**接口**：`GET /api/sessions/{session_id}`

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话ID |

**响应示例**：
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

**响应字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| stdout | string | 标准输出 |
| stderr | string | 标准错误 |
| exit_code | integer | 退出码（SSH）或状态码（HTTP） |

---

### 6. 查询客户端历史

**接口**：`GET /api/sessions/client/{client_id}`

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | integer | 否 | 返回数量，默认100 |

**请求示例**：
```bash
curl -k "https://localhost:8080/api/sessions/client/A1B2C3D4?limit=10" \
  -H "Authorization: Bearer your_access_token_here"
```

**响应示例**：
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

### 7. 获取在线客户端

**接口**：`GET /api/clients/online`

**响应示例**：
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

---

### 8. 获取所有客户端

**接口**：`GET /api/clients`

**响应示例**：同上，包含在线和离线的所有客户端。

---

### 9. 获取客户端详情

**接口**：`GET /api/clients/{client_id}`

**响应示例**：
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

## 调用示例

### Python 示例

```python
import requests
import time
import urllib3
import ssl

# 禁用SSL警告（仅用于自签名证书）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8080"
CLIENT_ID = "A1B2C3D4"

# 全局存储访问令牌
ACCESS_TOKEN = None

# 0. 用户登录获取访问令牌
def login(username, password):
    global ACCESS_TOKEN
    response = requests.post(f"{BASE_URL}/api/login",
        json={
            "username": username,
            "password": password
        },
        verify=False  # 跳过SSL证书验证（自签名证书）
    )
    if response.status_code == 200:
        data = response.json()
        ACCESS_TOKEN = data["access_token"]
        print(f"✅ 登录成功！访问令牌: {ACCESS_TOKEN[:20]}...")
        return True
    else:
        print(f"❌ 登录失败: {response.status_code}")
        return False

# 获取认证 Headers
def get_auth_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

# 1. 执行SSH命令
def execute_ssh(host, username, password, command):
    response = requests.post(
        f"{BASE_URL}/api/ssh/execute",
        headers=get_auth_headers(),
        json={
            "client_id": CLIENT_ID,
            "host": host,
            "port": 22,
            "username": username,
            "password": password,
            "command": command
        },
        verify=False  # 跳过SSL证书验证
    )
    return response.json()

# 2. 执行HTTP请求
def execute_http(url, method="GET", headers=None, body=None):
    response = requests.post(
        f"{BASE_URL}/api/http/execute",
        headers=get_auth_headers(),
        json={
            "client_id": CLIENT_ID,
            "url": url,
            "method": method,
            "headers": headers or {},
            "body": body
        },
        verify=False
    )
    return response.json()

# 2.5. 执行Telnet命令
def execute_telnet(host, username, password, command, port=23):
    response = requests.post(
        f"{BASE_URL}/api/telnet/execute",
        headers=get_auth_headers(),
        json={
            "client_id": CLIENT_ID,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "command": command
        },
        verify=False  # 跳过SSL证书验证
    )
    return response.json()

# 3. 查询结果
def get_result(session_id):
    response = requests.get(
        f"{BASE_URL}/api/sessions/{session_id}",
        headers=get_auth_headers(),
        verify=False
    )
    return response.json()

# 4. 执行本地命令
def execute_local(command, encoding="gbk"):
    response = requests.post(
        f"{BASE_URL}/api/local/execute",
        headers=get_auth_headers(),
        json={
            "client_id": CLIENT_ID,
            "command": command,
            "timeout": 30,
            "encoding": encoding
        },
        verify=False
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 首先登录
    if not login("your_username", "your_password"):
        exit(1)

    # 执行SSH命令
    result = execute_ssh("192.168.1.1", "admin", "password", "show version")
    print(f"会话ID: {result['session_id']}")

    # 等待并获取结果
    time.sleep(2)
    session = get_result(result['session_id'])
    print(f"执行结果: {session}")

    # 执行Telnet命令（旧设备支持）
    result = execute_telnet("192.168.1.1", "admin", "password", "show version")
    print(f"会话ID: {result['session_id']}")

    time.sleep(3)
    session = get_result(result['session_id'])
    print(f"执行结果: {session}")

    # 执行本地命令
    result = execute_local("systeminfo", "gbk")
    print(f"会话ID: {result['session_id']}")

    time.sleep(3)
    session = get_result(result['session_id'])
    print(f"执行结果: {session['response_data']['stdout'][:200]}...")
```

> 💡 **提示**：生产环境中应使用正式CA签发的证书，并移除 `verify=False` 参数以确保安全性。

### Bash 脚本示例

```bash
#!/bin/bash

BASE_URL="https://localhost:8080"
CLIENT_ID="A1B2C3D4"

# 0. 用户登录获取访问令牌
login() {
    local username=$1
    local password=$2

    RESPONSE=$(curl -s -k -X POST "$BASE_URL/api/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$username\", \"password\": \"$password\"}")

    ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')

    if [ "$ACCESS_TOKEN" != "null" ]; then
        echo "✅ 登录成功！"
        return 0
    else
        echo "❌ 登录失败"
        return 1
    fi
}

# 执行SSH命令
execute_ssh() {
    local host=$1
    local username=$2
    local password=$3
    local command=$4

    curl -s -k -X POST "$BASE_URL/api/ssh/execute" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"client_id\": \"$CLIENT_ID\",
            \"host\": \"$host\",
            \"port\": 22,
            \"username\": \"$username\",
            \"password\": \"$password\",
            \"command\": \"$command\"
        }" | jq -r '.session_id'
}

# 查询结果
get_result() {
    local session_id=$1
    curl -s -k "$BASE_URL/api/sessions/$session_id" \
        -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
}

# 使用
if login "your_username" "your_password"; then
    SESSION_ID=$(execute_ssh "192.168.1.1" "admin" "password" "show version")
    echo "会话ID: $SESSION_ID"

    sleep 2
    get_result "$SESSION_ID"
fi

# 执行本地命令
execute_local() {
    local command=$1
    local encoding=${2:-"gbk"}

    curl -s -k -X POST "$BASE_URL/api/local/execute" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -d "{
            \"client_id\": \"$CLIENT_ID\",
            \"command\": \"$command\",
            \"encoding\": \"$encoding\"
        }" | jq -r '.session_id'
}

# 使用
LOCAL_SESSION_ID=$(execute_local "hostname")
echo "本地命令会话ID: $LOCAL_SESSION_ID"
```

> 💡 **提示**：`-k` 参数用于跳过自签名证书验证。

### PowerShell 示例

```powershell
# 跳过SSL证书验证（仅用于自签名证书）
add-type -TypeDefinition @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

$BASE_URL = "https://localhost:8080"
$CLIENT_ID = "A1B2C3D4"
$ACCESS_TOKEN = $null

# 0. 用户登录获取访问令牌
function Login {
    param($Username, $Password)

    $body = @{
        username = $Username
        password = $Password
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE_URL/api/login" `
        -Method POST -Body $body -ContentType "application/json"

    $script:ACCESS_TOKEN = $response.access_token
    Write-Host "✅ 登录成功！"
    return $response.access_token
}

# 获取认证 Headers
function Get-AuthHeaders {
    return @{
        "Authorization" = "Bearer $script:ACCESS_TOKEN"
        "Content-Type" = "application/json"
    }
}

# 执行SSH命令
function Execute-SSH {
    param($Host, $Username, $Password, $Command)

    $body = @{
        client_id = $CLIENT_ID
        host = $Host
        port = 22
        username = $Username
        password = $Password
        command = $Command
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE_URL/api/ssh/execute" `
        -Method POST -Body $body -Headers (Get-AuthHeaders)

    return $response.session_id
}

# 查询结果
function Get-Result {
    param($SessionId)

    $response = Invoke-RestMethod -Uri "$BASE_URL/api/sessions/$SessionId" `
        -Headers (Get-AuthHeaders)
    return $response
}

# 使用
Login -Username "your_username" -Password "your_password"

$sessionId = Execute-SSH -Host "192.168.1.1" -Username "admin" -Password "password" -Command "show version"
Write-Host "会话ID: $sessionId"

Start-Sleep -Seconds 2
$result = Get-Result -SessionId $sessionId
Write-Host "执行结果: $($result.response_data.stdout)"

# 执行本地命令
function Execute-Local {
    param($Command, $Encoding = "gbk")

    $body = @{
        client_id = $CLIENT_ID
        command = $Command
        encoding = $Encoding
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$BASE_URL/api/local/execute" `
        -Method POST -Body $body -Headers (Get-AuthHeaders)

    return $response.session_id
}

# 使用
$localSessionId = Execute-Local -Command "hostname"
Write-Host "本地命令会话ID: $localSessionId"
```

> 💡 **提示**：证书验证跳过设置仅用于开发环境。生产环境中应使用正式CA签发的证书。

### Go 示例

```go
package main

import (
    "bytes"
    "crypto/tls"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

const (
    BaseURL  = "https://localhost:8080"
    ClientID = "A1B2C3D4"
)

// 跳过SSL证书验证的HTTP客户端（仅用于自签名证书）
var httpClient = &http.Client{
    Transport: &http.Transport{
        TLSClientConfig: &tls.Config{
            InsecureSkipVerify: true,
        },
    },
}

type SSHRequest struct {
    ClientID string `json:"client_id"`
    Host     string `json:"host"`
    Port     int    `json:"port"`
    Username string `json:"username"`
    Password string `json:"password"`
    Command  string `json:"command"`
}

type SessionResponse struct {
    SessionID string `json:"session_id"`
    Message   string `json:"message"`
}

func ExecuteSSH(host, username, password, command string) (string, error) {
    req := SSHRequest{
        ClientID: ClientID,
        Host:     host,
        Port:     22,
        Username: username,
        Password: password,
        Command:  command,
    }

    body, _ := json.Marshal(req)
    resp, err := httpClient.Post(BaseURL+"/api/ssh/execute", "application/json", bytes.NewBuffer(body))
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    var result SessionResponse
    json.NewDecoder(resp.Body).Decode(&result)
    return result.SessionID, nil
}

func main() {
    sessionID, _ := ExecuteSSH("192.168.1.1", "admin", "password", "show version")
    fmt.Printf("会话ID: %s\n", sessionID)

    time.Sleep(2 * time.Second)
    // 查询结果...
}
```

> 💡 **提示**：`InsecureSkipVerify: true` 仅用于开发环境。生产环境中应使用正式CA签发的证书。

---

## 常用 Windows 本地巡检命令

### 系统信息

| 命令 | 说明 |
|------|------|
| `systeminfo` | 完整系统信息 |
| `hostname` | 主机名 |
| `wmic os get Caption,Version,BuildNumber` | 操作系统版本 |
| `wmic computersystem get Model,Manufacturer` | 计算机型号和制造商 |
| `wmic cpu get Name,NumberOfCores,MaxClockSpeed` | CPU 信息 |
| `wmic memorychip get Capacity,Speed` | 内存信息 |
| `wmic bios get SerialNumber` | 主机序列号 |

### 网络相关

| 命令 | 说明 |
|------|------|
| `ipconfig` | IP 配置 |
| `ipconfig /all` | 详细 IP 配置 |
| `ipconfig /displaydns` | DNS 缓存 |
| `netstat -ano` | 所有网络连接 |
| `netstat -ano | findstr ESTABLISHED` | 活动连接 |
| `route print` | 路由表 |
| `arp -a` | ARP 缓存 |
| `ping 8.8.8.8` | 网络连通性测试 |
| `tracert www.baidu.com` | 路由追踪 |
| `nslookup www.baidu.com` | DNS 查询 |

### 进程和服务

| 命令 | 说明 |
|------|------|
| `tasklist` | 运行进程列表 |
| `tasklist /v` | 详细进程信息 |
| `tasklist /fo csv` | CSV 格式输出 |
| `tasklist | findstr chrome.exe` | 查找特定进程 |
| `wmic process where "name='chrome.exe'" get ProcessId,CommandLine` | 进程详细信息 |
| `sc query type= service state= all` | 所有服务状态 |
| `sc query Spooler` | 特定服务状态 |
| `powershell "Get-Process | Select-Object Name,CPU,WorkingSet -First 10"` | PowerShell 获取进程 |

### 文件和磁盘

| 命令 | 说明 |
|------|------|
| `dir C:\` | 列出目录内容 |
| `dir C:\ /s` | 递归列出所有文件 |
| `wmic logicaldisk get DeviceID,Size,FreeSpace` | 磁盘空间 |
| `fsutil volume diskfree C:` | 磁盘可用空间 |
| `type C:\file.txt` | 查看文件内容 |
| `findstr "keyword" C:\file.txt` | 搜索文件内容 |

### 软件和配置

| 命令 | 说明 |
|------|------|
| `wmic product get Name,Version,Vendor` | 已安装软件列表 |
| `wmic qfe get HotFixID,InstalledOn` | 已安装补丁 |
| `reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"` | 启动项 |
| `type C:\Windows\System32\drivers\etc\hosts` | hosts 文件 |
| `net user` | 用户列表 |
| `net localgroup administrators` | 管理员组成员 |

### 性能监控

| 命令 | 说明 |
|------|------|
| `powershell "Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 3"` | CPU 使用率 |
| `powershell "Get-Counter '\\Memory\\Available MBytes'"` | 可用内存 |
| `powershell "Get-Counter '\\Network Interface(*)\\Bytes Total/sec'"` | 网络流量 |
| `wevtutil qe System /c:10 /rd:true /f:text` | 最近 10 条系统日志 |

### 其他实用命令

| 命令 | 说明 |
|------|------|
| `whoami` | 当前用户 |
| `echo %DATE% %TIME%` | 日期和时间 |
| `schtasks /query /fo LIST` | 任务计划 |
| `driverquery` | 已安装驱动 |
| `powershell "Get-WmiObject Win32_PnPSignedDriver | Select-Object DeviceName,DriverVersion"` | 驱动版本 |

---

## 常用 Linux 本地巡检命令

### 系统信息

| 命令 | 说明 |
|------|------|
| `uname -a` | 系统信息 |
| `hostname` | 主机名 |
| `cat /etc/os-release` | 操作系统版本 |
| `uptime` | 系统运行时间 |
| `cat /proc/cpuinfo` | CPU 信息 |
| `free -h` | 内存使用 |
| `df -h` | 磁盘使用 |

### 网络相关

| 命令 | 说明 |
|------|------|
| `ip addr` | IP 地址 |
| `ip route` | 路由表 |
| `netstat -tuln` | 监听端口 |
| `ss -tuln` | 套接字统计 |
| `ping -c 4 8.8.8.8` | 网络测试 |
| `traceroute www.baidu.com` | 路由追踪 |

### 进程和服务

| 命令 | 说明 |
|------|------|
| `ps aux` | 进程列表 |
| `ps aux | grep nginx` | 查找进程 |
| `top -b -n 1` | 系统资源快照 |
| `systemctl status nginx` | 服务状态 |
| `systemctl list-units --type=service` | 所有服务 |

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 401 | 未授权（未提供令牌或令牌无效） |
| 403 | 禁止访问（无权使用该客户端） |
| 404 | 资源不存在 |
| 422 | 请求参数错误（如用户名密码错误） |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "客户端不在线: A1B2C3D4"
}
```

### 常见错误

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| 401 Unauthorized | 未提供认证凭据或令牌无效 | 检查 Authorization Header 或重新登录获取新令牌 |
| 403 Forbidden | 无权使用指定客户端 | 联系管理员分配客户端权限 |
| 422 Unprocessable Entity | 用户名或密码错误 | 检查登录凭据是否正确 |
| 客户端不存在 | 识别码错误 | 检查 client_id 是否正确 |
| 客户端不在线 | 客户端未连接 | 启动客户端 |
| 发送任务失败 | 网络问题 | 检查服务端日志 |
| 请求参数错误 | 参数格式错误 | 检查请求格式 |

---

## 最佳实践

### 1. 安全管理访问令牌

```python
# 令牌即将过期时自动续期
import time

TOKEN_EXPIRY = 24 * 60 * 60  # 24小时
login_time = time.time()

def is_token_expired():
    return time.time() - login_time > TOKEN_EXPIRY

def ensure_token_valid():
    if is_token_expired() or not ACCESS_TOKEN:
        login("username", "password")
```

### 2. 轮询查询结果

由于任务执行是异步的，需要轮询查询结果：

```python
def wait_for_result(session_id, timeout=60, interval=2):
    start = time.time()
    while time.time() - start < timeout:
        session = get_result(session_id)
        if session.get('response_data') is not None:
            return session
        time.sleep(interval)
    raise TimeoutError("任务执行超时")
```

### 2. 错误处理

```python
def execute_ssh_safe(host, username, password, command):
    try:
        result = execute_ssh(host, username, password, command)
        session = wait_for_result(result['session_id'])

        if not session['success']:
            print(f"执行失败: {session['error_message']}")
            return None

        return session['response_data']['stdout']

    except Exception as e:
        print(f"发生错误: {e}")
        return None
```

### 3. 批量执行

```python
def execute_batch(commands):
    results = []
    for cmd in commands:
        result = execute_ssh_safe(cmd['host'], cmd['username'], cmd['password'], cmd['command'])
        results.append({
            'command': cmd['command'],
            'result': result
        })
    return results
```

### 4. 日志记录

```python
import logging

logging.basicConfig(filename='api_calls.log', level=logging.INFO)

def log_api_call(endpoint, data):
    logging.info(f"API调用: {endpoint}, 数据: {json.dumps(data)}")
```

### 5. 连接池

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
```

---

## 附录

### 状态码说明

#### SSH 退出码

| 退出码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 误用shell命令 |
| 126 | 命令不可执行 |
| 127 | 命令未找到 |
| -1 | 连接或执行异常 |

#### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 2xx | 成功 |
| 4xx | 客户端错误 |
| 5xx | 服务端错误 |
| 0 | 请求失败 |

### API 文档

启动服务端后，访问 `https://your-server:8080/docs` 查看 Swagger UI 文档。

> ⚠️ **注意**：由于使用自签名证书，浏览器可能会显示安全警告。这是正常的，点击"继续访问"即可。

### 性能参考

| 操作 | 预期耗时 |
|------|----------|
| API调用 | <100ms |
| SSH命令执行 | 取决于命令 |
| HTTP请求 | 取决于网络 |
| 结果查询 | <50ms |

---

## 常见问题 FAQ

**Q: 如何获取访问令牌？**
A: 调用 `POST /api/login` 接口，使用用户名和密码登录获取。令牌有效期为 24 小时。

**Q: 令牌过期了怎么办？**
A: 重新调用 `/api/login` 接口获取新的访问令牌。

**Q: 为什么返回 403 Forbidden 错误？**
A: 这表示您当前登录的用户无权使用指定的客户端。请联系管理员将此客户端分配给您的账户。

**Q: 一个用户可以使用多个客户端吗？**
A: 可以。管理员可以为用户分配多个客户端权限。

**Q: 如何知道任务是否完成？**
A: 轮询 `/api/sessions/{id}` 接口，当 `response_data` 不为空时表示完成。

**Q: 任务会丢失吗？**
A: 客户端断线时，正在执行的任务会继续完成，但结果无法返回。建议执行前确认客户端在线。

**Q: 可以取消正在执行的任务吗？**
A: 当前版本不支持，任务会执行直到完成或超时。

**Q: 支持文件传输吗？**
A: 不支持，只能执行命令和HTTP请求。

**Q: 如何提高并发能力？**
A: 部署多个客户端，使用不同的 `client_id`。

**Q: 如何执行客户端本地命令？**
A: 使用 `/api/local/execute` 接口，客户端是纯粹执行器，可以执行任何系统命令。调用方应自行控制命令的安全性和合法性。

**Q: Windows 命令输出乱码怎么办？**
A: 设置 `encoding: "gbk"` 参数，Windows CMD 默认使用 GBK 编码。

**Q: 如何批量执行巡检？**
A: 可以并发执行多个巡检命令，然后轮询查询所有结果。参考上方常用巡检命令列表。

**Q: API 支持哪些编程语言？**
A: 支持任何可以进行 HTTP 调用的编程语言。文档中提供了 Python、Bash、PowerShell、Go 的示例代码。

**Q: 如何使用 Telnet 执行命令？**
A: 使用 `/api/telnet/execute` 接口，适用于不支持 SSH 的旧设备。需要提供主机地址、端口、用户名、密码和要执行的命令。

**Q: Telnet 和 SSH 有什么区别？**
A: SSH 是加密协议，更安全；Telnet 是明文传输，不安全。但某些旧设备只支持 Telnet，因此系统保留了 Telnet 支持以兼容这些设备。
