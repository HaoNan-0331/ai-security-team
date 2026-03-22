---
name: asset-database-sdk
description: AI Security Team资产库SDK使用技能。提供资产CRUD、查询、批量操作、密码管理、统计分析、健康检查、风险报告等功能集成。适用于资产管理、服务器运维、网络运维、威胁响应等场景。
---

# 资产库SDK使用技能

> 版本: v4.0 | 更新日期: 2026-02-26

---

## 快速开始

### 3行代码上手

```python
import sys
sys.path.insert(0, 'teams/ai-security-team/asset-database')
from asset_sdk import AssetClient

client = AssetClient()
```

### 5分钟快速体验

```python
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

## API速查表

### 基础CRUD

| 方法 | 用途 | 示例 |
|------|------|------|
| `create_asset()` | 创建资产 | `client.create_asset(name="Server", asset_type="Server", ...)` |
| `get_asset()` | 获取资产 | `client.get_asset(asset_id)` |
| `update_asset()` | 更新资产 | `client.update_asset(asset_id, status="maintenance")` |
| `delete_asset()` | 删除资产 | `client.delete_asset(asset_id)` |

### 查询操作

| 方法 | 用途 | 示例 |
|------|------|------|
| `list_assets()` | 列出资产 | `client.list_assets(asset_type="Server", environment="production")` |
| `find_assets()` | 关键字搜索 | `client.find_assets("web")` |
| `get_asset_by_ip()` | 按IP查询 | `client.get_asset_by_ip("192.168.1.100")` |
| `get_asset_by_name()` | 按名称查询 | `client.get_asset_by_name("Web服务器-01")` |
| `list_assets_by_risk()` | 按风险查询 | `client.list_assets_by_risk(min_score=60)` |
| `list_assets_by_isolation_status()` | 按隔离状态查询 | `client.list_assets_by_isolation_status("network")` |
| `list_assets_by_network_segment()` | 按网段查询 | `client.list_assets_by_network_segment("192.168.1.0/24")` |

### 批量操作

| 方法 | 用途 | 示例 |
|------|------|------|
| `batch_create()` | 批量创建 | `client.batch_create(assets, changed_by="admin")` |
| `batch_update()` | 批量更新 | `client.batch_update(updates, changed_by="admin")` |
| `batch_delete()` | 批量删除 | `client.batch_delete([id1, id2], changed_by="admin")` |
| `batch_get()` | 批量获取 | `client.batch_get([id1, id2, id3])` |

### 密码管理

| 方法 | 用途 | 示例 |
|------|------|------|
| `get_password()` | 获取密码 | `password = client.get_password(asset_id)` |
| `update_password()` | 更新密码 | `client.update_password(asset_id, "new_password")` |

### 统计分析

| 方法 | 用途 | 示例 |
|------|------|------|
| `get_statistics()` | 多维度统计 | `client.get_statistics(by_type=True, by_status=True)` |
| `get_risk_report()` | 风险报告 | `client.get_risk_report(min_score=50)` |
| `get_change_history()` | 变更历史 | `client.get_change_history(asset_id, limit=10)` |
| `get_audit_logs()` | 审计日志 | `client.get_audit_logs(asset_id=asset_id)` |

### 健康检查

| 方法 | 用途 | 示例 |
|------|------|------|
| `health_check()` | 健康检查 | `client.health_check(asset_id=asset_id, check_type="connectivity")` |

### 资产关系

| 方法 | 用途 | 示例 |
|------|------|------|
| `add_relationship()` | 添加关系 | `client.add_relationship(source_id, target_id, "depends_on")` |
| `get_relationships()` | 获取关系 | `client.get_relationships(asset_id=server_id)` |
| `remove_relationship()` | 删除关系 | `client.remove_relationship(relationship_id)` |

### 导出功能

| 方法 | 用途 | 示例 |
|------|------|------|
| `export_assets()` | 导出资产 | `client.export_assets(format="json")` |

---

## Agent使用场景

### server-ops（服务器运维）

```python
# 获取服务器列表
servers = client.list_assets(asset_type="Server", environment="production")

# 获取登录凭据
asset = client.get_asset(asset_id)
password = client.get_password(asset_id)
ssh_port = asset.get('ssh_port', 22)

# 更新硬件信息
client.update_asset(
    asset_id,
    cpu_cores=16,
    memory_gb=64,
    changed_by='server-ops',
    change_reason='硬件升级'
)

# 健康检查
result = client.health_check(asset_id=asset_id, check_type="connectivity")
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

# 按网段查询
segment_assets = client.list_assets_by_network_segment("192.168.1.0/24")
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
# 批量创建
result = client.batch_create([
    {"name": "Server-01", "asset_type": "Server", "ip_address": "192.168.1.10"},
    {"name": "Server-02", "asset_type": "Server", "ip_address": "192.168.1.11"},
], changed_by="asset-mgmt")

# 统计分析
stats = client.get_statistics(by_type=True, by_status=True, by_importance=True)

# 健康检查
result = client.health_check(asset_ids=[id1, id2, id3], check_type="connectivity")

# 导出资产
json_data = client.export_assets(format="json")
```

### vuln-assessment（漏洞评估）

```python
# 获取需要扫描的资产
servers = client.list_assets(
    asset_type="Server",
    environment="production",
    status="active"
)

# 更新漏洞数量
client.update_asset(
    asset_id,
    vulnerability_count=5,
    changed_by='vuln-assessment',
    change_reason='完成漏洞扫描'
)

# 按风险分数查询
high_risk = client.list_assets_by_risk(min_score=60)

# 生成风险报告
report = client.get_risk_report(min_score=50)
```

### compliance（合规检查）

```python
# 获取关键资产列表
critical_assets = client.list_assets(importance='critical')

# 获取生产环境资产
prod_assets = client.list_assets(environment='production')

# 多维度统计
stats = client.get_statistics(
    by_type=True,
    by_status=True,
    by_importance=True
)
```

### incident-response（事件响应）

```python
# 获取受影响资产详情
asset = client.get_asset(asset_id)

# 查询变更历史
history = client.get_change_history(asset_id, limit=50)

# 获取资产关系（影响分析）
relations = client.get_relationships(asset_id)
```

### alert-judgment（告警研判）

```python
# 获取资产重要性信息
asset = client.get_asset(asset_id)
importance = asset.get('importance')

# 批量获取相关资产
related_assets = client.batch_get([id1, id2, id3])

# 获取资产关系（用于事件关联）
relations = client.get_relationships(asset_id)
```

### pentest（渗透测试）

```python
# 获取测试目标资产
asset = client.get_asset(asset_id)

# 获取资产登录凭据（授权情况下）
password = client.get_password(asset_id)
ssh_port = asset.get('ssh_port', 22)

# 更新测试结果
client.update_asset(
    asset_id,
    vuln_count=3,
    changed_by='pentest',
    change_reason='完成渗透测试'
)
```

---

## 枚举值速查

### 资产类型 (asset_type)

| 值 | 说明 |
|----|------|
| `NetworkDevice` | 网络设备（交换机、路由器） |
| `SecurityDevice` | 安全设备（防火墙、IDS/IPS） |
| `Server` | 服务器 |
| `Terminal` | 终端（PC、笔记本） |
| `Database` | 数据库 |
| `Application` | 应用系统 |
| `Other` | 其他 |

### 资产状态 (status)

| 值 | 说明 |
|----|------|
| `active` | 在用 |
| `standby` | 备用 |
| `maintenance` | 维护中 |
| `retired` | 已退役 |
| `compromised` | 已失陷 |
| `investigating` | 调查中 |
| `isolated` | 已隔离 |
| `remediated` | 已修复 |
| `unknown` | 状态未知 |

### 隔离状态 (isolation_status)

| 值 | 说明 |
|----|------|
| `normal` | 正常运行 |
| `network` | 网络隔离（阻断外部访问） |
| `host` | 主机隔离（完全禁止访问） |

### 重要性 (importance)

| 值 | 说明 |
|----|------|
| `critical` | 关键资产 |
| `high` | 重要资产 |
| `medium` | 一般资产 |
| `low` | 非重要资产 |

### 环境 (environment)

| 值 | 说明 |
|----|------|
| `production` | 生产环境 |
| `development` | 开发环境 |
| `test` | 测试环境 |
| `staging` | 预发布环境 |
| `dmz` | DMZ区域 |

### 风险评分标准

| 分数范围 | 风险等级 | 说明 | 建议操作 |
|---------|---------|------|---------|
| 0-39 | 低 | 低风险资产 | 常规巡检 |
| 40-59 | 中 | 中等风险 | 加强监控 |
| 60-79 | 高 | 高风险，需要关注 | 立即检查 |
| 80-100 | 严重 | 严重风险，需要立即处理 | 启动应急响应 |

---

## 常见问题

### Q1: 如何处理并发写入错误？

SDK内置了自动重试机制，最多重试5次。如果仍然失败，检查是否有其他进程正在写入。

### Q2: 密码如何存储？

密码使用AES-256-GCM加密存储。创建时传入明文，获取时自动解密。

### Q3: 如何导出资产数据？

```python
# JSON导出
json_data = client.export_assets(format="json")

# CSV导出
csv_data = client.export_assets(format="csv")
```

### Q4: 如何进行健康检查？

```python
# 检查连通性（ICMP ping）
result = client.health_check(asset_id=asset_id, check_type="connectivity")

# 检查端口
result = client.health_check(asset_id=asset_id, check_type="port")
```

### Q5: 数据库文件在哪里？

```
teams/ai-security-team/asset-database/data/assets.db
teams/ai-security-team/asset-database/data/.secret_key
```

### Q6: 如何备份和恢复数据库？

```bash
# 备份
cp data/assets.db data/assets_backup_$(date +%Y%m%d).db

# 恢复
cp data/assets_backup_20260226.db data/assets.db
```

### Q7: 如何使用自定义数据库？

```python
# 使用自定义数据库路径
dev_client = AssetClient(db_path='./data/dev_assets.db')
```

### Q8: 批量操作如何使用试运行？

```python
# 先试运行
result = client.batch_create(assets, dry_run=True)
print(f"预计创建 {result['total']} 个资产")

# 确认无误后再执行
result = client.batch_create(assets, dry_run=False)
```

### Q9: 变更时如何记录原因？

```python
client.update_asset(
    asset_id,
    status='maintenance',
    changed_by='server-ops',
    change_reason='计划维护窗口'
)
```

### Q10: 如何查询已隔离资产？

```python
# 按隔离状态查询
isolated = client.list_assets_by_isolation_status("network")

# 或按状态查询
isolated_assets = client.list_assets(status="isolated")
```

---

## 辅助脚本

本技能提供以下辅助脚本（位于 `scripts/` 目录）：

| 脚本 | 用途 | 使用方式 |
|------|------|---------|
| `asset_query.py` | 交互式资产查询 | `python asset_query.py --type Server` |
| `asset_backup.py` | 资产库备份工具 | `python asset_backup.py --output /backup/` |
| `health_check.py` | 批量健康检查 | `python health_check.py --type Server` |

---

## 经验库

位于 `experiences/` 目录：

- `errors.json` - 常见错误及解决方案
- `solutions.json` - 最佳实践解决方案
- `pitfalls.md` - 常见陷阱和注意事项

---

## 示例代码

位于 `examples/` 目录：

- `agent_examples.py` - 各Agent使用示例代码
- `batch_import_example.json` - 批量导入示例数据

---

## 原始文档

完整文档位于 `teams/ai-security-team/asset-database/`：

- `README.md` - 项目说明
- `USER_GUIDE.md` - 使用手册
- `DATA_MODEL.md` - 数据模型和完整API文档
- `ASSET_DATABASE_FIELDS.md` - 字段详细说明

---

*负责人: asset-mgmt*
*版本: v4.0*
*更新日期: 2026-02-26*
