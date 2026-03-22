# 资产库 (Asset Database)

> AI Security Team的核心资产管理系统，纯SDK访问方式

---

## v4.0 更新说明 (2026-02-17)

- ✅ 新增P0高优先级字段（SSH连接、服务端口、风险评分、隔离状态、网络分类）
- ✅ 新增P1中优先级字段（硬件配置、合规扫描）
- ✅ 新增健康检查功能（health_check）
- ✅ 新增审计日志查询（get_audit_logs）
- ✅ 新增风险报告生成（get_risk_report）
- ✅ 新增按风险/隔离状态/网段查询
- ✅ 新增资产状态：investigating、isolated、remediated

---

## 快速开始

### 安装依赖

```bash
cd asset-database
pip install -r requirements.txt
```

### SDK使用

```python
import sys
sys.path.insert(0, 'teams/ai-security-team/asset-database')
from asset_sdk import AssetClient

client = AssetClient()

# 创建资产
asset = client.create_asset(
    name="Web服务器-01",
    asset_type="Server",
    ip_address="192.168.1.100",
    username="admin",
    password="secret",
    ssh_port=22,
    services=["nginx", "mysql"],
    risk_score=30
)

# 查询资产
servers = client.list_assets(
    asset_type="Server",
    environment="production"
)

# 获取密码
password = client.get_password(asset['asset_id'])

# 风险报告
report = client.get_risk_report(min_score=50)

# 健康检查
result = client.health_check(asset_id=asset['asset_id'])
```

---

## 目录结构

```
asset-database/
├── asset_sdk.py           # Python SDK
├── database.py            # 数据库配置（WAL模式）
├── models/                # 数据模型
│   ├── __init__.py
│   └── asset.py           # Asset, AssetChangeLog, 枚举
├── utils/                 # 工具函数
│   ├── __init__.py
│   ├── crypto.py          # 密码加密解密
│   └── file_lock.py       # 文件锁
├── scripts/               # 工具脚本
│   ├── migrate.py         # 数据库迁移
│   ├── discover.py        # 网络发现
│   ├── init_db.py         # 数据库初始化
│   └── export_inventory.py # 资产导出
├── migrations/            # 数据库迁移
│   └── 001_initial_schema.sql
├── schema/                # 数据库模式
│   ├── postgresql/
│   ├── elasticsearch/
│   └── neo4j/
├── data/                  # 数据目录
│   ├── assets.db          # SQLite数据库
│   ├── asset.db           # 备份数据库
│   └── .secret_key        # 加密密钥
├── DATA_MODEL.md          # 数据模型文档
├── ASSET_DATABASE_FIELDS.md  # 字段文档
└── README.md
```

---

## SDK API速查

### 基础CRUD

| 方法 | 用途 |
|------|------|
| `create_asset()` | 创建资产 |
| `get_asset()` | 获取资产详情 |
| `update_asset()` | 更新资产 |
| `delete_asset()` | 删除资产 |

### 查询

| 方法 | 用途 |
|------|------|
| `list_assets()` | 列出资产（支持多维度过滤） |
| `find_assets()` | 关键字搜索 |
| `get_asset_by_ip()` | 按IP查询 |
| `get_asset_by_name()` | 按名称查询 |
| `list_assets_by_risk()` | 按风险分数查询 |
| `list_assets_by_isolation_status()` | 按隔离状态查询 |
| `list_assets_by_network_segment()` | 按网段查询 |

### 批量操作

| 方法 | 用途 |
|------|------|
| `batch_create()` | 批量创建 |
| `batch_update()` | 批量更新 |
| `batch_delete()` | 批量删除 |
| `batch_get()` | 批量获取 |

### 新增功能

| 方法 | 用途 |
|------|------|
| `health_check()` | 健康检查（连通性/端口） |
| `get_audit_logs()` | 审计日志查询 |
| `get_risk_report()` | 风险报告生成 |
| `get_statistics()` | 多维度统计 |
| `get_change_history()` | 变更历史 |

### 其他

| 方法 | 用途 |
|------|------|
| `get_password()` | 获取密码（解密） |
| `update_password()` | 更新密码 |
| `add_relationship()` | 添加资产关系 |
| `get_relationships()` | 获取资产关系 |
| `remove_relationship()` | 删除资产关系 |
| `export_assets()` | 导出资产数据 |

---

## 资产类型

| 类型 | 说明 |
|------|------|
| `NetworkDevice` | 网络设备（交换机、路由器） |
| `SecurityDevice` | 安全设备（防火墙、IDS/IPS） |
| `Server` | 服务器 |
| `Terminal` | 终端（PC、笔记本） |
| `Database` | 数据库 |
| `Application` | 应用系统 |
| `Other` | 其他 |

## 资产状态

| 状态 | 说明 |
|------|------|
| `active` | 在用 |
| `standby` | 备用 |
| `maintenance` | 维护中 |
| `retired` | 已退役 |
| `compromised` | 已失陷 |
| `investigating` | 调查中 |
| `isolated` | 已隔离 |
| `remediated` | 已修复 |
| `unknown` | 状态未知 |

## 隔离状态

| 状态 | 说明 |
|------|------|
| `normal` | 正常运行 |
| `network` | 网络隔离（阻断外部访问） |
| `host` | 主机隔离（完全禁止访问） |

---

## Agent使用指南

### server-ops（服务器运维）

```python
# 获取服务器列表
servers = client.list_assets(asset_type="Server", environment="production")

# 获取登录凭据
asset = client.get_asset(asset_id)
password = client.get_password(asset_id)
ssh_port = asset.get('ssh_port', 22)

# 更新硬件信息
client.update_asset(asset_id, cpu_cores=16, memory_gb=64, changed_by='server-ops')
```

### network-ops（网络运维）

```python
# 获取网络设备
devices = client.list_assets(asset_type="NetworkDevice")

# 获取VLAN信息
device = client.get_asset(asset_id)
vlan_ids = device.get('vlan_ids', [])
network_segment = device.get('network_segment')

# 按设备角色查询
core_devices = client.find_assets("core", fields=['name', 'device_role'])
```

### threat-response（威胁处置）

```python
# 隔离资产
client.update_asset(
    asset_id,
    status='isolated',
    isolation_status='network',
    risk_score=85,
    changed_by='threat-response',
    change_reason='检测到恶意软件'
)

# 查看审计日志
logs = client.get_audit_logs(asset_id=asset_id)

# 生成风险报告
report = client.get_risk_report(min_score=50)

# 查询高风险资产
high_risk = client.list_assets_by_risk(min_score=60)
```

### asset-mgmt（资产管理）

```python
# 完整API文档见 agents/monitoring/asset-mgmt/prompt.md

# 批量创建
result = client.batch_create([
    {"name": "Server-01", "asset_type": "Server", "ip_address": "192.168.1.10"},
    {"name": "Server-02", "asset_type": "Server", "ip_address": "192.168.1.11"},
], changed_by="asset-mgmt")

# 统计分析
stats = client.get_statistics(by_type=True, by_status=True, by_importance=True)

# 健康检查
result = client.health_check(asset_ids=[id1, id2, id3], check_type="connectivity")
```

---

## 并发安全

- SQLite WAL模式：支持并发读
- 忙等待超时：30秒
- 自动重试机制：最多5次

---

## 详细文档

- [数据模型文档](./DATA_MODEL.md) - 完整的字段说明和API文档
- [资产管理Agent](../agents/monitoring/asset-mgmt/prompt.md) - 完整SDK使用示例

---

*负责人: asset-mgmt*
*版本: v4.0*
*更新日期: 2026-02-17*
