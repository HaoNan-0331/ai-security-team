# 资产数据库 SDK 使用手册

> 版本: v4.0 | 更新日期: 2026-02-26

---

## 目录

1. [快速开始](#快速开始)
2. [安装](#安装)
3. [基础用法](#基础用法)
4. [API参考](#api参考)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

---

## 快速开始

### 5分钟快速上手

```python
import sys
sys.path.insert(0, 'teams/ai-security-team/asset-database')
from asset_sdk import AssetClient

# 创建客户端
client = AssetClient()

# 创建资产
asset = client.create_asset(
    name="Web服务器-01",
    asset_type="Server",
    ip_address="192.168.1.100",
    username="admin",
    password="secret123"
)

# 查询资产
servers = client.list_assets(asset_type="Server")
print(f"找到 {len(servers)} 台服务器")
```

---

## 安装

### 环境要求

- Python 3.8+
- SQLite 3.25+（默认）或 PostgreSQL 12+

### 安装步骤

```bash
# 克隆或进入项目目录
cd teams/ai-security-team/asset-database

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "from asset_sdk import AssetClient; print('SDK安装成功')"
```

### 依赖包

```
sqlalchemy>=2.0.0
cryptography>=40.0.0
python-dotenv>=1.0.0
```

---

## 基础用法

### 1. 创建资产

```python
from asset_sdk import AssetClient

client = AssetClient()

# 基本创建
asset = client.create_asset(
    name="Web服务器-01",
    asset_type="Server",
    ip_address="192.168.1.100",
    username="admin",
    password="secret123"
)

# 完整创建（包含P0/P1字段）
asset = client.create_asset(
    name="核心数据库服务器",
    asset_type="Server",
    ip_address="192.168.1.200",
    username="dbadmin",
    password="db_password",
    # P0 SSH连接信息
    ssh_port=2222,
    hostname="db-server.example.com",
    management_ip="192.168.1.201",
    # P0 服务和端口
    services=["mysql", "redis"],
    open_ports=[3306, 6379, 22],
    # P0 安全相关
    risk_score=30,
    isolation_status="normal",
    # P0 网络分类
    device_role="database",
    vlan_ids=[100],
    network_segment="192.168.1.0/24",
    # P1 硬件配置
    cpu_cores=16,
    memory_gb=64,
    disk_gb=1000,
    # P1 合规与扫描
    compliance_status="compliant",
    fqdn="db-server.example.com",
    # 其他
    importance="critical",
    environment="production",
    owner="DBA团队",
    department="运维部",
    location="数据中心A区",
    vendor="Dell",
    model="PowerEdge R740",
    os_type="CentOS",
    os_version="7.9",
    changed_by="admin"
)
```

### 2. 查询资产

```python
# 按类型查询
servers = client.list_assets(asset_type="Server")

# 多条件查询
prod_servers = client.list_assets(
    asset_type="Server",
    environment="production",
    importance="critical"
)

# 按IP查询
asset = client.get_asset_by_ip("192.168.1.100")

# 按名称查询
asset = client.get_asset_by_name("Web服务器-01")

# 关键字搜索
results = client.find_assets("web")

# 按风险分数查询
high_risk = client.list_assets_by_risk(min_score=60)

# 按隔离状态查询
isolated = client.list_assets_by_isolation_status("network")

# 按网段查询
segment_assets = client.list_assets_by_network_segment("192.168.1.0/24")
```

### 3. 更新资产

```python
# 更新单个字段
client.update_asset(
    asset_id,
    description="更新描述",
    changed_by="admin"
)

# 更新多个字段
client.update_asset(
    asset_id,
    cpu_cores=32,
    memory_gb=128,
    risk_score=50,
    changed_by="admin",
    change_reason="硬件升级"
)
```

### 4. 删除资产

```python
# 软删除（保留数据，状态改为deleted）
client.delete_asset(
    asset_id,
    hard_delete=False,
    changed_by="admin",
    change_reason="设备退役"
)

# 硬删除（物理删除）
client.delete_asset(
    asset_id,
    hard_delete=True,
    changed_by="admin"
)
```

---

## API参考

### 基础CRUD操作

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `create_asset()` | name, asset_type, ip_address, ... | Dict | 创建资产 |
| `get_asset()` | asset_id | Dict/None | 获取资产详情 |
| `update_asset()` | asset_id, **kwargs | Dict/None | 更新资产 |
| `delete_asset()` | asset_id, hard_delete | bool | 删除资产 |

### 查询操作

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `list_assets()` | asset_type, status, importance, environment, owner, ip_range, limit, offset | List[Dict] | 列出资产 |
| `find_assets()` | keyword, fields, limit | List[Dict] | 关键字搜索 |
| `get_asset_by_ip()` | ip_address | Dict/None | 按IP查询 |
| `get_asset_by_name()` | name | Dict/None | 按名称查询 |
| `list_assets_by_risk()` | min_score, max_score, limit | List[Dict] | 按风险分数查询 |
| `list_assets_by_isolation_status()` | isolation_status, limit | List[Dict] | 按隔离状态查询 |
| `list_assets_by_network_segment()` | network_segment, limit | List[Dict] | 按网段查询 |

### 批量操作

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `batch_create()` | assets, dry_run, changed_by | Dict | 批量创建 |
| `batch_update()` | updates, dry_run, changed_by | Dict | 批量更新 |
| `batch_delete()` | asset_ids, hard_delete, changed_by | Dict | 批量删除 |
| `batch_get()` | asset_ids | List[Dict] | 批量获取 |

### 密码管理

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_password()` | asset_id | str/None | 获取解密后的密码 |
| `update_password()` | asset_id, new_password, changed_by | bool | 更新密码 |

### 统计分析

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `get_statistics()` | by_type, by_status, by_environment, by_importance, by_vendor, by_owner | Dict | 多维度统计 |
| `get_change_history()` | asset_id, limit | List[Dict] | 获取变更历史 |
| `get_audit_logs()` | asset_id, change_type, start_date, end_date, changed_by, limit | List[Dict] | 获取审计日志 |
| `get_risk_report()` | asset_type, environment, min_score, include_details | Dict | 生成风险报告 |

### 资产关系

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `add_relationship()` | source_id, target_id, relation_type, description, created_by | Dict | 添加资产关系 |
| `get_relationships()` | asset_id, direction | List[Dict] | 获取资产关系 |
| `remove_relationship()` | relationship_id | bool | 删除资产关系 |

### 其他功能

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `export_assets()` | format, asset_ids, **filters | str/bytes | 导出资产数据（JSON/CSV） |
| `health_check()` | asset_id, asset_ids, check_type | Dict | 健康检查（连通性/端口） |

---

## 最佳实践

### 1. 变更时记录原因

```python
# 好的做法
client.update_asset(
    asset_id,
    status='maintenance',
    changed_by='server-ops',
    change_reason='计划维护窗口'
)

# 不好的做法
client.update_asset(asset_id, status='maintenance')
```

### 2. 批量操作使用试运行

```python
# 先试运行
result = client.batch_create(assets, dry_run=True)
print(f"预计创建 {result['total']} 个资产")

# 确认无误后再执行
result = client.batch_create(assets, dry_run=False)
```

### 3. 风险评分标准

| 分数范围 | 风险等级 | 说明 | 建议操作 |
|---------|---------|------|---------|
| 0-39 | 低 | 低风险资产 | 常规巡检 |
| 40-59 | 中 | 中等风险 | 加强监控 |
| 60-79 | 高 | 高风险，需要关注 | 立即检查 |
| 80-100 | 严重 | 严重风险，需要立即处理 | 启动应急响应 |

### 4. 隔离状态使用

```python
# 网络隔离 - 阻断外部访问，但内部仍可访问
client.update_asset(asset_id, isolation_status='network')

# 主机隔离 - 完全禁止访问
client.update_asset(asset_id, isolation_status='host')

# 解除隔离
client.update_asset(asset_id, isolation_status='normal')
```

### 5. 使用自定义数据库

```python
# 开发/测试时使用单独数据库
dev_client = AssetClient(db_path='./data/dev_assets.db')

# 生产环境使用默认数据库
prod_client = AssetClient()
```

---

## 常见问题

### Q1: 如何处理并发写入错误？

A: SDK内置了自动重试机制，最多重试15次。如果仍然失败：
```python
# 使用文件锁（SDK自动处理）
from asset_sdk import AssetClient
client = AssetClient()
```

### Q2: 密码如何存储？

A: 密码使用AES-256-GCM加密存储：
```python
# 创建时传入明文
asset = client.create_asset(..., password="secret123")

# 获取时解密
password = client.get_password(asset_id)  # 返回明文
```

### Q3: 如何导出资产数据？

A: 支持JSON和CSV格式：
```python
# JSON导出
json_data = client.export_assets(format="json")
with open('assets.json', 'w') as f:
    f.write(json_data)

# CSV导出
csv_data = client.export_assets(format="csv")
with open('assets.csv', 'w') as f:
    f.write(csv_data)
```

### Q4: 如何进行健康检查？

A: 支持连通性和端口检查：
```python
# 检查连通性（ICMP ping）
result = client.health_check(
    asset_id=asset_id,
    check_type="connectivity"
)
# status: reachable/unreachable

# 检查端口
result = client.health_check(
    asset_id=asset_id,
    check_type="port"
)
# status: open/closed
```

### Q5: 数据库文件在哪里？

A: 默认位置：
```
teams/ai-security-team/asset-database/data/assets.db
```

加密密钥：
```
teams/ai-security-team/asset-database/data/.secret_key
```

### Q6: 如何备份和恢复数据库？

A: 直接复制数据库文件：
```bash
# 备份
cp data/assets.db data/assets_backup_$(date +%Y%m%d).db

# 恢复
cp data/assets_backup_20260226.db data/assets.db
```

### Q7: 支持哪些资产类型？

A: 共7种：
- `NetworkDevice` - 网络设备
- `SecurityDevice` - 安全设备
- `Server` - 服务器
- `Terminal` - 终端
- `Database` - 数据库
- `Application` - 应用系统
- `Other` - 其他

### Q8: 如何清空测试数据？

A: 删除测试数据库文件：
```bash
rm data/test_assets.db
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 项目说明和快速参考 |
| [DATA_MODEL.md](./DATA_MODEL.md) | 完整的数据模型和API文档 |
| [ASSET_DATABASE_FIELDS.md](./ASSET_DATABASE_FIELDS.md) | 字段详细说明 |
| [CHANGELOG.md](./CHANGELOG.md) | 版本变更记录 |

---

*负责人: asset-mgmt*
*版本: v4.0*
*更新日期: 2026-02-26*
