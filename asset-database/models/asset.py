"""
资产数据模型定义
"""
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

Base = declarative_base()


class AssetType(enum.Enum):
    """资产类型枚举"""
    NETWORK_DEVICE = "NetworkDevice"      # 网络设备（交换机、路由器）
    SECURITY_DEVICE = "SecurityDevice"    # 安全设备（防火墙、IDS/IPS）
    SERVER = "Server"                     # 服务器
    TERMINAL = "Terminal"                 # 终端（PC、笔记本）
    DATABASE = "Database"                 # 数据库
    APPLICATION = "Application"           # 应用系统
    OTHER = "Other"                       # 其他


class AssetStatus(enum.Enum):
    """资产状态枚举"""
    ACTIVE = "active"           # 在用
    STANDBY = "standby"         # 备用
    MAINTENANCE = "maintenance" # 维护中
    RETIRED = "retired"         # 已退役
    COMPROMISED = "compromised" # 已失陷
    INVESTIGATING = "investigating"  # 调查中
    ISOLATED = "isolated"            # 已隔离
    REMEDIATED = "remediated"        # 已修复
    UNKNOWN = "unknown"         # 状态未知


class AssetImportance(enum.Enum):
    """资产重要性枚举"""
    CRITICAL = "critical"  # 关键资产
    HIGH = "high"          # 重要资产
    MEDIUM = "medium"      # 一般资产
    LOW = "low"            # 非重要资产


class AssetEnvironment(enum.Enum):
    """资产环境枚举"""
    PRODUCTION = "production"      # 生产环境
    DEVELOPMENT = "development"    # 开发环境
    TEST = "test"                  # 测试环境
    STAGING = "staging"            # 预发布环境
    DMZ = "dmz"                    # DMZ区域


# 资产关系多对多关联表
asset_relationships = Table(
    'asset_relationships',
    Base.metadata,
    Column('id', String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column('source_id', String(36), ForeignKey('assets.asset_id'), nullable=False),
    Column('target_id', String(36), ForeignKey('assets.asset_id'), nullable=False),
    Column('relation_type', String(50), nullable=False),  # depends_on, connects_to, hosts, etc.
    Column('description', Text),
    Column('created_at', DateTime, default=datetime.now),
    Column('created_by', String(100))
)


class Asset(Base):
    """资产主表"""
    __tablename__ = 'assets'

    asset_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, comment='资产名称')
    asset_type = Column(String(50), nullable=False, comment='资产类型')
    ip_address = Column(String(50), comment='IP地址')
    mac_address = Column(String(50), comment='MAC地址')
    port = Column(Integer, comment='端口号')
    username = Column(String(100), comment='登录用户名')
    password_encrypted = Column(Text, comment='加密后的密码')
    status = Column(String(20), default='active', comment='资产状态')
    importance = Column(String(20), default='medium', comment='资产重要性')
    environment = Column(String(20), default='production', comment='资产环境')
    owner = Column(String(100), comment='负责人')
    department = Column(String(100), comment='所属部门')
    location = Column(String(200), comment='物理位置')
    vendor = Column(String(100), comment='厂商')
    model = Column(String(100), comment='型号')
    os_type = Column(String(100), comment='操作系统类型')
    os_version = Column(String(100), comment='操作系统版本')
    firmware_version = Column(String(100), comment='固件版本')
    serial_number = Column(String(100), comment='序列号')
    description = Column(Text, comment='描述')
    tags = Column(String(500), comment='标签（逗号分隔）')
    custom_fields = Column(Text, comment='自定义字段（JSON格式）')

    # 补丁管理
    last_patch_date = Column(DateTime, comment='最后补丁日期')
    patch_status = Column(String(50), default='unknown', comment='补丁状态')
    vulnerability_count = Column(Integer, default=0, comment='漏洞数量')

    # P0 高优先级字段 - SSH连接信息
    ssh_port = Column(Integer, comment='SSH端口')
    hostname = Column(String(200), comment='主机名')
    management_ip = Column(String(50), comment='管理IP地址')

    # P0 高优先级字段 - 服务和端口
    services = Column(Text, comment='运行的服务（JSON格式）')
    open_ports = Column(Text, comment='开放端口列表（JSON格式）')

    # P0 高优先级字段 - 安全相关
    risk_score = Column(Integer, default=0, comment='风险评分（0-100）')
    isolation_status = Column(String(20), default='normal', comment='隔离状态（normal/network/host）')

    # P0 高优先级字段 - 网络分类
    device_role = Column(String(50), comment='设备角色（core/distribution/access/edge）')
    vlan_ids = Column(Text, comment='VLAN ID列表（JSON格式）')
    network_segment = Column(String(50), comment='网段标识')

    # P1 中优先级字段 - 硬件配置
    cpu_cores = Column(Integer, comment='CPU核心数')
    memory_gb = Column(Integer, comment='内存大小(GB)')
    disk_gb = Column(Integer, comment='磁盘大小(GB)')

    # P1 中优先级字段 - 合规与扫描
    last_scan_date = Column(DateTime, comment='最后扫描日期')
    compliance_status = Column(String(20), default='unknown', comment='合规状态')
    fqdn = Column(String(255), comment='完全限定域名')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    last_seen_at = Column(DateTime, comment='最后发现时间')

    # 关系
    change_logs = relationship("AssetChangeLog", back_populates="asset", cascade="all, delete-orphan")

    def to_dict(self, include_password=False):
        """转换为字典"""
        result = {
            'asset_id': self.asset_id,
            'name': self.name,
            'asset_type': self.asset_type,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'port': self.port,
            'username': self.username,
            'status': self.status,
            'importance': self.importance,
            'environment': self.environment,
            'owner': self.owner,
            'department': self.department,
            'location': self.location,
            'vendor': self.vendor,
            'model': self.model,
            'os_type': self.os_type,
            'os_version': self.os_version,
            'firmware_version': self.firmware_version,
            'serial_number': self.serial_number,
            'description': self.description,
            'tags': self.tags.split(',') if self.tags and self.tags.strip() else [],
            'last_patch_date': self.last_patch_date.isoformat() if self.last_patch_date else None,
            'patch_status': self.patch_status,
            'vulnerability_count': self.vulnerability_count,
            # P0 高优先级字段
            'ssh_port': self.ssh_port,
            'hostname': self.hostname,
            'management_ip': self.management_ip,
            'services': json.loads(self.services) if self.services else [],
            'open_ports': json.loads(self.open_ports) if self.open_ports else [],
            'risk_score': self.risk_score,
            'isolation_status': self.isolation_status,
            'device_role': self.device_role,
            'vlan_ids': json.loads(self.vlan_ids) if self.vlan_ids else [],
            'network_segment': self.network_segment,
            # P1 中优先级字段
            'cpu_cores': self.cpu_cores,
            'memory_gb': self.memory_gb,
            'disk_gb': self.disk_gb,
            'last_scan_date': self.last_scan_date.isoformat() if self.last_scan_date else None,
            'compliance_status': self.compliance_status,
            'fqdn': self.fqdn,
            # 时间戳
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
        }
        if include_password:
            result['password_encrypted'] = self.password_encrypted
        return result


class AssetChangeLog(Base):
    """资产变更日志"""
    __tablename__ = 'asset_change_logs'

    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey('assets.asset_id'), nullable=False)
    change_type = Column(String(50), nullable=False, comment='变更类型：create/update/delete/password')
    field_name = Column(String(100), comment='变更字段')
    old_value = Column(Text, comment='旧值')
    new_value = Column(Text, comment='新值')
    changed_by = Column(String(100), comment='变更人')
    change_reason = Column(Text, comment='变更原因')
    created_at = Column(DateTime, default=datetime.now, comment='变更时间')

    # 关系
    asset = relationship("Asset", back_populates="change_logs")

    def to_dict(self):
        """转换为字典"""
        return {
            'log_id': self.log_id,
            'asset_id': self.asset_id,
            'change_type': self.change_type,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': self.changed_by,
            'change_reason': self.change_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
