-- =====================================================
-- AI Security Team - Asset Database
-- Migration: 001 - 初始数据库结构
-- Version: 1.0.0
-- =====================================================

-- 版本控制表
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入当前版本
INSERT INTO schema_migrations (version, name, description)
VALUES (1, 'initial_schema', '初始数据库结构，包含资产主表、关系表、变更表和标签表');

-- =====================================================
-- 1. 资产主表 (assets)
-- =====================================================

CREATE TABLE IF NOT EXISTS assets (
    -- 主键
    asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 基本信息
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,

    -- 网络信息
    ip_address INET,
    mac_address MACADDR,
    hostname VARCHAR(255),
    fqdn VARCHAR(255),
    subnet VARCHAR(50),
    vlan INTEGER,
    gateway INET,
    dns_servers TEXT[],

    -- 位置信息
    site VARCHAR(100),
    building VARCHAR(100),
    floor VARCHAR(50),
    room VARCHAR(100),
    rack VARCHAR(50),
    rack_unit VARCHAR(20),

    -- 分类标签
    importance VARCHAR(20) NOT NULL CHECK (importance IN ('critical', 'high', 'medium', 'low')),
    environment VARCHAR(20) NOT NULL CHECK (environment IN ('production', 'staging', 'development', 'dr')),
    business_unit VARCHAR(100),
    owner VARCHAR(255),
    cost_center VARCHAR(100),

    -- 状态信息
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'standby', 'retired', 'disposed')),
    lifecycle_stage VARCHAR(50),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),

    -- 安全信息
    cvss_score DECIMAL(3,1) CHECK (cvss_score BETWEEN 0 AND 10),
    vulnerability_count INTEGER DEFAULT 0,
    compliance_level VARCHAR(20),
    patch_level VARCHAR(50),

    -- 配置信息 (JSON)
    config JSONB DEFAULT '{}'::jsonb,
    services JSONB DEFAULT '[]'::jsonb,
    relationships JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- 审计字段
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 约束
    CONSTRAINT check_ip_not_null CHECK (
        ip_address IS NOT NULL OR config->>'ip_addresses' IS NOT NULL
    ),
    CONSTRAINT check_status_not_disposed CHECK (
        status IN ('retired', 'disposed') OR (status IN ('active', 'standby'))
    )
);

COMMENT ON TABLE assets IS '资产主表 - 存储所有资产的完整信息';

-- =====================================================
-- 2. 资产关系表 (asset_relationships)
-- =====================================================

CREATE TABLE IF NOT EXISTS asset_relationships (
    id SERIAL PRIMARY KEY,
    source_asset UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    target_asset UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    attributes JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_asset, target_asset, relationship_type)
);

COMMENT ON TABLE asset_relationships IS '资产关系表 - 存储资产间的依赖、连接等关系';

-- =====================================================
-- 3. 资产变更历史表 (asset_changes)
-- =====================================================

CREATE TABLE IF NOT EXISTS asset_changes (
    id SERIAL PRIMARY KEY,
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by VARCHAR(255),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    reason TEXT,
    source VARCHAR(100)
);

COMMENT ON TABLE asset_changes IS '资产变更历史表 - 记录所有资产变更的历史记录';

-- =====================================================
-- 4. 资产标签表 (asset_tags)
-- =====================================================

CREATE TABLE IF NOT EXISTS asset_tags (
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    tag_key VARCHAR(100) NOT NULL,
    tag_value VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (asset_id, tag_key)
);

COMMENT ON TABLE asset_tags IS '资产标签表 - 存储资产的键值对标签';

-- =====================================================
-- 5. 创建视图
-- =====================================================

-- 资产总览视图
CREATE OR REPLACE VIEW asset_summary AS
SELECT
    type,
    status,
    importance,
    environment,
    COUNT(*) as count
FROM assets
WHERE status != 'disposed'
GROUP BY type, status, importance, environment;

COMMENT ON VIEW asset_summary IS '资产总览视图 - 按类型、状态、重要性、环境统计资产数量';

-- 高危资产视图
CREATE OR REPLACE VIEW high_risk_assets AS
SELECT *
FROM assets
WHERE (cvss_score >= 7.0 OR vulnerability_count > 10 OR importance = 'critical')
  AND status IN ('active', 'standby');

COMMENT ON VIEW high_risk_assets IS '高危资产视图 - 显示高风险的资产';

-- 活跃资产视图
CREATE OR REPLACE VIEW active_assets AS
SELECT *
FROM assets
WHERE status = 'active'
  AND last_seen > NOW() - INTERVAL '30 days';

COMMENT ON VIEW active_assets IS '活跃资产视图 - 显示最近30天活跃的资产';

-- =====================================================
-- 6. 插入示例数据
-- =====================================================

INSERT INTO assets (name, type, manufacturer, model, ip_address, hostname,
                     importance, environment, business_unit, owner, site, status)
VALUES
    ('Core-Firewall-01', 'Security', 'Huawei', 'USG6000E', '192.168.1.1',
     'fw-core', 'critical', 'production', 'security-team', 'admin@example.com', 'DataCenter-A', 'active'),

    ('Web-Server-01', 'Server', 'Dell', 'PowerEdge R740', '192.168.1.100',
     'web-01', 'high', 'production', 'web-team', 'web-admin@example.com', 'DataCenter-A', 'active'),

    ('DB-Primary', 'Database', 'Oracle', 'Exadata X8M', '192.168.2.10',
     'db-primary', 'critical', 'production', 'database-team', 'dba@example.com', 'DataCenter-B', 'active'),

    ('Access-Switch-01', 'Network', 'Ruijie', 'RG-S5750-28GT4S', '192.168.1.254',
     'sw-access', 'medium', 'production', 'network-team', 'net-admin@example.com', 'Office-Floor2', 'active');

-- 插入示例关系
INSERT INTO asset_relationships (source_asset, target_asset, relationship_type)
SELECT a.asset_id, b.asset_id, 'DEPENDS_ON'
FROM assets a
CROSS JOIN assets b
WHERE a.name = 'Web-Server-01' AND b.name = 'DB-Primary';

INSERT INTO asset_relationships (source_asset, target_asset, relationship_type)
SELECT a.asset_id, b.asset_id, 'CONNECTED_TO'
FROM assets a
CROSS JOIN assets b
WHERE a.name = 'Web-Server-01' AND b.name = 'Access-Switch-01';

-- =====================================================
-- 7. 完成标记
-- =====================================================

-- 记录迁移完成
INSERT INTO schema_migrations (version, name, description)
VALUES (1, '001_initial_schema_applied', '迁移 001 已应用');

-- 显示完成信息
DO $$
    RAISE NOTICE 'Migration 001 completed: Initial schema created successfully';
    RAISE NOTICE 'Tables created: assets, asset_relationships, asset_changes, asset_tags';
    RAISE NOTICE 'Views created: asset_summary, high_risk_assets, active_assets';
    RAISE NOTICE 'Sample data inserted: 5 assets, 2 relationships';
END $$;
