# 资产库SDK使用技能

> AI Security Team资产库SDK使用技能 | 版本: v4.0

---

## 技能概述

本技能提供AI Security Team资产库的完整SDK访问能力，适用于以下场景：

- **资产管理 (asset-mgmt)**: 批量导入、统计分析、导出报告
- **服务器运维 (server-ops)**: 获取服务器凭据、执行维护、健康检查
- **网络运维 (network-ops)**: 管理网络设备、拓扑查询、VLAN管理
- **威胁响应 (threat-response)**: 隔离资产、风险分析、生成报告
- **漏洞评估 (vuln-assessment)**: 扫描目标管理、漏洞信息更新、风险评估

---

## 快速开始

### 3行代码上手

```python
import sys
sys.path.insert(0, 'teams/ai-security-team/asset-database')
from asset_sdk import AssetClient

client = AssetClient()
```

### 基本操作

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
servers = client.list_assets(asset_type="Server", environment="production")

# 获取密码
password = client.get_password(asset['asset_id'])
```

---

## 目录结构

```
asset-database-sdk/
├── SKILL.md                      # 技能定义（核心文档）
├── README.md                     # 本文件
├── scripts/                      # 辅助脚本
│   ├── asset_query.py            # 交互式资产查询
│   ├── asset_backup.py           # 资产库备份工具
│   └── health_check.py           # 批量健康检查
├── references/                   # 参考文档
│   └── links.md                  # 原始文档链接
├── experiences/                  # 经验库
│   ├── errors.json               # 常见错误及解决方案
│   ├── solutions.json            # 最佳实践解决方案
│   └── pitfalls.md               # 常见陷阱和注意事项
└── examples/                     # 使用示例
    ├── agent_examples.py         # Agent使用示例代码
    └── batch_import_example.json # 批量导入示例数据
```

---

## 辅助脚本

### asset_query.py - 交互式资产查询

```bash
# 按类型查询
python asset_query.py --type Server --env production

# 按IP查询
python asset_query.py --ip 192.168.1.100

# 关键字搜索
python asset_query.py --search web

# 按风险分数查询
python asset_query.py --risk --min 60

# 导出数据
python asset_query.py --export assets.json
```

### asset_backup.py - 资产库备份工具

```bash
# 备份到默认目录
python asset_backup.py

# 备份到指定目录并压缩
python asset_backup.py --output /backup/assets/ --compress

# 保留最近30天备份
python asset_backup.py --keep 30

# 列出备份文件
python asset_backup.py --list

# 恢复备份
python asset_backup.py --restore assets_backup_20260226.db
```

### health_check.py - 批量健康检查

```bash
# 检查所有服务器
python health_check.py --type Server

# 检查指定资产
python health_check.py --assets id1,id2,id3

# 检查端口
python health_check.py --type Server --check-type port

# 导出报告
python health_check.py --type Server --output report.json
```

---

## 经验库

### errors.json - 常见错误

包含常见错误代码及其解决方案：
- 数据库锁定错误
- 密码解密失败
- 资产不存在
- IP地址重复
- 无效的资产类型/状态
- 批量操作部分失败

### solutions.json - 解决方案库

包含最佳实践解决方案：
- 批量导入最佳实践
- 风险报告自动化
- 资产隔离应急响应
- SSH连接凭据获取
- 资产变更追溯
- 数据库备份策略

### pitfalls.md - 常见陷阱

包含使用时的常见陷阱和注意事项：
- 不要在日志中打印密码
- 批量操作前先试运行
- 处理None返回值
- 避免硬编码资产ID
- JSON字段格式要求

---

## 示例代码

### agent_examples.py - Agent使用示例

按Agent类型分类的示例代码：

```python
# server-ops: 获取服务器SSH凭据
credentials = server_ops_get_credentials(asset_id)

# network-ops: 按设备角色查询
devices = network_ops_list_devices_by_role("core")

# threat-response: 隔离资产
threat_response_isolate_asset(asset_id, "检测到恶意软件")

# asset-mgmt: 批量导入
result = asset_mgmt_batch_import(assets)

# vuln-assessment: 更新漏洞信息
result = vuln_assessment_update_vulnerability_info(asset_id, 5, "high")
```

### batch_import_example.json - 批量导入示例

包含完整的示例资产数据，可直接用于批量导入测试。

---

## 完整文档

详见 [SKILL.md](./SKILL.md)，包含：

- 完整API速查表
- Agent使用场景详解
- 枚举值参考
- 常见问题解答
- 原始文档链接

---

## 原始文档

资产库原始文档位于 `teams/ai-security-team/asset-database/`：

- `README.md` - 项目说明
- `USER_GUIDE.md` - 使用手册
- `DATA_MODEL.md` - 数据模型和完整API文档
- `ASSET_DATABASE_FIELDS.md` - 字段详细说明

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.0 | 2026-02-26 | 初始版本 |

---

*负责人: asset-mgmt*
*更新日期: 2026-02-26*
