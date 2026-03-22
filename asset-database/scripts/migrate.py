"""
数据库迁移工具
管理数据库版本和迁移脚本执行
"""

import click
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import List
from loguru import logger

from dotenv import load_dotenv

load_dotenv()


# =====================================================
# 迁移脚本目录
# =====================================================

MIGRATIONS_DIR = Path(__file__).parent.parent / "schema" / "postgresql"
MIGRATION_TABLE = "schema_migrations"


def get_current_version(conn) -> int:
    """
    获取当前数据库版本
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT MAX(version) as version
        FROM {MIGRATION_TABLE}
    """)
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result and result[0] else 0


def get_available_migrations() -> List[Path]:
    """
    获取所有可用的迁移脚本
    """
    if not MIGRATIONS_DIR.exists():
        return []

    return sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda f: int(f.stem.split('_')[0]))


def execute_migration(conn, migration_file: Path) -> bool:
    """
    执行单个迁移脚本
    """
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        # 分割SQL语句（处理多个语句）
        statements = []
        current_statement = []
        for line in sql.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            current_statement.append(line)
            if line.endswith(';'):
                statement = '\n'.join(current_statement)
                statements.append(statement)
                current_statement = []

        # 执行每个语句
        cursor = conn.cursor()
        for statement in statements:
            cursor.execute(statement)

        conn.commit()
        logger.success(f"✅ 迁移 {migration_file.name} 执行成功")
        return True

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ 迁移 {migration_file.name} 执行失败: {e}")
        return False


def record_migration(conn, version: int, name: str, description: str):
    """
    记录迁移历史
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO {MIGRATION_TABLE} (version, name, description, applied_at)
        VALUES (%s, %s, %s, NOW())
    """, (version, name, description))
    conn.commit()
    cursor.close()


# =====================================================
# CLI 命令
# =====================================================

@click.group()
def cli():
    """数据库迁移工具"""
    pass


@cli.command()
@click.option('--target-version', '-t', type=int, help='目标版本')
@click.option('--dry-run', is_flag=True, help='试运行（不实际执行）')
def migrate(target_version, dry_run):
    """
    执行数据库迁移到指定版本
    """
    import os
    db_url = os.getenv('DATABASE_URL')

    if not db_url:
        logger.error("DATABASE_URL 环境变量未设置")
        return

    try:
        conn = psycopg2.connect(db_url)
        current_version = get_current_version(conn)
        logger.info(f"当前数据库版本: {current_version}")

        if target_version <= current_version:
            logger.info(f"数据库已是 {target_version} 版本，无需迁移")
            return

        # 获取可用迁移
        migrations = get_available_migrations()

        # 筛选需要执行的迁移
        to_apply = [m for m in migrations if int(m.stem.split('_')[0]) > current_version and int(m.stem.split('_')[0]) <= target_version]

        if not to_apply:
            logger.info("没有需要执行的迁移")
            return

        logger.info(f"将执行 {len(to_apply)} 个迁移:")
        for m in to_apply:
            logger.info(f"  - {m.name}")

        if dry_run:
            logger.info("🏃 试运行模式，不会实际执行")

        # 执行迁移
        for m in to_apply:
            if dry_run:
                logger.info(f"  [DRY RUN] {m.name}")
            else:
                if execute_migration(conn, m):
                    version_num = int(m.stem.split('_')[0])
                    name = m.stem.replace('_', ' ').title()
                    record_migration(conn, version_num, name, f"Apply {m.name}")
                else:
                    logger.error(f"迁移失败，停止后续迁移")
                    break

        conn.close()
        logger.success("✅ 迁移完成")

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")


@cli.command()
def status():
    """
    查看迁移状态
    """
    import os
    db_url = os.getenv('DATABASE_URL')

    try:
        conn = psycopg2.connect(db_url)
        current_version = get_current_version(conn)
        conn.close()

        migrations = get_available_migrations()

        click.echo(f"\n📋 当前版本: {current_version}")
        click.echo(f"📋 可用迁移: {len(migrations)}")

        if migrations:
            click.echo("\n可执行的迁移:")
            for m in migrations:
                version_num = int(m.stem.split('_')[0])
                status = "✅ " if version_num > current_version else "✓ "
                click.echo(f"{status} {m.name} ({'已应用' if version_num <= current_version else '待执行'})")

    except Exception as e:
        logger.error(f"❌ 查询失败: {e}")


@cli.command()
@click.argument('version', type=int)
@click.option('--name', '-n', help='迁移名称')
@click.option('--description', '-d', help='迁移描述')
def create(version, name, description):
    """
    创建新的迁移脚本模板
    """
    import os
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"{version:03d}_{timestamp}_{name.replace(' ', '_').lower()}.sql"

    template = f"""-- =====================================================
-- AI Security Team - Asset Database
-- Migration: {version:03d} - {name}
-- Version: 1.{version // 10}.{version % 10}
-- Created: {timestamp}
-- =====================================================

-- Migration Description
-- {description}

-- =====================================================
-- Upgrades
-- =====================================================

-- TODO: 在此处添加您的迁移SQL语句
-- ALTER TABLE assets ADD COLUMN new_field VARCHAR(100);

-- =====================================================
-- Version Update
-- =====================================================

INSERT INTO schema_migrations (version, name, description)
VALUES ({version}, '{filename}', '{description}');
"""

    migrations_dir = MIGRATIONS_DIR
    migrations_dir.mkdir(parents=True, exist_ok=True)

    output_file = migrations_dir / filename
    output_file.write_text(template)

    click.echo(f"✅ 迁移模板已创建: {output_file}")
        click.echo(f"请编辑文件并添加迁移SQL语句")


if __name__ == "__main__":
    cli()
