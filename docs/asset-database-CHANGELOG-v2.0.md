# 资产库更新通知 (v2.0)

> 更新日期: 2026-02-14
> 更新版本: v2.0.0

---

## 重要变更

### 1. 资产类型简化 (8种 → 4种)

| 旧类型 | 新类型 | 说明 |
|--------|--------|------|
| Network | NetworkDevice | 网络设备 |
| Security | SecurityDevice | 网络安全设备 |
| Server, Virtual, Storage, Database, Application | Server | 服务器 |
| Endpoint | Terminal | 终端 |

**请使用新的 `asset_type` 字段代替旧的 `type` 字段**

### 2. 新增必填字段

- `username` - 设备账号（必填）

### 3. 新增可选字段

- `system_version` - 系统版本
- `location` - 物理位置（合并了旧的 site/building/floor/room）
- `remote_protocol` - 远程协议 (SSH/Telnet/HTTP/HTTPS/SNMP/API)
- `password` - 设备密码（自动 AES-256-GCM 加密存储）
- `notes` - 备注

### 4. 密码安全存储

- 密码使用 **AES-256-GCM** 加密存储
- API 响应中**不会返回密码**
- 需要密码时调用专用接口获取

---

## API 变更

### 创建资产（新版）

```
POST /api/v1/assets/
```

```json
{
  "name": "核心交换机-01",
  "asset_type": "NetworkDevice",
  "manufacturer": "华为",
  "model": "S5735-L48T4S-A",
  "ip_address": "192.168.1.1",
  "system_version": "V200R019C10",
  "location": "机房A-3F-机柜05",
  "remote_protocol": "SSH",
  "username": "admin",
  "password": "MySecretPassword",
  "notes": "核心层交换机",
  "importance": "critical",
  "environment": "production",
  "owner": "网络运维组"
}
```

### 获取解密密码（新增）

```
GET /api/v1/assets/{asset_id}/password
```

响应:
```json
{
  "password": "MySecretPassword"
}
```

### 查询过滤（新增）

- 按厂商过滤: `?manufacturer=华为`
- 按远程协议过滤: `?remote_protocol=SSH`
- 按资产类型过滤: `?asset_type=NetworkDevice`

### 统计接口（更新）

```
GET /api/v1/assets/statistics/summary
```

新增 `by_asset_type` 和 `by_remote_protocol` 统计

---

## 迁移指南

### 对于 Agent 开发者

1. **创建资产时**:
   - 必须提供 `username`
   - 使用 `asset_type` 而非 `type`
   - 密码会自动加密，无需手动处理

2. **查询资产时**:
   - 响应中不包含密码
   - 需要密码时调用 `/api/v1/assets/{id}/password`

3. **过滤查询时**:
   - 使用新的过滤参数
   - `asset_type` 代替 `type`

### 字段映射

| 旧字段 | 新字段 |
|--------|--------|
| type | asset_type |
| site, building, floor, room, rack | location |
| mac_address, hostname, fqdn, etc. | meta_data (扩展) |
| cvss_score, vulnerability_count | meta_data (扩展) |

---

## 快速测试

```bash
# 启动服务
cd teams/ai-security-team/asset-database
python -m uvicorn api.database:app --reload

# 访问 API 文档
# http://127.0.0.1:8000/docs

# 创建测试资产
curl -X POST http://127.0.0.1:8000/api/v1/assets/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-switch",
    "asset_type": "NetworkDevice",
    "ip_address": "192.168.1.1",
    "remote_protocol": "SSH",
    "username": "admin",
    "password": "test123"
  }'
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `api/schemas/asset.py` | Schema 定义 |
| `api/models/asset.py` | 数据库模型 |
| `api/routes/assets.py` | API 路由 |
| `api/utils/crypto.py` | 加密工具 |
| `.env` | 加密密钥配置 |

---

如有问题，请联系团队负责人。
