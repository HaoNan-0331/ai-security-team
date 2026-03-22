# Syslog Server 部署文档

## 服务器信息

| 项目 | 值 |
|------|-----|
| IP地址 | 192.168.10.248 |
| 操作系统 | CentOS Linux 7.6.1810 |
| Python版本 | 3.11 (编译安装) |
| 数据库 | PostgreSQL 9.2 |
| 缓存 | Redis 3.2 |
| API端口 | 8000 |

---

## 快速部署

### 方法一：Docker 部署（推荐）

使用内置的部署脚本：

```bash
cd E:\knowlegdge_base\python_project\syslog-server
python scripts/deploy.py
```

此脚本会自动：
1. 检查服务器环境和Docker安装
2. 创建必要的目录结构
3. 生成安全密码和配置文件
4. 构建Docker镜像
5. 启动所有服务（PostgreSQL + Redis + Syslog Server）

### 方法二：手动部署

#### 1. 系统要求

| 组件 | 版本要求 |
|------|---------|
| Python | 3.11+ |
| PostgreSQL | 9.2+ |
| Redis | 3.0+ |
| OpenSSL | 1.1.1+ (Python SSL模块) |

#### 2. 安装依赖

```bash
# 安装系统依赖
yum install -y gcc postgresql-devel redis

# 创建虚拟环境
python3.11 -m venv /opt/syslog-server/venv
source /opt/syslog-server/venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=syslog
DB_USER=syslog_user
DB_PASSWORD=your_password
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50

# 服务配置
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=INFO

# API配置
API_SECRET_KEY=change-me-in-production
API_MAX_PAGE_SIZE=1000

# 数据保留策略
HOT_DATA_DAYS=30
WARM_DATA_DAYS=60
COLD_DATA_DAYS=275
```

#### 4. 配置接收器

编辑 `config/receivers.yaml` 配置日志接收端口：

```yaml
receivers:
  - name: standard_udp
    protocol: udp
    host: 0.0.0.0
    port: 514
    format: rfc5424
    enabled: true
    workers: 4
    buffer_size: 1048576
    description: "标准 UDP Syslog 接收器"

  - name: firewall
    protocol: tcp
    host: 0.0.0.0
    port: 514
    format: cef
    enabled: true
    workers: 4
    max_connections: 500
    description: "防火墙 CEF 接收器"

  - name: threat_probe
    protocol: tcp
    host: 0.0.0.0
    port: 515
    format: json
    enabled: true
    workers: 4
    max_connections: 200
    description: "威胁探针 JSON 接收器"
```

#### 5. 配置增强功能

编辑以下配置文件以启用数据增强功能：

- `config/assets.yaml` - 资产库配置
- `config/threat_signatures.yaml` - 威胁特征库
- `config/mitre_mappings.yaml` - MITRE ATT&CK 映射
- `config/ip_reputation.yaml` - IP 声誉库

#### 6. 配置解析器

编辑 `config/parsers.yaml` 配置日志解析器：

```yaml
parsers:
  - name: rfc5424
    type: syslog
    version: rfc5424
  - name: cef
    type: cef
  - name: json
    type: json
```

#### 7. 启动服务

```bash
# 启动服务
python -m syslog_server.main

# 或使用 uvicorn 直接启动
uvicorn syslog_server.main:create_app --host 0.0.0.0 --port 8000
```

#### 8. 创建 systemd 服务

创建 `/etc/systemd/system/syslog-server.service`：

```ini
[Unit]
Description=Syslog Server Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=root
WorkingDirectory=/opt/syslog-server
Environment="PATH=/opt/syslog-server/venv/bin"
ExecStart=/opt/syslog-server/venv/bin/python -m syslog_server.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
systemctl daemon-reload
systemctl enable syslog-server
systemctl start syslog-server
systemctl status syslog-server
```

---

## 配置说明

### 支持的日志格式

| 格式 | 说明 | 适用设备 |
|------|------|----------|
| `rfc5424` | 标准Syslog RFC5424 | 交换机、路由器、服务器 |
| `rfc3164` | 旧版BSD Syslog | 老旧设备 |
| `cef` | 通用事件格式 | 防火墙、IDS/IPS（深信服、天融信、绿盟等） |
| `json` | JSON格式 | 威胁探针、现代安全设备 |

### 数据增强功能

系统支持以下数据增强模块（通过环境变量控制）：

| 功能 | 环境变量 | 默认值 |
|------|----------|--------|
| 资产关联 | `ENRICHMENT_ENABLE_ASSET` | true |
| 地理位置 | `ENRICHMENT_ENABLE_GEO` | true |
| 威胁检测 | `ENRICHMENT_ENABLE_THREAT` | true |
| MITRE映射 | `ENRICHMENT_ENABLE_MITRE` | true |
| 并行处理 | `ENRICHMENT_PARALLEL_STAGES` | true |

### 数据保留策略

系统采用分层存储策略：

| 层级 | 保留天数 | 说明 |
|------|----------|------|
| 热 | 30天 | 高频查询，主存储 |
| 温 | 60天 | 中频查询，归档存储 |
| 冷 | 275天 | 低频查询，压缩存储 |

---

## 服务管理命令

```bash
# 查看服务状态
systemctl status syslog-server

# 重启服务
systemctl restart syslog-server

# 查看日志
journalctl -u syslog-server -f

# 停止服务
systemctl stop syslog-server

# 重新加载配置
systemctl reload syslog-server
```

---

## 添加新接收端口

### 编辑配置文件

修改 `config/receivers.yaml` 添加新接收器：

```yaml
receivers:
  # 添加华为交换机专用端口
  - name: huawei_switch
    protocol: udp
    host: 0.0.0.0
    port: 5514
    format: rfc5424
    enabled: true
    workers: 2
    parser_options:
      vendor: huawei
      device_type: switch
    description: "华为交换机专用端口"

  # 添加思科交换机专用端口
  - name: cisco_switch
    protocol: udp
    host: 0.0.0.0
    port: 5515
    format: rfc5424
    enabled: true
    workers: 2
    parser_options:
      vendor: cisco
      device_type: switch
    description: "思科交换机专用端口"
```

### 重启服务

```bash
systemctl restart syslog-server
```

### 验证端口监听

```bash
netstat -tlnp | grep syslog
# 或
ss -tlnp | grep python
```

---

## API 接口

### 健康检查

```bash
curl http://192.168.10.248:8000/api/v1/health
```

响应示例：

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600.0,
  "storage": {
    "status": "connected"
  },
  "receivers": [
    {
      "name": "514/udp",
      "status": "listening",
      "rate": 1523
    }
  ]
}
```

### 查询日志

```bash
curl "http://192.168.10.248:8000/api/v1/logs?start_time=2026-02-25T00:00:00&end_time=2026-02-25T23:59:59"
```

### Prometheus 指标

```bash
curl http://192.168.10.248:8000/api/v1/metrics
```

### 交互式文档

- Swagger UI: http://192.168.10.248:8000/docs
- ReDoc: http://192.168.10.248:8000/redoc

详细 API 文档请参考 [API文档.md](./API文档.md)

---

## 系统配置

### 防火墙端口开放

```bash
# 开放Syslog端口
firewall-cmd --permanent --add-port=514/udp
firewall-cmd --permanent --add-port=515/udp
firewall-cmd --permanent --add-port=516/udp
firewall-cmd --permanent --add-port=514/tcp
firewall-cmd --permanent --add-port=515/tcp
firewall-cmd --permanent --add-port=516/tcp
firewall-cmd --permanent --add-port=8000/tcp  # API端口
firewall-cmd --reload

# 验证
firewall-cmd --list-ports
```

### PostgreSQL 配置

允许远程连接：

```bash
# 编辑 /var/lib/pgsql/data/pg_hba.conf
host    all             all               127.0.0.1/32            md5
host    syslog          syslog_user        127.0.0.1/32            md5

# 重启 PostgreSQL
systemctl restart postgresql
```

### Redis 配置

```bash
# 启动 Redis
systemctl start redis

# 设置密码（可选）
redis-cli CONFIG SET requirepass your_password
```

---

## 故障排查

### 常见问题

#### 问题：服务无法启动

```bash
# 查看详细日志
journalctl -u syslog-server -n 100 --no-pager

# 检查端口占用
netstat -tlnp | grep -E '(514|8000)'

# 检查数据库连接
psql -h 127.0.0.1 -U syslog_user -d syslog -c "SELECT 1"
```

#### 问题：接收器无法启动

检查配置文件语法：

```bash
python -c "import yaml; yaml.safe_load(open('config/receivers.yaml'))"
```

检查端口权限（< 1024 需要root）：

```bash
# 使用 setcap 允许非root绑定低端口
setcap cap_net_bind_service=+ep /opt/syslog-server/venv/bin/python
```

#### 问题：日志解析失败

查看解析器日志：

```bash
tail -f /app/logs/server.log | grep -i parse
```

---

## 日志位置

| 日志类型 | 路径 |
|---------|------|
| 应用日志 | `/opt/syslog-server/logs/server.log` |
| 服务日志 | `/opt/syslog-server/logs/service.log` |
| Syslog日志 | PostgreSQL数据库 |
| systemd日志 | `journalctl -u syslog-server` |
| 数据库日志 | `/var/lib/pgsql/data/logfile` |

---

## 性能调优

### 数据库连接池

```bash
# 在 .env 中调整
DB_POOL_SIZE=50        # 连接池大小
DB_MAX_OVERFLOW=100     # 最大溢出连接
```

### 接收器工作线程

```yaml
# 在 config/receivers.yaml 中调整
workers: 8             # 增加工作线程
max_connections: 2000  # TCP最大连接数
```

### 数据增强批次大小

```bash
# 在 .env 中调整
ENRICHMENT_BATCH_SIZE=200
ENRICHMENT_PARALLEL_STAGES=true
```

---

## 项目结构

```
syslog-server/
├── config/                  # 配置文件
│   ├── receivers.yaml       # 接收器配置
│   ├── parsers.yaml         # 解析器配置
│   ├── assets.yaml          # 资产库配置
│   ├── threat_signatures.yaml # 威胁特征库
│   ├── mitre_mappings.yaml  # MITRE映射配置
│   └── ip_reputation.yaml   # IP声誉库
├── syslog_server/           # 主程序
│   ├── config/              # 配置管理
│   ├── receivers/           # 日志接收器
│   ├── parsers/             # 日志解析器
│   ├── storage/             # 存储层
│   ├── enrichment/          # 数据增强
│   ├── api/                 # API接口
│   └── utils/               # 工具函数
├── tests_scripts/           # 测试脚本
│   ├── check_db.py          # 数据库检查
│   ├── send_test_log.sh     # 发送测试日志
│   ├── tcp_test.py          # TCP测试
│   ├── tcp_test2.py         # TCP测试2
│   ├── test_receiver.py     # 接收器测试
│   └── view_logs.py         # 日志查看
├── scripts/                 # 部署脚本
│   └── deploy.py            # 自动部署脚本
├── requirements.txt         # Python依赖
├── README.md               # 项目说明
├── API文档.md              # API文档
├── DEPLOYMENT.md           # 本文档
└── Syslog服务端设计方案.md # 设计文档
```

---

## 测试工具

项目包含以下测试脚本：

```bash
# 发送测试日志
./tests_scripts/send_test_log.sh

# 测试TCP接收
python tests_scripts/tcp_test.py

# 检查数据库
python tests_scripts/check_db.py

# 查看日志
python tests_scripts/view_logs.py
```

---

**文档版本**: v2.0
**更新日期**: 2026-02-25
**状态**: 🟢 生产就绪
