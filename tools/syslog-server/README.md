# Syslog Server

企业级 Syslog 服务器，用于接收、存储和查询各类网络设备日志。

## 功能特性

- ✅ 多端口接收 (UDP/TCP)
- ✅ 支持多种日志格式 (RFC3164/RFC5424/CEF/JSON)
- ✅ 智能解析和标准化
- ✅ REST API 查询接口
- ✅ 资产关联增强
- ✅ 威胁标签和 ATT&CK 映射
- ✅ Linux systemd 服务

## 支持的设备

| 设备类型 | 端口 | 格式 |
|---------|------|------|
| 交换机/路由器 | 514/UDP | RFC5424 |
| 防火墙 | 514/TCP | CEF |
| 威胁探针 | 515/TCP | JSON |
| IDS/IPS | 516/TCP | CEF |
| 服务器 | 514/UDP | RFC3164/RFC5424 |

## 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | 3.11+ |
| PostgreSQL | 9.2+ |
| Redis | 3.0+ |
| OpenSSL | 1.1.1+ (Python SSL模块) |

## 快速开始

### 本地开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m syslog_server.main
```

### Linux 服务器部署

详细部署步骤请参考 [DEPLOYMENT.md](./DEPLOYMENT.md)

```bash
# 快速部署（已配置systemd服务）
systemctl start syslog-server
systemctl status syslog-server
```

## 配置

### 环境变量 (.env)

```bash
# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=syslog
DB_USER=syslog_user
DB_PASSWORD=your_password

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# 服务配置
HOST=0.0.0.0
PORT=8000
WORKERS=1
LOG_LEVEL=INFO
```

### 接收器配置 (config/receivers.yaml)

```yaml
receivers:
  - name: standard_udp
    protocol: udp
    port: 514
    format: rfc5424
    enabled: true
```

#### 添加新端口

要添加新的接收端口，在 `config/receivers.yaml` 中添加新的接收器配置：

```yaml
# 示例：添加 515 UDP 端口用于防火墙
- name: firewall_udp
  protocol: udp
  host: 0.0.0.0
  port: 515
  format: cef          # 日志格式: rfc5424 / rfc3164 / cef / json
  enabled: true
  workers: 4           # 工作线程数
  buffer_size: 1048576 # UDP缓冲区大小(字节)
  parser_options:
    device_type: firewall
    vendor: generic
  description: "防火墙UDP接收器"
```

**配置字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 接收器名称，唯一标识 |
| `protocol` | 是 | 协议类型：`udp` 或 `tcp` |
| `host` | 否 | 监听地址，默认 `0.0.0.0` |
| `port` | 是 | 监听端口号 |
| `format` | 是 | 日志格式：`rfc5424`/`rfc3164`/`cef`/`json` |
| `enabled` | 否 | 是否启用，默认 `true` |
| `workers` | 否 | 工作线程数，默认 4 |
| `buffer_size` | 否 | UDP缓冲区大小，默认 1MB |

**常用日志格式：**

| 格式 | 适用设备 |
|------|----------|
| `rfc5424` | 标准Syslog，交换机、路由器、服务器 |
| `rfc3164` | 旧版BSD Syslog |
| `cef` | 防火墙、IDS/IPS（深信服、天融信等） |
| `json` | 威胁探针、现代安全设备 |

**修改后重启服务：**
```bash
systemctl restart syslog-server
```

### 解析器配置 (config/parsers.yaml)

```yaml
parsers:
  - name: rfc5424
    type: syslog
    version: rfc5424
```

## API 文档

服务启动后访问: http://localhost:8000/docs

### 主要接口

| 接口 | 方法 | 状态 | 说明 |
|------|------|:----:|------|
| `/api/v1/health` | GET | ✅ | 健康检查 |
| `/api/v1/metrics` | GET | ✅ | Prometheus监控指标 |
| `/api/v1/logs` | GET | ✅ | 查询日志 |
| `/api/v1/logs/{log_id}` | GET | 🚧 | 获取单条日志 (未实现) |
| `/api/v1/logs/search` | POST | 🚧 | 高级搜索 (未实现) |
| `/openapi.json` | GET | ✅ | OpenAPI规范 |

## 项目结构

```
syslog-server/
├── config/              # 配置文件
│   ├── receivers.yaml   # 接收器配置
│   ├── parsers.yaml     # 解析器配置
│   └── *.yaml           # 其他配置
├── syslog_server/       # 主程序
│   ├── config/          # 配置管理
│   ├── receivers/       # 日志接收器
│   ├── parsers/         # 日志解析器
│   ├── storage/         # 存储层
│   ├── enrichment/      # 数据增强
│   ├── api/             # API 接口
│   └── utils/           # 工具函数
├── scripts/             # 脚本工具
├── sql/                 # 数据库脚本
├── requirements.txt     # Python依赖
├── README.md            # 项目说明
├── API文档.md           # API文档
├── DEPLOYMENT.md        # 部署文档
└── Syslog服务端设计方案.md # 设计文档
```

## 性能指标

| 指标 | 目标值 |
|------|--------|
| UDP 接收速率 | >10,000 条/秒 |
| TCP 接收速率 | >5,000 条/秒 |
| 解析延迟 | <10ms |
| 查询响应 | <1秒 |

## 相关文档

- [API文档.md](./API文档.md) - 详细的API接口文档
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Linux服务器部署指南
- [Syslog服务端设计方案.md](./Syslog服务端设计方案.md) - 系统设计文档

## 许可证

MIT License
