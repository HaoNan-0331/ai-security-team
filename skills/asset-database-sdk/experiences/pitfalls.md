# 资产库SDK使用常见陷阱

> 版本: v4.0 | 更新日期: 2026-02-26

---

## ⚠️ 重要警告

### 1. 永远不要在日志中打印密码

```python
# 错误 ❌
password = client.get_password(asset_id)
print(f"密码: {password}")  # 密码会记录到日志

# 正确 ✅
password = client.get_password(asset_id)
# 直接使用，不要打印
ssh.connect(host, username=user, password=password)
```

### 2. 不要硬编码资产ID

```python
# 错误 ❌
asset_id = "a1b2c3d4-e5f6-..."  # 硬编码

# 正确 ✅
asset = client.get_asset_by_ip("192.168.1.100")
asset_id = asset['asset_id']
```

### 3. 批量操作前不验证数据

```python
# 错误 ❌
client.batch_create(large_data_list, changed_by="admin")  # 直接执行

# 正确 ✅
result = client.batch_create(large_data_list, dry_run=True)  # 先试运行
if result['invalid_count'] == 0:
    result = client.batch_create(large_data_list, dry_run=False)
```

---

## 常见陷阱

### 陷阱1: 忘记记录变更原因

**问题**: 更新资产时不记录变更原因，导致审计困难

```python
# 错误 ❌
client.update_asset(asset_id, status="maintenance")

# 正确 ✅
client.update_asset(
    asset_id,
    status="maintenance",
    changed_by="server-ops",
    change_reason="计划维护窗口 - 安全补丁更新"
)
```

---

### 陷阱2: JSON字段格式错误

**问题**: services/open_ports/vlan_ids等字段格式不正确

```python
# 错误 ❌
client.create_asset(
    ...,
    services="nginx,mysql",  # 字符串格式错误
    open_ports="22,80,443"   # 字符串格式错误
)

# 正确 ✅
client.create_asset(
    ...,
    services=["nginx", "mysql"],  # 列表格式
    open_ports=[22, 80, 443]      # 列表格式
)

# 或者使用JSON字符串
client.create_asset(
    ...,
    services='["nginx", "mysql"]',
    open_ports='[22, 80, 443]'
)
```

---

### 陷阱3: 风险评分超出范围

**问题**: risk_score必须在0-100之间

```python
# 错误 ❌
client.update_asset(asset_id, risk_score=150)  # 超出范围

# 正确 ✅
risk_score = max(0, min(100, risk_score))  # 限制范围
client.update_asset(asset_id, risk_score=risk_score)
```

---

### 陷阱4: 并发写入导致数据库锁定

**问题**: 多个Agent同时写入可能导致数据库锁定

```python
# 解决方案: SDK内置重试机制，无需额外处理
# 但建议批量操作时加锁或错峰执行

import time

def safe_batch_update(client, updates, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.batch_update(updates)
        except Exception as e:
            if "locked" in str(e).lower():
                time.sleep(2 ** attempt)  # 指数退避
                continue
            raise
```

---

### 陷阱5: 查询结果为None时的处理

**问题**: get_asset/get_asset_by_ip/get_asset_by_name可能返回None

```python
# 错误 ❌
asset = client.get_asset(asset_id)
name = asset['name']  # 可能报错: 'NoneType' object is not subscriptable

# 正确 ✅
asset = client.get_asset(asset_id)
if asset:
    name = asset['name']
else:
    print(f"资产 {asset_id} 不存在")
```

---

### 陷阱6: 隔离状态与资产状态混淆

**问题**: isolation_status和status是两个不同的字段

```python
# 错误 ❌
client.update_asset(asset_id, status="network")  # status应该是"isolated"

# 正确 ✅
client.update_asset(
    asset_id,
    status="isolated",           # 资产状态
    isolation_status="network"  # 隔离状态
)
```

---

### 陷阱7: 批量删除不使用硬删除

**问题**: 默认delete_asset是软删除，数据仍在数据库中

```python
# 默认软删除 - 数据保留，状态改为deleted
client.delete_asset(asset_id, changed_by="admin")

# 如果需要物理删除，必须明确指定
client.delete_asset(asset_id, hard_delete=True, changed_by="admin")
```

---

### 陷阱8: 健康检查超时处理

**问题**: 健康检查可能因为网络问题超时

```python
# 错误 ❌
result = client.health_check(asset_id=asset_id, check_type="connectivity")
# 如果网络不通，可能长时间等待

# 正确 ✅
import socket

def is_port_open(host, port, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except:
        return False
```

---

### 陷阱9: 导出数据时编码问题

**问题**: Windows系统导出CSV可能遇到编码问题

```python
# 错误 ❌
csv_data = client.export_assets(format="csv")
with open('assets.csv', 'w') as f:  # Windows可能乱码
    f.write(csv_data)

# 正确 ✅
csv_data = client.export_assets(format="csv")
with open('assets.csv', 'w', encoding='utf-8-sig') as f:  # BOM解决Excel乱码
    f.write(csv_data)
```

---

### 陷阱10: 忽略审计日志的查询限制

**问题**: 大量资产审计日志可能导致性能问题

```python
# 错误 ❌
logs = client.get_audit_logs()  # 可能返回大量数据

# 正确 ✅
logs = client.get_audit_logs(
    asset_id=asset_id,        # 限定资产
    start_date="2026-02-01",  # 限定时间范围
    end_date="2026-02-28",
    limit=100                 # 限制返回数量
)
```

---

### 陷阱11: 使用错误的数据库路径

**问题**: 多环境时可能连接到错误的数据库

```python
# 错误 ❌
client = AssetClient()  # 可能连接到错误的数据库

# 正确 ✅
import os
env = os.getenv('ENVIRONMENT', 'development')
db_path = f'./data/{env}_assets.db'
client = AssetClient(db_path=db_path)
```

---

### 陷阱12: 资产关系创建自关联

**问题**: 不能将资产关联到自己

```python
# 错误 ❌
client.add_relationship(
    source_id=asset_id,
    target_id=asset_id,  # 同一个ID
    relation_type="depends_on"
)

# 正确 ✅
if source_id == target_id:
    raise ValueError("不能创建自关联")
```

---

### 陷阱13: 批量操作不检查返回结果

**问题**: 批量操作可能部分失败，但代码不检查

```python
# 错误 ❌
client.batch_create(assets, changed_by="admin")
# 假设全部成功

# 正确 ✅
result = client.batch_create(assets, changed_by="admin")
print(f"成功: {result['success_count']}, 失败: {result['failed_count']}")

if result['failed_count'] > 0:
    for item in result['failed_items']:
        print(f"失败: {item}")
```

---

### 陷阱14: 查询时不使用limit

**问题**: 大数据量查询可能返回过多结果

```python
# 错误 ❌
assets = client.list_assets()  # 可能返回所有资产

# 正确 ✅
assets = client.list_assets(limit=100)  # 限制返回数量
```

---

### 陷阱15: 硬删除后无法恢复

**问题**: 硬删除的数据无法恢复

```python
# 警告 ⚠️
client.delete_asset(asset_id, hard_delete=True, changed_by="admin")
# 数据永久删除，无法恢复

# 建议: 先软删除，确认后再硬删除
client.delete_asset(asset_id, hard_delete=False, changed_by="admin")
# ... 确认无误后
client.delete_asset(asset_id, hard_delete=True, changed_by="admin")
```

---

## 最佳实践总结

### ✅ 推荐做法

| 实践 | 说明 |
|------|------|
| 批量操作前试运行 | 使用dry_run=True预览结果 |
| 始终记录变更原因 | 使用changed_by和change_reason |
| 检查None返回值 | get_asset可能返回None |
| 使用查询限制 | 使用limit控制返回数量 |
| 验证输入参数 | 检查类型、范围、格式 |
| 处理异常情况 | 捕获并处理数据库异常 |
| 定期备份数据 | 使用asset_backup.py或手动备份 |
| 避免日志密码 | 不要在日志中打印密码 |
| 使用标准枚举值 | 使用标准资产类型、状态等 |
| 检查批量操作结果 | 检查success_count和failed_count |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-26 | 初始版本 |

---

*负责人: asset-mgmt*
