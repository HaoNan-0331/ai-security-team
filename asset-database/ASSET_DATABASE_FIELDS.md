# 资产库数据库字段说明

## 当前资产列表

### 1. Web-Server-Prod-01
- **资产ID**: 564dff55-2710-4a55-936a-f55a42f2437e
- **名称**: Web-Server-Prod-01
- **类型**: Server
- **IP 地址**: 10.0.1.10
- **重要性**: critical (关键)
- **环境**: production (生产)

### 2. Example-Server
- **资产ID**: 561d8f7c-2ebd-4447-8d00-c4190fefe9df
- **名称**: Example-Server
- **IP 地址**: 192.168.1.100
- **重要性**: null (未设置)

---

## 数据库字段分类

### 基本信息
- `asset_id` - 资产唯一标识符 (UUID)
- `name` - 资产名称
- `type` - 资产类型 (Server, Network, Security, Database, Application, Endpoint, Storage, Virtual)
- `manufacturer` - 制造商
- `model` - 型号
- `serial_number` - 序列号

### 网络信息
- `ip_address` - IP 地址
- `mac_address` - MAC 地址
- `hostname` - 主机名
- `fqdn` - 完全限定域名
- `subnet` - 子网
- `vlan` - VLAN 号
- `gateway` - 网关
- `dns_servers` - DNS 服务器

### 物理位置
- `site` - 站点 (如: Beijing-DC)
- `building` - 楼宇 (如: Building-A)
- `floor` - 楼层
- `room` - 房间
- `rack` - 机柜
- `rack_unit` - U 位

### 分类标签
- `importance` - 重要性 (critical, high, medium, low)
- `environment` - 环境 (production, staging, development, dr)
- `business_unit` - 业务单元
- `owner` - 责任人
- `cost_center` - 成本中心
- `asset_status` - 资产状态 (active, standby, retired, disposed, compromised, under_investigation, quarantined)

### 生命周期
- `lifecycle_stage` - 生命周期阶段
- `first_seen` - 首次发现时间
- `last_seen` - 最后发现时间
- `last_updated` - 最后更新时间

### 安全信息
- `cvss_score` - CVSS 评分 (0-10)
- `vulnerability_count` - 漏洞数量
- `compliance_level` - 合规等级 (compliant, non_compliant)
- `patch_level` - 补丁等级 (latest, outdated)

### 扩展配置 (JSON 字符串)
- `config` - 配置信息 (如: CPU, RAM, 磁盘等)
- `services` - 服务列表 (如: web, database, ssh 等)
- `relationships` - 资产关系 (如: 依赖、连接等)
- `meta_data` - 元数据 (自定义扩展字段)

### 审计信息
- `created_by` - 创建者
- `created_at` - 创建时间
- `updated_by` - 更新者
- `updated_at` - 更新时间

---

## 如何查询这些信息

### 通过 API 查询
```bash
# 查询所有资产（包含所有字段）
curl -s "http://127.0.0.1:8000/api/v1/assets/"

# 查询特定资产
curl -s "http://127.0.0.1:8000/api/v1/assets/{ASSET_ID}"

# 按类型筛选
curl -s "http://127.0.0.1:8000/api/v1/assets/?type=Server"

# 按重要性筛选
curl -s "http://127.0.0.1:8000/api/v1/assets/?importance=critical"

# 获取统计信息
curl -s "http://127.0.0.1:8000/api/v1/assets/statistics/summary"
```

### 直接查询数据库
```bash
cd E:\knowlegdge_base\claude\.claude\teams\ai-security-team\asset-database
python -c "import sqlite3; conn = sqlite3.connect('./data/asset.db'); cursor = conn.cursor(); cursor.execute('SELECT asset_id, name, type, ip_address, importance, environment, status FROM assets'); rows = cursor.fetchall(); [print(row) for row in rows]"
```

---

## 使用建议

1. **定期更新资产信息** - 记录 first_seen/last_seen 时间跟踪资产状态变化
2. **安全字段优先** - cvss_score 和 vulnerability_count 应该定期从漏洞扫描结果更新
3. **扩展字段使用** - config/services/relationships/meta_data 可以存储任意 JSON 格式的扩展信息
4. **状态管理** - 使用 asset_status 字段标记资产生命周期状态
   - `active` - 正常使用中
   - `standby` - 备用状态
   - `retired` - 已退役
   - `disposed` - 已处置
   - `compromised` - 已被入侵
   - `under_investigation` - 调查中
   - `quarantined` - 已隔离
5. **物理位置完整** - site/building/floor/room/rack/rack_unit 构成完整的位置层级

---

**数据库文件位置**: `E:\knowlegdge_base\claude\.claude\teams\ai-security-team\asset-database\data\asset.db`

**API 文档**: http://127.0.0.1:8000/docs
