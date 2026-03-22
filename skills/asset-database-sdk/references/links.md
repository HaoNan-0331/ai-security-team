# 资产库原始文档链接

本文档列出了资产库的原始文档路径，供深入参考使用。

---

## 核心文档

| 文档 | 路径 | 说明 |
|------|------|------|
| README.md | `teams/ai-security-team/asset-database/README.md` | 项目说明和快速参考 |
| USER_GUIDE.md | `teams/ai-security-team/asset-database/USER_GUIDE.md` | 完整使用手册 |
| DATA_MODEL.md | `teams/ai-security-team/asset-database/DATA_MODEL.md` | 数据模型和API文档 |
| ASSET_DATABASE_FIELDS.md | `teams/ai-security-team/asset-database/ASSET_DATABASE_FIELDS.md` | 字段详细说明 |
| CHANGELOG.md | `teams/ai-security-team/asset-database/CHANGELOG.md` | 版本变更记录 |

---

## SDK文件

| 文件 | 路径 | 说明 |
|------|------|------|
| asset_sdk.py | `teams/ai-security-team/asset-database/asset_sdk.py` | Python SDK主文件 |
| database.py | `teams/ai-security-team/asset-database/database.py` | 数据库配置 |
| models/asset.py | `teams/ai-security-team/asset-database/models/asset.py` | 数据模型 |

---

## 工具脚本

| 文件 | 路径 | 说明 |
|------|------|------|
| scripts/migrate.py | `teams/ai-security-team/asset-database/scripts/migrate.py` | 数据库迁移 |
| scripts/discover.py | `teams/ai-security-team/asset-database/scripts/discover.py` | 网络发现 |
| scripts/init_db.py | `teams/ai-security-team/asset-database/scripts/init_db.py` | 数据库初始化 |
| scripts/export_inventory.py | `teams/ai-security-team/asset-database/scripts/export_inventory.py` | 资产导出 |

---

## 数据文件

| 文件 | 路径 | 说明 |
|------|------|------|
| assets.db | `teams/ai-security-team/asset-database/data/assets.db` | SQLite数据库 |
| .secret_key | `teams/ai-security-team/asset-database/data/.secret_key` | 加密密钥 |

---

## 相关Agent

| Agent | 路径 | 说明 |
|-------|------|------|
| asset-mgmt | `teams/ai-security-team/agents/monitoring/asset-mgmt/prompt.md` | 资产管理Agent |

---

*版本: v4.0*
*更新日期: 2026-02-26*
