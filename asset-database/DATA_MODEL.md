# 资产库数据模型文档

> 版本: v4.0 | 更新日期: 2026-02-17

---

## 概述

资产库是AI安全团队的核心资产管理系统，采用纯SDK方案，通过Python SDK直接访问SQLite数据库，支持并发访问和批量操作。

---

## 数据模型

### Asset表（资产主表）

资产主表包含45个字段，覆盖资产的全生命周期管理。

#### 基本信息

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| asset_id | String(36) | 资产ID（UUID主键） | `a1b2c3d4-e5f6-...` |
| name | String(200) | 资产名称（必填） | `Web服务器-01` |
| asset_type | String(50) | 资产类型（必填） | `Server` |
| ip_address | String(50) | IP地址 | `192.168.1.100` |
| mac_address | String(50) | MAC地址 | `00:11:22:33:44:55` |
| port | Integer | 端口号 | `443` |
| username | String(100) | 登录用户名 | `admin` |
| password_encrypted | Text | 加密后的密码 | `gAAAAABl...` |
| description | Text | 描述 | `主Web服务器` |
| tags | String(500) | 标签（逗号分隔） | `web,production,critical` |
| custom_fields | Text | 自定义字段（JSON） | `{"backup": true}` |

#### 分类属性

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| status | String(20) | `active` | 资产状态 |
| importance | String(20) | `medium` | 重要性 |
| environment | String(20) | `production` | 环境 |

#### 责任归属

| 字段 | 类型 | 说明 |
|------|------|------|
| owner | String(100) | 负责人 |
| department | String(100) | 所属部门 |
| location | String(200) | 物理位置 |

#### 硬件信息

| 字段 | 类型 | 说明 |
|------|------|------|
| vendor | String(100) | 厂商 |
| model | String(100) | 型号 |
| os_type | String(100) | 操作系统类型 |
| os_version | String(100) | 操作系统版本 |
| firmware_version | String(100) | 固件版本 |
| serial_number | String(100) | 序列号 |

#### P0 高优先级字段 - SSH连接信息

| 字段 | 类型 | 说明 |
|------|------|------|
| ssh_port | Integer | SSH端口 |
| hostname | String(200) | 主机名 |
| management_ip | String(50) | 管理IP地址 |

#### P0 高优先级字段 - 服务和端口

| 字段 | 类型 | 说明 |
|------|------|------|
| services | Text | 运行的服务（JSON格式） |
| open_ports | Text | 开放端口列表（JSON格式） |

#### P0 高优先级字段 - 安全相关

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| risk_score | Integer | `0` | 风险评分（0-100） |
| isolation_status | String(20) | `normal` | 隔离状态 |

#### P0 高优先级字段 - 网络分类

| 字段 | 类型 | 说明 |
|------|------|------|
| device_role | String(50) | 设备角色 |
| vlan_ids | Text | VLAN ID列表（JSON格式） |
| network_segment | String(50) | 网段标识 |

#### P1 中优先级字段 - 硬件配置

| 字段 | 类型 | 说明 |
|------|------|------|
| cpu_cores | Integer | CPU核心数 |
| memory_gb | Integer | 内存大小(GB) |
| disk_gb | Integer | 磁盘大小(GB) |

#### P1 中优先级字段 - 合规与扫描

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| last_scan_date | DateTime | - | 最后扫描日期 |
| compliance_status | String(20) | `unknown` | 合规状态 |
| fqdn | String(255) | - | 完全限定域名 |

#### 补丁管理

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| last_patch_date | DateTime | - | 最后补丁日期 |
| patch_status | String(50) | `unknown` | 补丁状态 |
| vulnerability_count | Integer | `0` | 漏洞数量 |

#### 时间戳

| 字段 | 类型 | 说明 |
|------|------|------|
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| last_seen_at | DateTime | 最后发现时间 |

---

### AssetChangeLog表（变更日志表）

| 字段 | 类型 | 说明 |
|------|------|------|
| log_id | String(36) | 日志ID（UUID主键） |
| asset_id | String(36) | 资产ID（外键） |
| change_type | String(50) | 变更类型：create/update/delete/password |
| field_name | String(100) | 变更字段 |
| old_value | Text | 旧值 |
| new_value | Text | 新值 |
| changed_by | String(100) | 变更人 |
| change_reason | Text | 变更原因 |
| created_at | DateTime | 变更时间 |

---

### asset_relationships表（资产关系表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | String(36) | 关系ID（UUID主键） |
| source_id | String(36) | 源资产ID（外键） |
| target_id | String(36) | 目标资产ID（外键） |
| relation_type | String(50) | 关系类型 |
| description | Text | 关系描述 |
| created_at | DateTime | 创建时间 |
| created_by | String(100) | 创建人 |

---

## 枚举类型

### AssetType（资产类型）- 7种

| 枚举值 | 字符串值 | 说明 |
|--------|----------|------|
| NETWORK_DEVICE | NetworkDevice | 网络设备（交换机、路由器） |
| SECURITY_DEVICE | SecurityDevice | 安全设备（防火墙、IDS/IPS） |
| SERVER | Server | 服务器 |
| TERMINAL | Terminal | 终端（PC、笔记本） |
| DATABASE | Database | 数据库 |
| APPLICATION | Application | 应用系统 |
| OTHER | Other | 其他 |

### AssetStatus（资产状态）- 9种

| 枚举值 | 字符串值 | 说明 |
|--------|----------|------|
| ACTIVE | active | 在用 |
| STANDBY | standby | 备用 |
| MAINTENANCE | maintenance | 维护中 |
| RETIRED | retired | 已退役 |
| COMPROMISED | compromised | 已失陷 |
| INVESTIGATING | investigating | 调查中 |
| ISOLATED | isolated | 已隔离 |
| REMEDIATED | remediated | 已修复 |
| UNKNOWN | unknown | 状态未知 |

### AssetImportance（重要性）- 4种

| 枚举值 | 字符串值 | 说明 |
|--------|----------|------|
| CRITICAL | critical | 关键资产 |
| HIGH | high | 重要资产 |
| MEDIUM | medium | 一般资产 |
| LOW | low | 非重要资产 |

### AssetEnvironment（环境）- 5种

| 枚举值 | 字符串值 | 说明 |
|--------|----------|------|
| PRODUCTION | production | 生产环境 |
| DEVELOPMENT | development | 开发环境 |
| TEST | test | 测试环境 |
| STAGING | staging | 预发布环境 |
| DMZ | dmz | DMZ区域 |

---

## SDK API文档

### 基础CRUD操作

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `create_asset()` | 创建资产 | name, asset_type, ... | Dict |
| `get_asset()` | 获取资产 | asset_id | Dict/None |
| `update_asset()` | 更新资产 | asset_id, **kwargs | Dict/None |
| `delete_asset()` | 删除资产 | asset_id, hard_delete | bool |

### 查询操作

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `list_assets()` | 列出资产 | type, status, environment, ... | List[Dict] |
| `find_assets()` | 搜索资产 | keyword, fields, limit | List[Dict] |
| `get_asset_by_ip()` | 按IP查询 | ip_address | Dict/None |
| `get_asset_by_name()` | 按名称查询 | name | Dict/None |
| `list_assets_by_risk()` | 按风险查询 | min_score, max_score | List[Dict] |
| `list_assets_by_isolation_status()` | 按隔离状态查询 | isolation_status | List[Dict] |
| `list_assets_by_network_segment()` | 按网段查询 | network_segment | List[Dict] |

### 批量操作

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `batch_create()` | 批量创建 | assets, dry_run | Dict |
| `batch_update()` | 批量更新 | updates, dry_run | Dict |
| `batch_delete()` | 批量删除 | asset_ids, hard_delete | Dict |
| `batch_get()` | 批量获取 | asset_ids | List[Dict] |

### 密码管理

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_password()` | 获取密码 | asset_id | str/None |
| `update_password()` | 更新密码 | asset_id, new_password | bool |

### 新增功能

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `health_check()` | 健康检查 | asset_id/asset_ids, check_type | Dict |
| `get_audit_logs()` | 审计日志 | asset_id, change_type, ... | List[Dict] |
| `get_risk_report()` | 风险报告 | asset_type, min_score, ... | Dict |
| `get_statistics()` | 统计分析 | by_type, by_status, ... | Dict |
| `get_change_history()` | 变更历史 | asset_id, limit | List[Dict] |

### 资产关系

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `add_relationship()` | 添加关系 | source_id, target_id, relation_type | Dict |
| `get_relationships()` | 获取关系 | asset_id, direction | List[Dict] |
| `remove_relationship()` | 删除关系 | relationship_id | bool |

### 导出功能

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `export_assets()` | 导出资产 | format, asset_ids, ... | str/bytes |

---

## 最佳实践

### 1. 使用SDK

```python
import sys
sys.path.insert(0, 'teams/ai-security-team/asset-database')
from asset_sdk import AssetClient

client = AssetClient()
```

### 2. 变更时记录原因

```python
client.update_asset(
    asset_id,
    status='maintenance',
    changed_by='server-ops',
    change_reason='计划维护'
)
```

### 3. 风险评分标准

| 分数范围 | 风险等级 | 说明 |
|---------|---------|------|
| 0-39 | 低 | 低风险资产 |
| 40-59 | 中 | 中等风险 |
| 60-79 | 高 | 高风险，需要关注 |
| 80-100 | 严重 | 严重风险，需要立即处理 |

### 4. 隔离状态使用

| 状态 | 使用场景 |
|------|---------|
| normal | 正常运行 |
| network | 网络隔离，阻断外部访问 |
| host | 主机隔离，完全禁止访问 |

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v4.0 | 2026-02-17 | 纯SDK方案；新增P0/P1字段；新增健康检查、审计日志、风险报告功能 |
| v2.0 | 2026-02-15 | 新增批量操作和统计分析 |
| v1.0 | 2026-02-10 | 初始版本 |
