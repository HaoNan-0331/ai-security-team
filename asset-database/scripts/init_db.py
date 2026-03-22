"""
资产库初始化脚本
用于初始化PostgreSQL数据库和Neo4j图数据库
"""

import click
import psycopg2
from neo4j import GraphDatabase
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


@click.group()
def cli():
    """资产库管理工具"""
    load_dotenv()


@cli.command()
@click.option('--create-schema', is_flag=True, help='创建数据库Schema')
@click.option('--load-sample', is_flag=True, help='加载示例数据')
def init_db(create_schema, load_sample):
    """初始化数据库"""
    if create_schema:
        init_postgresql()
        init_neo4j()
    if load_sample:
        load_sample_data()


def init_postgresql():
    """初始化PostgreSQL数据库"""
    logger.info("正在初始化PostgreSQL数据库...")

    db_url = os.getenv('DATABASE_URL',
                      'postgresql://asset_user:asset_password@localhost:5432/asset_db')

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # 读取并执行schema文件
        schema_dir = Path(__file__).parent / 'schema' / 'postgresql'
        schema_files = sorted(schema_dir.glob('*.sql'))

        for schema_file in schema_files:
            logger.info(f"执行 {schema_file.name}...")
            with open(schema_file, 'r', encoding='utf-8') as f:
                cursor.execute(f.read())

        conn.commit()
        cursor.close()
        conn.close()

        logger.success("✅ PostgreSQL数据库初始化成功！")

    except Exception as e:
        logger.error(f"❌ PostgreSQL初始化失败: {e}")
        raise


def init_neo4j():
    """初始化Neo4j图数据库"""
    logger.info("正在初始化Neo4j图数据库...")

    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')

    try:
        driver = GraphDatabase.driver(uri)
        driver.verify_connectivity()

        with GraphDatabase.driver(uri) as driver:
            with driver.session() as session:
                # 读取并执行约束文件
                constraint_file = Path(__file__).parent / 'schema' / 'neo4j' / '01_constraints.cql'
                if constraint_file.exists():
                    with open(constraint_file, 'r', encoding='utf-8') as f:
                        for statement in f.read().split(';'):
                            statement = statement.strip()
                            if statement:
                                session.run(statement)

        logger.success("✅ Neo4j图数据库初始化成功！")

    except Exception as e:
        logger.error(f"❌ Neo4j初始化失败: {e}")
        raise


def load_sample_data():
    """加载示例数据"""
    logger.info("正在加载示例数据...")

    db_url = os.getenv('DATABASE_URL')

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # 示例资产
        sample_assets = [
            ('Core-Firewall-01', 'Security', 'Huawei', 'USG6000', '192.168.1.1',
             'critical', 'production', 'security-team', 'DataCenter-A'),
            ('Web-Server-01', 'Server', 'Dell', 'PowerEdge R740', '192.168.1.100',
             'high', 'production', 'web-team', 'DataCenter-A'),
            ('DB-Primary', 'Database', 'Oracle', 'Exadata X8M', '192.168.2.10',
             'critical', 'production', 'dba-team', 'DataCenter-B'),
        ]

        for asset in sample_assets:
            cursor.execute("""
                INSERT INTO assets (name, type, manufacturer, model, ip_address,
                                     importance, environment, owner, site)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (serial_number) DO NOTHING
            """, asset)

        conn.commit()
        cursor.close()
        conn.close()

        logger.success(f"✅ 已加载 {len(sample_assets)} 条示例资产")

    except Exception as e:
        logger.error(f"❌ 加载示例数据失败: {e}")
        raise


@cli.command()
@click.option('--output', '-o', default='data/backups', help='备份目录')
def backup(output):
    """备份数据库"""
    from datetime import datetime
    from subprocess import run

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = output_dir / f'backup_{timestamp}.sql'

    logger.info(f"正在备份数据库到 {backup_file}...")

    db_url = os.getenv('DATABASE_URL')

    try:
        run(f'pg_dump {db_url} > {backup_file}', shell=True, check=True)
        logger.success(f"✅ 备份完成: {backup_file}")
    except Exception as e:
        logger.error(f"❌ 备份失败: {e}")
        raise


@cli.command()
@click.argument('backup_file', type=click.Path(exists=True))
def restore(backup_file):
    """恢复数据库"""
    logger.info(f"正在从 {backup_file} 恢复数据库...")

    db_url = os.getenv('DATABASE_URL')

    try:
        run(f'psql {db_url} < {backup_file}', shell=True, check=True)
        logger.success("✅ 恢复完成")
    except Exception as e:
        logger.error(f"❌ 恢复失败: {e}")
        raise


if __name__ == '__main__':
    cli()
