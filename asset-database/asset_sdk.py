"""
资产数据库SDK - AI安全团队版
支持并发访问、批量操作和多维度过滤
"""
import os
import time
import ipaddress
import json
from functools import wraps
from typing import List, Dict, Optional, Any, Union
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import func, or_
from sqlalchemy.exc import OperationalError

from database import get_engine, get_db_session, init_database, SessionLocal
from sqlalchemy.orm import sessionmaker
from models import Asset, AssetChangeLog, asset_relationships, Base
from utils import encrypt_password, decrypt_password, DatabaseLock


def retry_on_lock(max_retries: int = 15, delay: float = 0.2):
    """
    数据库锁重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 基础延迟时间（秒），实际延迟会随重试次数增加

    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_error = e
                    error_msg = str(e).lower()
                    if 'locked' in error_msg or 'database is locked' in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = delay * (attempt + 1) * (1 + 0.1 * attempt)
                            time.sleep(wait_time)
                            continue
                    raise
            raise last_error
        return wrapper
    return decorator


class AssetClient:
    """
    资产数据库客户端

    提供资产的增删改查、批量操作、统计分析和变更历史等功能
    """

    def __init__(self, db_path: str = None, auto_init: bool = True):
        """
        初始化客户端

        Args:
            db_path: 数据库文件路径（仅SQLite），不提供则使用默认路径
            auto_init: 是否自动初始化数据库表
        """
        self.db_path = db_path
        if db_path:
            # 直接创建新引擎，而不是修改全局环境变量
            from database import create_db_engine
            self.engine = create_db_engine(f'sqlite:///{db_path}')
            # 创建专用的SessionLocal
            self._session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        else:
            self.engine = get_engine()
            # 使用全局SessionLocal
            self._session_local = SessionLocal

        if auto_init:
            init_database(self.engine)

    @contextmanager
    def _get_session(self):
        """获取数据库会话"""
        session = self._session_local()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _get_db_path(self) -> str:
        """获取数据库文件路径"""
        if self.db_path:
            return self.db_path
        # 从引擎URL中提取路径
        url = str(self.engine.url)
        if url.startswith('sqlite:///'):
            return url[10:]  # 移除 sqlite:/// 前缀
        return None

    # ==================== 基础CRUD操作 ====================

    @retry_on_lock(max_retries=15)
    def create_asset(
        self,
        name: str,
        username: str = None,
        password: str = None,
        asset_type: str = "Server",
        ip_address: str = None,
        mac_address: str = None,
        port: int = None,
        status: str = "active",
        importance: str = "medium",
        environment: str = "production",
        owner: str = None,
        department: str = None,
        location: str = None,
        vendor: str = None,
        model: str = None,
        os_type: str = None,
        os_version: str = None,
        firmware_version: str = None,
        serial_number: str = None,
        description: str = None,
        tags: List[str] = None,
        custom_fields: Dict = None,
        # P0 高优先级字段
        ssh_port: int = None,
        hostname: str = None,
        management_ip: str = None,
        services: List[str] = None,
        open_ports: List[int] = None,
        risk_score: int = 0,
        isolation_status: str = "normal",
        device_role: str = None,
        vlan_ids: List[int] = None,
        network_segment: str = None,
        # P1 中优先级字段
        cpu_cores: int = None,
        memory_gb: int = None,
        disk_gb: int = None,
        last_scan_date: datetime = None,
        compliance_status: str = "unknown",
        fqdn: str = None,
        changed_by: str = "system",
        **kwargs
    ) -> Dict:
        """
        创建资产

        Args:
            name: 资产名称（必填）
            username: 登录用户名
            password: 登录密码（会自动加密存储）
            asset_type: 资产类型
            ip_address: IP地址
            ssh_port: SSH端口
            hostname: 主机名
            management_ip: 管理IP地址
            services: 运行的服务列表
            open_ports: 开放端口列表
            risk_score: 风险评分（0-100）
            isolation_status: 隔离状态（normal/network/host）
            device_role: 设备角色
            vlan_ids: VLAN ID列表
            network_segment: 网段标识
            cpu_cores: CPU核心数
            memory_gb: 内存大小(GB)
            disk_gb: 磁盘大小(GB)
            last_scan_date: 最后扫描日期
            compliance_status: 合规状态
            fqdn: 完全限定域名
            ... 其他字段

        Returns:
            创建的资产信息
        """
        db_path = self._get_db_path()

        def _do_create():
            with self._get_session() as session:
                # 处理密码加密
                password_encrypted = None
                if password:
                    password_encrypted = encrypt_password(password)

                # 处理标签
                tags_str = ','.join(tags) if tags else None

                # 处理自定义字段
                custom_fields_str = json.dumps(custom_fields) if custom_fields else None

                # 处理JSON字段
                services_str = json.dumps(services) if services else None
                open_ports_str = json.dumps(open_ports) if open_ports else None
                vlan_ids_str = json.dumps(vlan_ids) if vlan_ids else None

                # 创建资产
                asset = Asset(
                    name=name,
                    username=username,
                    password_encrypted=password_encrypted,
                    asset_type=asset_type,
                    ip_address=ip_address,
                    mac_address=mac_address,
                    port=port,
                    status=status,
                    importance=importance,
                    environment=environment,
                    owner=owner,
                    department=department,
                    location=location,
                    vendor=vendor,
                    model=model,
                    os_type=os_type,
                    os_version=os_version,
                    firmware_version=firmware_version,
                    serial_number=serial_number,
                    description=description,
                    tags=tags_str,
                    custom_fields=custom_fields_str,
                    # P0 高优先级字段
                    ssh_port=ssh_port,
                    hostname=hostname,
                    management_ip=management_ip,
                    services=services_str,
                    open_ports=open_ports_str,
                    risk_score=risk_score,
                    isolation_status=isolation_status,
                    device_role=device_role,
                    vlan_ids=vlan_ids_str,
                    network_segment=network_segment,
                    # P1 中优先级字段
                    cpu_cores=cpu_cores,
                    memory_gb=memory_gb,
                    disk_gb=disk_gb,
                    last_scan_date=last_scan_date,
                    compliance_status=compliance_status,
                    fqdn=fqdn,
                )

                # 处理额外字段
                for key, value in kwargs.items():
                    if hasattr(asset, key):
                        setattr(asset, key, value)

                session.add(asset)
                session.flush()

                # 记录变更日志
                self._record_change(
                    session, asset.asset_id, 'create', None, None, None,
                    changed_by=changed_by, change_reason='资产创建'
                )

                return asset.to_dict()

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path:
            with DatabaseLock(db_path):
                return _do_create()
        else:
            return _do_create()

    @retry_on_lock(max_retries=5)
    def get_asset(self, asset_id: str) -> Optional[Dict]:
        """
        获取资产详情

        Args:
            asset_id: 资产ID

        Returns:
            资产信息字典，不存在返回None
        """
        with self._get_session() as session:
            asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
            if asset:
                return asset.to_dict()
            return None

    @retry_on_lock(max_retries=15)
    def update_asset(
        self,
        asset_id: str,
        changed_by: str = "system",
        change_reason: str = None,
        **kwargs
    ) -> Optional[Dict]:
        """
        更新资产信息

        Args:
            asset_id: 资产ID
            changed_by: 变更人
            change_reason: 变更原因
            **kwargs: 要更新的字段

        Returns:
            更新后的资产信息
        """
        db_path = self._get_db_path()

        def _do_update():
            with self._get_session() as session:
                asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
                if not asset:
                    return None

                # 记录变更
                for key, new_value in kwargs.items():
                    if hasattr(asset, key):
                        old_value = getattr(asset, key)

                        # 特殊处理密码
                        if key == 'password' and new_value:
                            new_value = encrypt_password(new_value)
                            key = 'password_encrypted'
                            old_value = '******'  # 日志中不记录原密码

                        # 特殊处理标签
                        if key == 'tags' and isinstance(new_value, list):
                            new_value = ','.join(new_value)
                            old_value = getattr(asset, 'tags')

                        # 特殊处理自定义字段
                        if key == 'custom_fields' and isinstance(new_value, dict):
                            new_value = json.dumps(new_value)

                        # 特殊处理JSON字段（services, open_ports, vlan_ids）
                        if key in ('services', 'open_ports', 'vlan_ids') and isinstance(new_value, list):
                            new_value = json.dumps(new_value)
                            old_value = getattr(asset, key)

                        if old_value != new_value:
                            setattr(asset, key, new_value)
                            self._record_change(
                                session, asset_id, 'update', key,
                                str(old_value), str(new_value),
                                changed_by=changed_by, change_reason=change_reason
                            )

                asset.updated_at = datetime.now()
                return asset.to_dict()

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path:
            with DatabaseLock(db_path):
                return _do_update()
        else:
            return _do_update()

    @retry_on_lock(max_retries=15)
    def delete_asset(
        self,
        asset_id: str,
        hard_delete: bool = False,
        changed_by: str = "system",
        change_reason: str = None
    ) -> bool:
        """
        删除资产

        Args:
            asset_id: 资产ID
            hard_delete: 是否硬删除（物理删除）
            changed_by: 变更人
            change_reason: 变更原因

        Returns:
            是否成功删除
        """
        db_path = self._get_db_path()

        def _do_delete():
            with self._get_session() as session:
                asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
                if not asset:
                    return False

                self._record_change(
                    session, asset_id, 'delete', None,
                    asset.name, None,
                    changed_by=changed_by, change_reason=change_reason
                )

                if hard_delete:
                    session.delete(asset)
                else:
                    asset.status = 'deleted'

                return True

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path:
            with DatabaseLock(db_path):
                return _do_delete()
        else:
            return _do_delete()

    # ==================== 查询操作 ====================

    @retry_on_lock(max_retries=5)
    def list_assets(
        self,
        asset_type: str = None,
        status: str = None,
        importance: str = None,
        environment: str = None,
        owner: str = None,
        department: str = None,
        ip_range: str = None,
        vendor: str = None,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[Dict]:
        """
        列出资产（支持多维度过滤）

        Args:
            asset_type: 资产类型
            status: 资产状态
            importance: 重要性
            environment: 环境
            owner: 负责人
            department: 部门
            ip_range: IP范围（CIDR格式，如192.168.1.0/24）
            vendor: 厂商
            limit: 返回数量限制
            offset: 偏移量（分页）
            include_deleted: 是否包含已删除资产

        Returns:
            资产列表
        """
        with self._get_session() as session:
            query = session.query(Asset)

            if not include_deleted:
                query = query.filter(Asset.status != 'deleted')

            if asset_type:
                query = query.filter(Asset.asset_type == asset_type)
            if status:
                query = query.filter(Asset.status == status)
            if importance:
                query = query.filter(Asset.importance == importance)
            if environment:
                query = query.filter(Asset.environment == environment)
            if owner:
                query = query.filter(Asset.owner == owner)
            if department:
                query = query.filter(Asset.department == department)
            if vendor:
                query = query.filter(Asset.vendor == vendor)

            if ip_range:
                # CIDR过滤
                try:
                    network = ipaddress.ip_network(ip_range, strict=False)
                    # 构建IP范围条件
                    ip_conditions = []
                    for ip in network.hosts():
                        ip_conditions.append(Asset.ip_address == str(ip))
                    # 对于大网段，使用前缀匹配
                    if len(ip_conditions) > 256:
                        network_str = str(network.network_address)
                        prefix = '.'.join(network_str.split('.')[:3])
                        query = query.filter(Asset.ip_address.like(f'{prefix}%'))
                    else:
                        if ip_conditions:
                            query = query.filter(or_(*ip_conditions))
                except ValueError:
                    pass  # 无效的CIDR，忽略过滤

            assets = query.order_by(Asset.updated_at.desc()).offset(offset).limit(limit).all()
            return [a.to_dict() for a in assets]

    @retry_on_lock(max_retries=5)
    def find_assets(
        self,
        keyword: str,
        fields: List[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        关键字搜索资产

        Args:
            keyword: 搜索关键字
            fields: 搜索字段列表，默认搜索name, ip_address, description
            limit: 返回数量限制

        Returns:
            匹配的资产列表
        """
        if not fields:
            fields = ['name', 'ip_address', 'description', 'owner', 'vendor', 'model']

        with self._get_session() as session:
            query = session.query(Asset).filter(Asset.status != 'deleted')

            conditions = []
            for field in fields:
                if hasattr(Asset, field):
                    conditions.append(getattr(Asset, field).like(f'%{keyword}%'))

            if conditions:
                query = query.filter(or_(*conditions))

            assets = query.limit(limit).all()
            return [a.to_dict() for a in assets]

    @retry_on_lock(max_retries=5)
    def get_asset_by_ip(self, ip_address: str) -> Optional[Dict]:
        """通过IP地址获取资产"""
        with self._get_session() as session:
            asset = session.query(Asset).filter(
                Asset.ip_address == ip_address,
                Asset.status != 'deleted'
            ).first()
            return asset.to_dict() if asset else None

    @retry_on_lock(max_retries=5)
    def get_asset_by_name(self, name: str) -> Optional[Dict]:
        """通过名称获取资产"""
        with self._get_session() as session:
            asset = session.query(Asset).filter(
                Asset.name == name,
                Asset.status != 'deleted'
            ).first()
            return asset.to_dict() if asset else None

    # ==================== 密码管理 ====================

    @retry_on_lock(max_retries=5)
    def get_password(self, asset_id: str) -> Optional[str]:
        """
        获取资产密码（解密）

        Args:
            asset_id: 资产ID

        Returns:
            明文密码
        """
        with self._get_session() as session:
            asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
            if asset and asset.password_encrypted:
                return decrypt_password(asset.password_encrypted)
            return None

    @retry_on_lock(max_retries=15)
    def update_password(
        self,
        asset_id: str,
        new_password: str,
        changed_by: str = "system",
        change_reason: str = None
    ) -> bool:
        """
        更新资产密码

        Args:
            asset_id: 资产ID
            new_password: 新密码
            changed_by: 变更人
            change_reason: 变更原因

        Returns:
            是否成功
        """
        db_path = self._get_db_path()

        def _do_update_password():
            with self._get_session() as session:
                asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
                if not asset:
                    return False

                old_password = asset.password_encrypted
                asset.password_encrypted = encrypt_password(new_password)
                asset.updated_at = datetime.now()

                self._record_change(
                    session, asset_id, 'password', 'password',
                    '******', '******',
                    changed_by=changed_by, change_reason=change_reason
                )

                return True

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path:
            with DatabaseLock(db_path):
                return _do_update_password()
        else:
            return _do_update_password()

    # ==================== 批量操作 ====================

    @retry_on_lock(max_retries=15)
    def batch_create(
        self,
        assets: List[Dict],
        dry_run: bool = False,
        changed_by: str = "system"
    ) -> Dict:
        """
        批量创建资产

        Args:
            assets: 资产数据列表
            dry_run: 试运行模式，不实际写入
            changed_by: 变更人

        Returns:
            {'created': [...], 'errors': [...], 'total': N}
        """
        db_path = self._get_db_path()
        created = []
        errors = []

        def _do_batch_create():
            nonlocal created, errors
            with self._get_session() as session:
                for asset_data in assets:
                    try:
                        # 复制数据，避免修改原始字典
                        data = asset_data.copy()

                        # 处理密码加密
                        if 'password' in data and data['password']:
                            data['password_encrypted'] = encrypt_password(data.pop('password'))

                        # 处理标签
                        if 'tags' in data and isinstance(data['tags'], list):
                            data['tags'] = ','.join(data['tags'])

                        # 处理自定义字段
                        if 'custom_fields' in data and isinstance(data['custom_fields'], dict):
                            data['custom_fields'] = json.dumps(data['custom_fields'])

                        if dry_run:
                            created.append({'dry_run': True, 'data': data})
                        else:
                            asset = Asset(**data)
                            session.add(asset)
                            session.flush()

                            self._record_change(
                                session, asset.asset_id, 'create', None, None, None,
                                changed_by=changed_by, change_reason='批量创建'
                            )

                            created.append(asset.to_dict())

                    except Exception as e:
                        errors.append({
                            'data': asset_data,
                            'error': str(e)
                        })

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path and not dry_run:
            with DatabaseLock(db_path):
                _do_batch_create()
        else:
            _do_batch_create()

        return {
            'created': created,
            'errors': errors,
            'total': len(assets),
            'success_count': len(created),
            'error_count': len(errors)
        }

    @retry_on_lock(max_retries=15)
    def batch_update(
        self,
        updates: List[Dict],
        dry_run: bool = False,
        changed_by: str = "system"
    ) -> Dict:
        """
        批量更新资产

        Args:
            updates: 更新数据列表，每项需包含asset_id
            dry_run: 试运行模式
            changed_by: 变更人

        Returns:
            {'updated': [...], 'errors': [...], 'total': N}
        """
        db_path = self._get_db_path()
        updated = []
        errors = []

        def _do_batch_update():
            nonlocal updated, errors
            with self._get_session() as session:
                for update_data in updates:
                    # 复制数据，避免修改原始字典
                    data = update_data.copy()
                    asset_id = data.pop('asset_id', None)
                    if not asset_id:
                        errors.append({'data': update_data, 'error': '缺少asset_id'})
                        continue

                    try:
                        asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
                        if not asset:
                            errors.append({'data': update_data, 'error': f'资产不存在: {asset_id}'})
                            continue

                        if dry_run:
                            updated.append({'dry_run': True, 'asset_id': asset_id, 'data': data})
                        else:
                            for key, value in data.items():
                                if hasattr(asset, key):
                                    if key == 'password' and value:
                                        asset.password_encrypted = encrypt_password(value)
                                    elif key == 'tags' and isinstance(value, list):
                                        asset.tags = ','.join(value)
                                    else:
                                        setattr(asset, key, value)

                            asset.updated_at = datetime.now()
                            updated.append(asset.to_dict())

                    except Exception as e:
                        errors.append({'data': update_data, 'error': str(e)})

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path and not dry_run:
            with DatabaseLock(db_path):
                _do_batch_update()
        else:
            _do_batch_update()

        return {
            'updated': updated,
            'errors': errors,
            'total': len(updates),
            'success_count': len(updated),
            'error_count': len(errors)
        }

    @retry_on_lock(max_retries=15)
    def batch_delete(
        self,
        asset_ids: List[str],
        hard_delete: bool = False,
        changed_by: str = "system"
    ) -> Dict:
        """
        批量删除资产

        Args:
            asset_ids: 资产ID列表
            hard_delete: 是否硬删除
            changed_by: 变更人

        Returns:
            {'deleted': [...], 'errors': [...], 'total': N}
        """
        db_path = self._get_db_path()
        deleted = []
        errors = []

        def _do_batch_delete():
            nonlocal deleted, errors
            with self._get_session() as session:
                for asset_id in asset_ids:
                    try:
                        asset = session.query(Asset).filter(Asset.asset_id == asset_id).first()
                        if not asset:
                            errors.append({'asset_id': asset_id, 'error': '资产不存在'})
                            continue

                        self._record_change(
                            session, asset_id, 'delete', None, asset.name, None,
                            changed_by=changed_by, change_reason='批量删除'
                        )

                        if hard_delete:
                            session.delete(asset)
                        else:
                            asset.status = 'deleted'

                        deleted.append(asset_id)

                    except Exception as e:
                        errors.append({'asset_id': asset_id, 'error': str(e)})

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path:
            with DatabaseLock(db_path):
                _do_batch_delete()
        else:
            _do_batch_delete()

        return {
            'deleted': deleted,
            'errors': errors,
            'total': len(asset_ids),
            'success_count': len(deleted),
            'error_count': len(errors)
        }

    @retry_on_lock(max_retries=5)
    def batch_get(self, asset_ids: List[str]) -> List[Dict]:
        """
        批量获取资产

        Args:
            asset_ids: 资产ID列表

        Returns:
            资产列表
        """
        with self._get_session() as session:
            assets = session.query(Asset).filter(
                Asset.asset_id.in_(asset_ids),
                Asset.status != 'deleted'
            ).all()
            return [a.to_dict() for a in assets]

    # ==================== 统计分析 ====================

    @retry_on_lock(max_retries=5)
    def get_statistics(
        self,
        by_type: bool = False,
        by_status: bool = False,
        by_environment: bool = False,
        by_importance: bool = False,
        by_vendor: bool = False,
        by_owner: bool = False
    ) -> Dict:
        """
        多维度资产统计

        Args:
            by_type: 按类型统计
            by_status: 按状态统计
            by_environment: 按环境统计
            by_importance: 按重要性统计
            by_vendor: 按厂商统计
            by_owner: 按负责人统计

        Returns:
            统计结果字典
        """
        with self._get_session() as session:
            result = {
                'total': session.query(Asset).filter(Asset.status != 'deleted').count()
            }

            if by_type:
                rows = session.query(
                    Asset.asset_type,
                    func.count(Asset.asset_id)
                ).filter(Asset.status != 'deleted').group_by(Asset.asset_type).all()
                result['by_type'] = {row[0]: row[1] for row in rows}

            if by_status:
                rows = session.query(
                    Asset.status,
                    func.count(Asset.asset_id)
                ).filter(Asset.status != 'deleted').group_by(Asset.status).all()
                result['by_status'] = {row[0]: row[1] for row in rows}

            if by_environment:
                rows = session.query(
                    Asset.environment,
                    func.count(Asset.asset_id)
                ).filter(Asset.status != 'deleted').group_by(Asset.environment).all()
                result['by_environment'] = {row[0]: row[1] for row in rows}

            if by_importance:
                rows = session.query(
                    Asset.importance,
                    func.count(Asset.asset_id)
                ).filter(Asset.status != 'deleted').group_by(Asset.importance).all()
                result['by_importance'] = {row[0]: row[1] for row in rows}

            if by_vendor:
                rows = session.query(
                    Asset.vendor,
                    func.count(Asset.asset_id)
                ).filter(
                    Asset.status != 'deleted',
                    Asset.vendor.isnot(None)
                ).group_by(Asset.vendor).all()
                result['by_vendor'] = {row[0]: row[1] for row in rows}

            if by_owner:
                rows = session.query(
                    Asset.owner,
                    func.count(Asset.asset_id)
                ).filter(
                    Asset.status != 'deleted',
                    Asset.owner.isnot(None)
                ).group_by(Asset.owner).all()
                result['by_owner'] = {row[0]: row[1] for row in rows}

            return result

    # ==================== 变更历史 ====================

    def _record_change(
        self,
        session,
        asset_id: str,
        change_type: str,
        field_name: str,
        old_value: str,
        new_value: str,
        changed_by: str = "system",
        change_reason: str = None
    ):
        """记录变更日志（内部方法）"""
        log = AssetChangeLog(
            asset_id=asset_id,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            change_reason=change_reason
        )
        session.add(log)

    @retry_on_lock(max_retries=5)
    def get_change_history(
        self,
        asset_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取资产变更历史

        Args:
            asset_id: 资产ID
            limit: 返回数量限制

        Returns:
            变更记录列表
        """
        with self._get_session() as session:
            logs = session.query(AssetChangeLog).filter(
                AssetChangeLog.asset_id == asset_id
            ).order_by(AssetChangeLog.created_at.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]

    # ==================== 资产关系 ====================

    @retry_on_lock(max_retries=15)
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        description: str = None,
        created_by: str = "system"
    ) -> Dict:
        """
        添加资产关系

        Args:
            source_id: 源资产ID
            target_id: 目标资产ID
            relation_type: 关系类型（depends_on, connects_to, hosts等）
            description: 关系描述
            created_by: 创建人

        Returns:
            操作结果
        """
        db_path = self._get_db_path()

        def _do_add_relationship():
            with self._get_session() as session:
                # 验证资产存在
                source = session.query(Asset).filter(Asset.asset_id == source_id).first()
                target = session.query(Asset).filter(Asset.asset_id == target_id).first()

                if not source or not target:
                    return {'success': False, 'error': '源资产或目标资产不存在'}

                # 检查关系是否已存在
                existing = session.execute(
                    asset_relationships.select().where(
                        asset_relationships.c.source_id == source_id,
                        asset_relationships.c.target_id == target_id,
                        asset_relationships.c.relation_type == relation_type
                    )
                ).fetchone()

                if existing:
                    return {'success': False, 'error': '关系已存在'}

                # 创建关系
                import uuid
                stmt = asset_relationships.insert().values(
                    id=str(uuid.uuid4()),
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    description=description,
                    created_by=created_by
                )
                session.execute(stmt)

                return {
                    'success': True,
                    'source_id': source_id,
                    'target_id': target_id,
                    'relation_type': relation_type
                }

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path:
            with DatabaseLock(db_path):
                return _do_add_relationship()
        else:
            return _do_add_relationship()

    @retry_on_lock(max_retries=5)
    def get_relationships(
        self,
        asset_id: str,
        direction: str = "both"
    ) -> List[Dict]:
        """
        获取资产关系

        Args:
            asset_id: 资产ID
            direction: 方向（outgoing/incoming/both）

        Returns:
            关系列表
        """
        with self._get_session() as session:
            results = []

            if direction in ['outgoing', 'both']:
                outgoing = session.execute(
                    asset_relationships.select().where(
                        asset_relationships.c.source_id == asset_id
                    )
                ).fetchall()
                for row in outgoing:
                    results.append({
                        'id': row.id,
                        'target_id': row.target_id,
                        'relation_type': row.relation_type,
                        'description': row.description,
                        'direction': 'outgoing',
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'created_by': row.created_by
                    })

            if direction in ['incoming', 'both']:
                incoming = session.execute(
                    asset_relationships.select().where(
                        asset_relationships.c.target_id == asset_id
                    )
                ).fetchall()
                for row in incoming:
                    results.append({
                        'id': row.id,
                        'source_id': row.source_id,
                        'relation_type': row.relation_type,
                        'description': row.description,
                        'direction': 'incoming',
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'created_by': row.created_by
                    })

            return results

    @retry_on_lock(max_retries=15)
    def remove_relationship(self, relationship_id: str) -> bool:
        """
        删除资产关系

        Args:
            relationship_id: 关系ID

        Returns:
            是否成功
        """
        db_path = self._get_db_path()

        def _do_remove_relationship():
            with self._get_session() as session:
                result = session.execute(
                    asset_relationships.delete().where(
                        asset_relationships.c.id == relationship_id
                    )
                )
                return result.rowcount > 0

        # 如果是SQLite数据库，使用文件锁保护写入
        if db_path:
            with DatabaseLock(db_path):
                return _do_remove_relationship()
        else:
            return _do_remove_relationship()

    # ==================== 导出功能 ====================

    @retry_on_lock(max_retries=5)
    def export_assets(
        self,
        format: str = "json",
        asset_ids: List[str] = None,
        **filters
    ) -> Union[str, bytes]:
        """
        导出资产数据

        Args:
            format: 导出格式（json/csv）
            asset_ids: 指定资产ID列表
            **filters: 过滤条件

        Returns:
            导出数据
        """
        if asset_ids:
            assets = self.batch_get(asset_ids)
        else:
            assets = self.list_assets(limit=10000, **filters)

        if format == 'json':
            return json.dumps(assets, ensure_ascii=False, indent=2)
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            if assets:
                writer = csv.DictWriter(output, fieldnames=assets[0].keys())
                writer.writeheader()
                writer.writerows(assets)
            return output.getvalue()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    # ==================== 健康检查 ====================

    @retry_on_lock(max_retries=5)
    def health_check(
        self,
        asset_id: str = None,
        asset_ids: List[str] = None,
        check_type: str = "connectivity"
    ) -> Dict:
        """
        健康检查

        Args:
            asset_id: 单个资产ID
            asset_ids: 资产ID列表
            check_type: 检查类型（connectivity/service/port）

        Returns:
            检查结果
        """
        import subprocess
        import socket

        ids = asset_ids if asset_ids else ([asset_id] if asset_id else [])
        if not ids:
            return {'error': '未指定资产ID'}

        results = []
        with self._get_session() as session:
            for aid in ids:
                asset = session.query(Asset).filter(Asset.asset_id == aid).first()
                if not asset:
                    results.append({'asset_id': aid, 'status': 'not_found'})
                    continue

                result = {
                    'asset_id': aid,
                    'name': asset.name,
                    'ip_address': asset.ip_address,
                    'check_type': check_type,
                    'status': 'unknown'
                }

                if check_type == "connectivity" and asset.ip_address:
                    # ICMP ping检查
                    try:
                        # Windows使用-n，Linux使用-c
                        ping_cmd = ['ping', '-n', '1', '-w', '2000', asset.ip_address]
                        response = subprocess.run(ping_cmd, capture_output=True, timeout=5)
                        result['status'] = 'reachable' if response.returncode == 0 else 'unreachable'
                    except Exception as e:
                        result['status'] = 'error'
                        result['error'] = str(e)

                elif check_type == "port" and asset.ip_address and asset.port:
                    # 端口检查
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(3)
                        check_result = sock.connect_ex((asset.ip_address, asset.port))
                        result['status'] = 'open' if check_result == 0 else 'closed'
                        sock.close()
                    except Exception as e:
                        result['status'] = 'error'
                        result['error'] = str(e)

                else:
                    result['status'] = 'skipped'
                    result['reason'] = '缺少必要参数'

                results.append(result)

        return {
            'check_type': check_type,
            'total': len(results),
            'results': results
        }

    # ==================== 审计日志查询 ====================

    @retry_on_lock(max_retries=5)
    def get_audit_logs(
        self,
        asset_id: str = None,
        change_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        changed_by: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取审计日志

        Args:
            asset_id: 资产ID（可选，不指定则查询所有）
            change_type: 变更类型（create/update/delete/password）
            start_date: 开始日期
            end_date: 结束日期
            changed_by: 变更人
            limit: 返回数量限制

        Returns:
            变更日志列表
        """
        with self._get_session() as session:
            query = session.query(AssetChangeLog)

            if asset_id:
                query = query.filter(AssetChangeLog.asset_id == asset_id)
            if change_type:
                query = query.filter(AssetChangeLog.change_type == change_type)
            if changed_by:
                query = query.filter(AssetChangeLog.changed_by == changed_by)
            if start_date:
                query = query.filter(AssetChangeLog.created_at >= start_date)
            if end_date:
                query = query.filter(AssetChangeLog.created_at <= end_date)

            logs = query.order_by(AssetChangeLog.created_at.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]

    # ==================== 风险报告 ====================

    @retry_on_lock(max_retries=5)
    def get_risk_report(
        self,
        asset_type: str = None,
        environment: str = None,
        min_score: int = 0,
        include_details: bool = True
    ) -> Dict:
        """
        生成风险报告

        Args:
            asset_type: 资产类型过滤
            environment: 环境过滤
            min_score: 最低风险分数
            include_details: 是否包含资产详情

        Returns:
            风险报告
        """
        with self._get_session() as session:
            query = session.query(Asset).filter(
                Asset.status != 'deleted',
                Asset.risk_score >= min_score
            )

            if asset_type:
                query = query.filter(Asset.asset_type == asset_type)
            if environment:
                query = query.filter(Asset.environment == environment)

            assets = query.order_by(Asset.risk_score.desc()).all()

            # 统计
            risk_distribution = {
                'critical': 0,  # 80-100
                'high': 0,      # 60-79
                'medium': 0,    # 40-59
                'low': 0        # 0-39
            }

            for asset in assets:
                if asset.risk_score >= 80:
                    risk_distribution['critical'] += 1
                elif asset.risk_score >= 60:
                    risk_distribution['high'] += 1
                elif asset.risk_score >= 40:
                    risk_distribution['medium'] += 1
                else:
                    risk_distribution['low'] += 1

            # 隔离状态统计
            isolation_stats = {}
            for asset in assets:
                status = asset.isolation_status or 'normal'
                isolation_stats[status] = isolation_stats.get(status, 0) + 1

            report = {
                'generated_at': datetime.now().isoformat(),
                'filters': {
                    'asset_type': asset_type,
                    'environment': environment,
                    'min_score': min_score
                },
                'summary': {
                    'total_assets': len(assets),
                    'average_risk_score': sum(a.risk_score or 0 for a in assets) / len(assets) if assets else 0,
                    'max_risk_score': max((a.risk_score or 0 for a in assets), default=0)
                },
                'risk_distribution': risk_distribution,
                'isolation_status': isolation_stats
            }

            if include_details:
                report['assets'] = [a.to_dict() for a in assets[:100]]  # 最多返回100个详情

            return report

    # ==================== 按新字段查询 ====================

    @retry_on_lock(max_retries=5)
    def list_assets_by_risk(
        self,
        min_score: int = 0,
        max_score: int = 100,
        limit: int = 100
    ) -> List[Dict]:
        """
        按风险分数查询资产

        Args:
            min_score: 最低风险分数
            max_score: 最高风险分数
            limit: 返回数量限制

        Returns:
            资产列表
        """
        with self._get_session() as session:
            assets = session.query(Asset).filter(
                Asset.status != 'deleted',
                Asset.risk_score >= min_score,
                Asset.risk_score <= max_score
            ).order_by(Asset.risk_score.desc()).limit(limit).all()
            return [a.to_dict() for a in assets]

    @retry_on_lock(max_retries=5)
    def list_assets_by_isolation_status(
        self,
        isolation_status: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        按隔离状态查询资产

        Args:
            isolation_status: 隔离状态（normal/network/host）
            limit: 返回数量限制

        Returns:
            资产列表
        """
        with self._get_session() as session:
            assets = session.query(Asset).filter(
                Asset.status != 'deleted',
                Asset.isolation_status == isolation_status
            ).limit(limit).all()
            return [a.to_dict() for a in assets]

    @retry_on_lock(max_retries=5)
    def list_assets_by_network_segment(
        self,
        network_segment: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        按网段查询资产

        Args:
            network_segment: 网段标识
            limit: 返回数量限制

        Returns:
            资产列表
        """
        with self._get_session() as session:
            assets = session.query(Asset).filter(
                Asset.status != 'deleted',
                Asset.network_segment == network_segment
            ).limit(limit).all()
            return [a.to_dict() for a in assets]


# 便捷函数
def get_client(db_path: str = None) -> AssetClient:
    """获取资产客户端实例"""
    return AssetClient(db_path=db_path)
