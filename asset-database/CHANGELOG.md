# 修改记录

## 2026-02-26

### 删除
- `api/` 目录 - 移除API server相关代码，改为纯SDK方案
- `QUICKSTART.md` - 移除API相关快速开始文档
- `supervisor/` 目录 - 移除空的监控器目录

### 修改
- `models/asset.py:65` - 修复 datetime.utcnow() 弃用问题，改为 datetime.now()
- `models/asset.py:132,133` - 修复 datetime.utcnow() 弃用问题，改为 datetime.now()
- `models/asset.py:206` - 修复 datetime.utcnow() 弃用问题，改为 datetime.now()
- `models/asset.py:226-252` - 删除 AssetRelationship 类（使用 Table 对象代替）
- `models/__init__.py:4,6` - 更新导出，移除 AssetRelationship
- `asset_sdk.py` - 批量替换 datetime.utcnow() 为 datetime.now()
- `asset_sdk.py:1450-1470` - 删除测试代码
- `README.md:7-15` - 更新 v4.0 说明，移除 CLI 相关描述
- `README.md:70-98` - 更新目录结构，添加 scripts/migrations/schema 等目录
- `README.md:144` - 添加 remove_relationship() 方法说明
- `DATA_MODEL.md:17` - 更正字段数量（49->45）
- `DATA_MODEL.md:316-319` - 更新版本历史，移除 v3.0 描述

### 新增
- `CHANGELOG.md` - 本修改记录文件
- `USER_GUIDE.md` - SDK使用手册

### 测试
- 完成SDK全功能测试（12个测试项，100%通过率）

---

## 2026-02-17

### 新增
- v4.0 版本发布
- P0高优先级字段（SSH连接、服务端口、风险评分、隔离状态、网络分类）
- P1中优先级字段（硬件配置、合规扫描）
- 健康检查功能（health_check）
- 审计日志查询（get_audit_logs）
- 风险报告生成（get_risk_report）
- 按风险/隔离状态/网段查询

---

## 2026-02-15

### 新增
- 批量操作功能
- 统计分析功能

---

## 2026-02-10

### 新增
- v1.0 初始版本
