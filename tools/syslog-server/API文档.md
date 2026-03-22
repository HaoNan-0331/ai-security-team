# Syslog Server API 文档

## 基础信息

| 项目 | 值 |
|------|-----|
| 服务地址 | `http://192.168.10.248:8000` |
| 协议 | HTTP |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| API前缀 | `/api/v1` |

## API 端点

### 1. 健康检查

检查服务运行状态。

**请求**
```
GET /api/v1/health
```

**响应示例**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 0.0,
  "storage": {
    "status": "connected"
  },
  "receivers": [
    {
      "name": "514/udp",
      "status": "listening",
      "rate": 0
    },
    {
      "name": "514/tcp",
      "status": "listening",
      "rate": 0
    },
    {
      "name": "515/tcp",
      "status": "listening",
      "rate": 0
    },
    {
      "name": "516/tcp",
      "status": "listening",
      "rate": 0
    }
  ]
}
```

**字段说明**
| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态 (healthy/degraded) |
| version | string | 服务版本 |
| uptime | float | 运行时间(秒) |
| storage.status | string | 存储状态 (connected/disconnected) |
| receivers | array | 接收器列表 |

---

### 2. Prometheus 指标

获取服务 Prometheus 监控指标。

**请求**
```
GET /api/v1/metrics
```

**响应示例**
```
# HELP syslog_messages_received_total Total syslog messages received
# TYPE syslog_messages_received_total counter
syslog_messages_received_total{receiver="514/udp"} 1523
...
```

**说明**: 返回 Prometheus 格式的文本指标数据。

---

### 2. 查询日志

查询存储的日志条目，支持多种过滤条件。

**请求**
```
GET /api/v1/logs
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| start_time | datetime | **是** | - | 开始时间 (ISO8601) |
| end_time | datetime | **是** | - | 结束时间 (ISO8601) |
| device_ip | string | 否 | - | 设备IP |
| device_type | string | 否 | - | 设备类型 |
| vendor | string | 否 | - | 设备厂商 |
| event_type | string | 否 | - | 事件类型 |
| severity | string | 否 | - | 严重程度 (逗号分隔，如: err,warning,crit) |
| src_ip | string | 否 | - | 源IP |
| dst_ip | string | 否 | - | 目的IP |
| port | int | 否 | - | 端口号 |
| protocol | string | 否 | - | 协议 |
| keyword | string | 否 | - | 关键词搜索 |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 100 | 每页条数 (最大1000) |
| sort_by | string | 否 | timestamp | 排序字段 |
| sort_order | string | 否 | desc | 排序方向 (asc/desc) |

**响应格式说明**

API使用统一的响应包装格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ...实际数据... },
  "timestamp": "2026-02-25T15:30:00.123456"
}
```

其中 `data` 字段包含实际的查询结果：

```json
{
  "total": 150,
  "page": 1,
  "page_size": 100,
  "total_pages": 2,
  "logs": [
    {
      "id": 1,
      "received_at": "2026-02-25T00:00:00.000Z",
      "timestamp": "2026-02-25T00:00:00.000Z",
      "device_ip": "192.168.1.100",
      "device_type": "firewall",
      "severity": 3,
      "severity_label": "err",
      "message": "DENY TCP 192.168.1.50:5353 -> 10.0.0.1:53",
      "src_ip": "192.168.1.50",
      "dst_ip": "10.0.0.1",
      "protocol": "TCP",
      "raw_message": "<34>1 2026-02-25T00:00:00.000Z firewall 1 - - DENY TCP 192.168.1.50:5353 -> 10.0.0.1:53"
    }
  ]
}
```

**请求示例**
```bash
# 基本查询（必须提供时间范围）
curl "http://192.168.10.248:8000/api/v1/logs?start_time=2026-02-25T00:00:00&end_time=2026-02-25T23:59:59"

# 分页查询
curl "http://192.168.10.248:8000/api/v1/logs?start_time=2026-02-25T00:00:00&end_time=2026-02-25T23:59:59&page=2&page_size=50"

# 按设备IP过滤
curl "http://192.168.10.248:8000/api/v1/logs?start_time=2026-02-25T00:00:00&end_time=2026-02-25T23:59:59&device_ip=192.168.1.100"

# 按严重程度过滤 (逗号分隔的严重程度字符串)
curl "http://192.168.10.248:8000/api/v1/logs?start_time=2026-02-25T00:00:00&end_time=2026-02-25T23:59:59&severity=err,warning,crit"
```

---

### 3. 获取单条日志 (未实现)

> **⚠️ 警告**: 此端点当前未实现，调用将返回 HTTP 501 错误。

**请求**
```
GET /api/v1/logs/{log_id}
```

**状态**: 🚧 计划功能，尚未实现

---

### 4. 高级搜索 (未实现)

> **⚠️ 警告**: 此端点当前未实现，调用将返回 HTTP 501 错误。

支持复杂查询条件的高级搜索功能。

**请求**
```
POST /api/v1/logs/search
Content-Type: application/json
```

**请求体示例**
```json
{
  "query": {
    "device_ip": "192.168.1.100",
    "severity": [3, 4, 5],
    "time_range": {
      "start": "2026-02-24T00:00:00Z",
      "end": "2026-02-25T00:00:00Z"
    }
  },
  "aggregation": {
    "group_by": "device_ip",
    "metrics": ["count"]
  },
  "page": 1,
  "page_size": 100
}
```

**状态**: 🚧 计划功能，尚未实现

---

## 发送 Syslog 消息

### UDP 端口

**端口**: 514 (UDP)

### 消息格式

支持标准 Syslog 格式 (RFC5424):

```
<PRIVAL>VERSION ISOTIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
```

**示例**
```
<134>1 2026-02-25T10:00:00.000Z firewall 1 - - DENY TCP 192.168.1.50:5353 -> 10.0.0.1:53
```

### 发送方式

**使用 netcat**
```bash
echo "<134>1 2026-02-25T10:00:00.000Z myhost 1 - - My log message" | nc -u 192.168.10.248 514
```

**使用 logger**
```bash
logger -n 192.168.10.248 -P 514 "My log message"
```

**Python 示例**
```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
message = b"<134>1 2026-02-25T10:00:00.000Z myhost 1 - - My log message"
sock.sendto(message, ("192.168.10.248", 514))
sock.close()
```

---

## Python 客户端示例

```python
import requests
import socket
from datetime import datetime

class SyslogClient:
    """Syslog Server 客户端"""

    def __init__(self, api_url="http://192.168.10.248:8000"):
        self.api_url = api_url
        self.syslog_host = "192.168.10.248"
        self.syslog_port = 514

    def health(self):
        """健康检查"""
        return requests.get(f"{self.api_url}/api/v1/health").json()

    def query_logs(self, **filters):
        """查询日志"""
        return requests.get(f"{self.api_url}/api/v1/logs", params=filters).json()

    def search_logs(self, query):
        """高级搜索"""
        return requests.post(f"{self.api_url}/api/v1/logs/search", json=query).json()

    def send(self, message, severity=6):
        """发送日志消息 (severity: 0=emerg, 6=info, 7=debug)"""
        facility = 16  # local use
        priority = facility * 8 + severity

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        syslog_msg = f"<{priority}>1 {timestamp} client 1 - - {message}"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(syslog_msg.encode(), (self.syslog_host, self.syslog_port))
        sock.close()

# 使用示例
client = SyslogClient()

# 发送日志
client.send("Service started", severity=6)
client.send("Connection failed", severity=3)

# 健康检查
health = client.health()
print(f"服务状态: {health['status']}")

# 查询日志
logs = client.query_logs(page=1, page_size=10)
print(f"共 {logs['total']} 条日志")
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 端点不存在 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

---

## OpenAPI 文档

服务启动后访问交互式API文档:
- Swagger UI: http://192.168.10.248:8000/docs
- ReDoc: http://192.168.10.248:8000/redoc
- OpenAPI JSON: http://192.168.10.248:8000/openapi.json

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-02-25 | 初始版本，支持PostgreSQL+Redis存储 |

---

## 联系方式

- 服务器: 192.168.10.248
- API 文档: http://192.168.10.248:8000/docs
- UDP 端口: 514
- TCP 端口: 514, 515, 516
