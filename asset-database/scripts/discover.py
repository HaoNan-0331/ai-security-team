"""
资产清单导入工具
支持从 CSV/Excel/YAML 格式导入资产
"""

import click
import yaml
import pandas as pd
from pathlib import Path
from typing import Optional
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from api.database import get_db
from api.models.asset import AssetModel
from loguru import logger


# =====================================================
# CSV 格式定义
# =====================================================

REQUIRED_COLUMNS = [
    'name', 'type', 'ip_address', 'importance', 'environment', 'owner'
]

OPTIONAL_COLUMNS = [
    'manufacturer', 'model', 'serial_number', 'mac_address', 'hostname',
    'site', 'building', 'floor', 'room', 'rack', 'rack_unit',
    'business_unit', 'cost_center', 'cvss_score', 'vulnerability_count',
    'os_type', 'os_version', 'services'
]


def import_csv(file_path: Path, db_session):
    """
    从 CSV 文件导入资产
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        logger.info(f"从 CSV 文件读取到 {len(df)} 行")

        # 验证必需列
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            logger.warning(f"⚠️  CSV 文件缺少必需列: {missing_cols}")
            logger.info("将使用默认值...")

        # 处理空值
        df = df.fillna({
            'importance': 'medium',
            'environment': 'development'
        })

        # 导入数据
        success_count = 0
        for idx, row in df.iterrows():
            try:
                asset = AssetModel(
                    name=row['name'],
                    type=row['type'],
                    ip_address=row.get('ip_address'),
                    mac_address=row.get('mac_address'),
                    hostname=row.get('hostname'),
                    importance=row.get('importance', 'medium'),
                    environment=row.get('environment', 'development'),
                    manufacturer=row.get('manufacturer'),
                    model=row.get('model'),
                    serial_number=row.get('serial_number'),
                    site=row.get('site'),
                    building=row.get('building'),
                    floor=row.get('floor'),
                    room=row.get('room'),
                    rack=row.get('rack'),
                    rack_unit=row.get('rack_unit'),
                    business_unit=row.get('business_unit'),
                    owner=row.get('owner'),
                    cvss_score=float(row.get('cvss_score', 0)) if pd.notna(row.get('cvss_score')) else None
                )

                db_session.add(asset)
                success_count += 1

            except Exception as e:
                logger.error(f"❌ 第 {idx+2} 行导入失败: {e}")

        logger.success(f"✅ CSV 导入完成: {success_count}/{len(df)} 条资产成功")
        return success_count

    except Exception as e:
        logger.error(f"❌ CSV 文件读取失败: {e}")
        return 0


def import_excel(file_path: Path, db_session):
    """
    从 Excel 文件导入资产
    """
    try:
        # 尝试读取 Excel 文件
        df = pd.read_excel(file_path, engine='openpyxl')
        logger.info(f"从 Excel 文件读取到 {len(df)} 行")

        # 标准化列名
        df.columns = df.columns.str.lower()
        df.rename(columns={
            '设备名称': 'name',
            '设备类型': 'type',
            'IP地址': 'ip_address',
            'MAC地址': 'mac_address',
            '主机名': 'hostname',
            '厂商': 'manufacturer',
            '型号': 'model',
            '序列号': 'serial_number',
            '站点': 'site',
            '重要性': 'importance',
            '环境': 'environment',
            '责任人': 'owner',
            'CVSS评分': 'cvss_score'
        }, inplace=True)

        # 验证必需列
        missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            logger.warning(f"⚠️ Excel 文件缺少必需列: {missing_cols}")

        # 处理空值
        df = df.fillna({
            'importance': 'medium',
            'environment': 'development'
        })

        # 导入数据
        success_count = 0
        for idx, row in df.iterrows():
            try:
                asset = AssetModel(
                    name=row['name'],
                    type=row['type'],
                    ip_address=row.get('ip_address'),
                    mac_address=row.get('mac_address'),
                    hostname=row.get('hostname'),
                    importance=row.get('importance', 'medium'),
                    environment=row.get('environment', 'development'),
                    manufacturer=row.get('manufacturer'),
                    model=row.get('model'),
                    serial_number=row.get('serial_number'),
                    site=row.get('site'),
                    business_unit=row.get('business_unit'),
                    owner=row.get('owner'),
                    cvss_score=float(row.get('cvss_score', 0)) if pd.notna(row.get('cvss_score')) else None
                )

                db_session.add(asset)
                success_count += 1

            except Exception as e:
                logger.error(f"❌ 第 {idx+2} 行导入失败: {e}")

        logger.success(f"✅ Excel 导入完成: {success_count}/{len(df)} 条资产成功")
        return success_count

    except Exception as e:
        logger.error(f"❌ Excel 文件读取失败: {e}")
        return 0


def import_yaml(file_path: Path, db_session):
    """
    从 YAML 文件导入资产
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or 'assets' not in data:
                logger.error("❌ YAML 文件格式错误：缺少 'assets' 键")
                return 0

        assets = data['assets']
        logger.info(f"从 YAML 文件读取到 {len(assets)} 条资产")

        success_count = 0
        for asset_data in assets:
            try:
                asset = AssetModel(
                    name=asset_data.get('name'),
                    type=asset_data.get('type'),
                    ip_address=asset_data.get('ip_address'),
                    mac_address=asset_data.get('mac_address'),
                    hostname=asset_data.get('hostname'),
                    importance=asset_data.get('importance', 'medium'),
                    environment=asset_data.get('environment', 'development'),
                    manufacturer=asset_data.get('manufacturer'),
                    model=asset_data.get('model'),
                    serial_number=asset_data.get('serial_number'),
                    site=asset_data.get('site'),
                    building=asset_data.get('building'),
                    floor=asset_data.get('floor'),
                    room=asset_data.get('room'),
                    rack=asset_data.get('rack'),
                    rack_unit=asset_data.get('rack_unit'),
                    business_unit=asset_data.get('business_unit'),
                    owner=asset_data.get('owner'),
                    config=asset_data.get('config'),
                    services=asset_data.get('services', []),
                    metadata=asset_data.get('metadata', {})
                )

                db_session.add(asset)
                success_count += 1

            except Exception as e:
                logger.error(f"❌ 资产导入失败: {e}")

        logger.success(f"✅ YAML 导入完成: {success_count}/{len(assets)} 条资产成功")
        return success_count

    except Exception as e:
        logger.error(f"❌ YAML 文件读取失败: {e}")
        return 0


# =====================================================
# CLI 命令
# =====================================================

@click.group()
def cli():
    """资产导入工具"""
    pass


@cli.command()
@click.argument('file', type=click.Path(exists=True), required=True)
@click.option('--format', '-f', type=click.Choice(['csv', 'excel', 'yaml']), default='auto', help='文件格式')
@click.option('--dry-run', is_flag=True, help='试运行（不实际导入）')
def import_(file: click.Path, format: str, dry_run: bool):
    """
    导入资产清单

    示例:
      python import_inventory.py data/inventory/devices.yaml
      python import_inventory.py data/inventory/devices.csv
      python import_inventory.py data/inventory/devices.xlsx
    """
    from dotenv import load_dotenv
    from api.database import get_db

    load_dotenv()

    # 检测文件格式
    if format == 'auto':
        file_ext = file.suffix.lower()
        if file_ext == '.csv':
            format = 'csv'
        elif file_ext in ['.xlsx', '.xls']:
            format = 'excel'
        elif file_ext == ['.yaml', '.yml']:
            format = 'yaml'
        else:
            logger.error(f"❌ 无法识别文件格式: {file_ext}")
            return

    logger.info(f"导入文件: {file}")
    logger.info(f"文件格式: {format}")

    if dry_run:
        logger.info("🏃 试运行模式，不会实际导入数据")

    # 获取数据库会话
    db_gen = get_db()
    with db_gen() as db:
        if format == 'csv':
            count = import_csv(file, db)
        elif format == 'excel':
            count = import_excel(file, db)
        elif format == 'yaml':
            count = import_yaml(file, db)
        else:
            logger.error(f"❌ 不支持的格式: {format}")
            return

    if not dry_run and count > 0:
        db.commit()
        logger.success(f"✅ 成功导入 {count} 条资产")


@cli.command()
@click.argument('directory', type=click.Path(exists=True), required=True)
@click.option('--recursive', '-r', is_flag=True, help='递归查找')
def scan_directory(directory: click.Path, recursive: bool):
    """
    扫描目录中的所有资产文件并导入
    """
    from dotenv import load_dotenv
    from api.database import get_db

    load_dotenv()

    # 查找所有支持的文件
    pattern = '**/*.csv' if recursive else '*.csv'
    csv_files = list(directory.glob(pattern))

    pattern = '**/*.xlsx' if recursive else '*.xlsx'
    excel_files = list(directory.glob(pattern))

    pattern = '**/*.yaml' if recursive else '*.yaml'
    yaml_files = list(directory.glob(pattern))

    all_files = csv_files + excel_files + yaml_files

    if not all_files:
        logger.warning(f"在 {directory} 中未找到任何支持的文件")
        return

    logger.info(f"找到 {len(all_files)} 个文件")

    db_gen = get_db()
    total_imported = 0

    with db_gen() as db:
        for file_path in all_files:
            file_ext = file_path.suffix.lower()

            if file_ext == '.csv':
                count = import_csv(file_path, db)
            elif file_ext in ['.xlsx', '.xls']:
                count = import_excel(file_path, db)
            elif file_ext in ['.yaml', '.yml']:
                count = import_yaml(file_path, db)

            if count > 0:
                total_imported += count
                db.commit()

    logger.success(f"✅ 扫描目录完成: 共导入 {total_imported} 条资产")


if __name__ == '__main__':
    cli()
