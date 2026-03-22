"""
资产清单导出工具
支持导出为 CSV、Excel、YAML 等多种格式
"""

import click
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import os

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from api.database import get_db
from api.models.asset import AssetModel
from loguru import logger


@click.group()
def cli():
    """资产导出工具"""
    pass


@cli.command()
@click.argument('output', type=click.Path(), required=True)
@click.option('--format', '-f', type=click.Choice(['csv', 'excel', 'yaml', 'json']), default='csv', help='导出格式')
@click.option('--filter', type=str, help='过滤条件（SQL WHERE子句）')
@click.option('--sort', type=str, default='last_seen DESC', help='排序字段')
@click.option('--limit', type=int, default=1000, help='导出数量限制')
@click.option('--fields', type=str, default='all', help='导出字段（逗号分隔）')
def export(output: click.Path, format: str, filter: str, sort: str, limit: int, fields: str):
    """
    导出资产清单
    """
    from dotenv import load_dotenv
    load_dotenv()

    # 确保输出目录存在
    output.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"正在导出资产清单到 {output}，格式：{format}")

    db_gen = get_db()
    with db_gen() as db:
        # 构建查询
        query = db.query(AssetModel)

        # 应用过滤条件
        if filter:
            # 安全的过滤 - 只允许特定字段
            safe_filter = filter.replace(";", " --")  # 移除潜在的分号注入
            query = query.filter(text=safe_filter)
        else:
            # 默认只导出活跃资产
            query = query.filter(AssetModel.status != 'disposed')

        # 应用排序
        if sort:
            # 解析排序字段
            parts = sort.split()
            order_column = getattr(AssetModel, parts[0], None)
            if len(parts) > 1 and parts[1].upper() in ('ASC', 'DESC'):
                query = query.order_by(order_column.desc() if parts[1].upper() == 'DESC' else order_column.asc())

        # 应用限制
        if limit:
            query = query.limit(limit)

        # 执行查询
        assets = query.all()

        if not assets:
            logger.warning("没有找到符合条件的资产")
            return

        logger.success(f"找到 {len(assets)} 条资产")

    # 根据格式导出
    try:
        if format == 'csv':
            export_to_csv(assets, output)
        elif format == 'excel':
            export_to_excel(assets, output, fields)
        elif format == 'yaml':
            export_to_yaml(assets, output)
        elif format == 'json':
            export_to_json(assets, output)
        else:
            logger.error(f"不支持的格式: {format}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"导出失败: {e}")
        sys.exit(1)


def export_to_csv(assets, output: Path):
    """导出为 CSV 格式"""
    import csv

    # 选择要导出的字段
    fields = [
        'asset_id', 'name', 'type', 'manufacturer', 'model', 'serial_number',
        'ip_address', 'mac_address', 'hostname', 'fqdn',
        'site', 'building', 'floor', 'room', 'rack', 'rack_unit',
        'importance', 'environment', 'business_unit', 'owner', 'cost_center',
        'status', 'lifecycle_stage', 'first_seen', 'last_seen', 'last_updated',
        'cvss_score', 'vulnerability_count', 'compliance_level', 'patch_level'
    ]

    # 转换为字典格式
    data = []
    for asset in assets:
        row = {}
        for field in fields:
            value = getattr(asset, field, None)
            if value is not None:
                # 特殊处理
                if field == 'config':
                    row[field] = 'JSON格式见数据库'  # 不导出复杂JSON
                elif field == 'services':
                    row[field] = ','.join(value) if isinstance(value, list) else ''
                elif field == 'relationships':
                    row[field] = '关系数据见数据库'  # 不导出复杂JSON
                elif field == 'metadata':
                    row[field] = '元数据见数据库'  # 不导出复杂JSON
                else:
                    row[field] = value
        data.append(row)

    # 写入 CSV
    with open(output, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)
        writer.writerows(data)

    logger.success(f"CSV 文件已保存: {output}")


def export_to_excel(assets, output: Path, fields: str):
    """导出为 Excel 格式"""
    import xlsxwriter

    # 处理字段列表
    if fields == 'all':
        # 导出所有非JSON字段
        columns = [
            'name', 'type', 'manufacturer', 'model', 'serial_number',
            'ip_address', 'mac_address', 'hostname', 'fqdn',
            'site', 'building', 'floor', 'room', 'rack', 'rack_unit',
            'importance', 'environment', 'business_unit', 'owner', 'cost_center',
            'status', 'lifecycle_stage', 'first_seen', 'last_seen', 'last_updated',
            'cvss_score', 'vulnerability_count', 'compliance_level', 'patch_level'
        ]
    else:
        columns = [f.strip() for f in fields.split(',')]

    # 准备数据
    data = []
    for asset in assets:
        row = {}
        for col in columns:
            value = getattr(asset, col, None)
            if value is not None:
                # 简化复杂字段
                if col in ['config', 'services', 'relationships', 'metadata']:
                    # 转换为可读格式
                    if col == 'config':
                        row[col] = '见数据库'
                    elif col == 'services':
                        row[col] = '、'.join(value) if isinstance(value, list) else value
                    else:
                        row[col] = str(value)
                else:
                    row[col] = value
        data.append(row)

    # 写入 Excel
    with xlsxwriter.Workbook(output) as wb:
        ws = wb.active
        sheet = wb.create_sheet("资产清单", data)
        sheet.freeze()

    logger.success(f"Excel 文件已保存: {output}")


def export_to_yaml(assets, output: Path):
    """导出为 YAML 格式"""
    import yaml

    data = []
    for asset in assets:
        # 转换为字典
        asset_dict = {
            'asset_id': str(asset.asset_id),
            'name': asset.name,
            'type': asset.type,
            'manufacturer': asset.manufacturer,
            'model': asset.model,
            'serial_number': asset.serial_number,
            'ip_address': asset.ip_address,
            'mac_address': str(asset.mac_address) if asset.mac_address else None,
            'hostname': asset.hostname,
            'fqdn': asset.fqdn,
            'subnet': asset.subnet,
            'vlan': asset.vlan,
            'gateway': asset.gateway,
            'dns_servers': list(asset.dns_servers) if asset.dns_servers else [],
            'site': asset.site,
            'building': asset.building,
            'floor': asset.floor,
            'room': asset.room,
            'rack': asset.rack,
            'rack_unit': asset.rack_unit,
            'importance': asset.importance,
            'environment': asset.environment,
            'business_unit': asset.business_unit,
            'owner': asset.owner,
            'cost_center': asset.cost_center,
            'status': asset.status,
            'lifecycle_stage': asset.lifecycle_stage,
            'first_seen': asset.first_seen.isoformat() if asset.first_seen else None,
            'last_seen': asset.last_seen.isoformat() if asset.last_seen else None,
            'last_updated': asset.last_updated.isoformat() if asset.last_updated else None,
            'cvss_score': float(asset.cvss_score) if asset.cvss_score else None,
            'vulnerability_count': asset.vulnerability_count,
            'compliance_level': asset.compliance_level,
            'patch_level': asset.patch_level
        }
        data.append(asset_dict)

    # 写入 YAML
    with open(output, 'w', encoding='utf-8') as f:
        yaml.dump({'assets': data}, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    logger.success(f"YAML 文件已保存: {output}")


def export_to_json(assets, output: Path):
    """导出为 JSON 格式"""
    import json

    data = []
    for asset in assets:
        asset_dict = {
            'asset_id': str(asset.asset_id),
            'name': asset.name,
            'type': asset.type,
            'manufacturer': asset.manufacturer,
            'model': asset.model,
            'serial_number': asset.serial_number,
            'ip_address': asset.ip_address,
            'mac_address': str(asset.mac_address) if asset.mac_address else None,
            'hostname': asset.hostname,
            'fqdn': asset.fqdn,
            'subnet': asset.subnet,
            'vlan': asset.vlan,
            'gateway': asset.gateway,
            'dns_servers': list(asset.dns_servers) if asset.dns_servers else [],
            'site': asset.site,
            'building': asset.building,
            'floor': asset.floor,
            'room': asset.room,
            'rack': asset.rack,
            'rack_unit': asset.rack_unit,
            'importance': asset.importance,
            'environment': asset.environment,
            'business_unit': asset.business_unit,
            'owner': asset.owner,
            'cost_center': asset.cost_center,
            'status': asset.status,
            'lifecycle_stage': asset.lifecycle_stage,
            'first_seen': asset.first_seen.isoformat() if asset.first_seen else None,
            'last_seen': asset.last_seen.isoformat() if asset.last_seen else None,
            'last_updated': asset.last_updated.isoformat() if asset.last_updated else None,
            'cvss_score': float(asset.cvss_score) if asset.cvss_score else None,
            'vulnerability_count': asset.vulnerability_count,
            'compliance_level': asset.compliance_level,
            'patch_level': asset.patch_level,
            'config': asset.config,
            'services': list(asset.services) if asset.services else [],
            'relationships': asset.relationships,
            'metadata': asset.metadata
        }
        data.append(asset_dict)

    # 写入 JSON
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.success(f"JSON 文件已保存: {output}")


if __name__ == '__main__':
    cli()
