-- =====================================================
-- AI Security Team - Asset Database
-- PostgreSQL Schema Definition
-- Version: 1.0
-- =====================================================

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

    -- 约束
    CONSTRAINT check_ip_not_null CHECK (
        ip_address IS NOT NULL
        OR config->>'ip_addresses' IS NOT NULL
        OR status IN ('retired', 'disposed')
    ),
    CONSTRAINT check_mac_optional CHECK (
        type IN ('Server', 'Network', 'Database', 'Application')
        OR mac_address IS NULL
    )
);

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

-- =====================================================
-- 索引创建
-- =====================================================

-- 资产表索引
CREATE INDEX IF NOT EXISTS idx_assets_ip ON assets(ip_address) WHERE ip_address IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_assets_mac ON assets(mac_address) WHERE mac_address IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_assets_hostname ON assets(hostname) WHERE hostname IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);
CREATE INDEX IF NOT EXISTS idx_assets_importance ON assets(importance);
CREATE INDEX IF NOT EXISTS idx_assets_environment ON assets(environment);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_assets_site ON assets(site);
CREATE INDEX IF NOT EXISTS idx_assets_last_seen ON assets(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_assets_config ON assets USING GIN(config);
CREATE INDEX IF NOT EXISTS idx_assets_metadata ON assets USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_assets_services ON assets USING GIN(services);

-- 全文搜索索引 (PostgreSQL 11+)
CREATE INDEX IF NOT EXISTS idx_assets_fulltext ON assets
    USING GIN(to_tsvector('simple', name || ' ' || COALESCE(hostname, '')));

-- 关系表索引
CREATE INDEX IF NOT EXISTS idx_rel_source ON asset_relationships(source_asset);
CREATE INDEX IF NOT EXISTS idx_rel_target ON asset_relationships(target_asset);
CREATE INDEX IF NOT EXISTS idx_rel_type ON asset_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_rel_created ON asset_relationships(created_at DESC);

-- 变更历史索引
CREATE INDEX IF NOT EXISTS idx_changes_asset ON asset_changes(asset_id);
CREATE INDEX IF NOT EXISTS idx_changes_time ON asset_changes(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_changes_type ON asset_changes(change_type);

-- 标签索引
CREATE INDEX IF NOT EXISTS idx_tags_key ON asset_tags(tag_key);
CREATE INDEX IF NOT EXISTS idx_tags_value ON asset_tags(tag_value);
CREATE INDEX IF NOT EXISTS idx_tags_asset ON asset_tags(asset_id);

-- =====================================================
-- 视图定义
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
GROUP BY type, status, importance, environment;

-- 高危资产视图
CREATE OR REPLACE VIEW high_risk_assets AS
SELECT *
FROM assets
WHERE cvss_score >= 7.0
   OR vulnerability_count > 10
   OR importance = 'critical'
ORDER BY cvss_score DESC, vulnerability_count DESC;

-- 活跃资产视图
CREATE OR REPLACE VIEW active_assets AS
SELECT *
FROM assets
WHERE status = 'active'
   AND last_seen > NOW() - INTERVAL '30 days';

-- =====================================================
-- 触发器定义
-- =====================================================

-- 自动更新 last_updated 时间戳
CREATE OR REPLACE FUNCTION update_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_last_updated
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_last_updated();

-- 记录资产变更
CREATE OR REPLACE FUNCTION log_asset_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO asset_changes (asset_id, change_type, new_value, changed_by)
        VALUES (NEW.asset_id, 'created', row_to_json(NEW), NEW.created_by);

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO asset_changes (asset_id, change_type, old_value, new_value, changed_by)
        VALUES (NEW.asset_id, 'updated', row_to_json(OLD), row_to_json(NEW), NEW.updated_by);

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO asset_changes (asset_id, change_type, old_value, changed_by)
        VALUES (OLD.asset_id, 'deleted', row_to_json(OLD), session_user);

    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_asset_changes
    AFTER INSERT OR UPDATE OR DELETE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION log_asset_changes();

-- =====================================================
-- 初始数据
-- =====================================================

-- 插入示例资产（仅用于测试）
-- INSERT INTO assets (name, type, ip_address, hostname, importance, environment, owner)
-- VALUES
--     ('Core-Firewall-01', 'Security', '192.168.1.1', 'fw-core', 'critical', 'production', 'security-team'),
--     ('Web-Server-01', 'Server', '192.168.1.100', 'web-01', 'high', 'production', 'web-team'),
--     ('DB-Primary', 'Database', '192.168.2.10', 'db-primary', 'critical', 'production', 'dba-team');

-- =====================================================
-- 注释
-- =====================================================

COMMENT ON TABLE assets IS '资产主表 - 存储所有资产信息';
COMMENT ON TABLE asset_relationships IS '资产关系表 - 存储资产间的关系';
COMMENT ON TABLE asset_changes IS '资产变更历史表 - 记录所有资产变更';
COMMENT ON TABLE asset_tags IS '资产标签表 - 存储资产的键值对标签';

COMMENT ON COLUMN assets.config IS '资产配置信息 (JSON格式)';
COMMENT ON COLUMN assets.services IS '资产服务列表 (JSON数组)';
COMMENT ON COLUMN assets.relationships IS '资产关系信息 (JSON格式)';
COMMENT ON COLUMN assets.metadata IS '其他元数据 (JSON格式)';
