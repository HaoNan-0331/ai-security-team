#!/usr/bin/env python3
import asyncio
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/syslog-server")

from syslog_server.storage.manager import StorageManager
from syslog_server.config.settings import settings


async def main():
    storage = StorageManager(
        database_url=str(settings.database_url),
        redis_url=str(settings.redis_url)
    )
    await storage.initialize()
    
    hours = 1
    since = datetime.now() - timedelta(hours=hours)
    
    print(f"=== Syslog 服务器日志查看 ===")
    print(f"时间范围：最近 {hours} 小时")
    print("-" * 60)
    
    try:
        logs = await storage.get_logs(limit=20, offset=0, since=since)
        print(f"最近 {len(logs)} 条日志:")
        print("-" * 60)
        
        for i, log in enumerate(logs, 1):
            print(f"\n[{i}] {log.received_at}")
            print(f"    设备IP: {log.device_ip}")
            print(f"    严重级别: {log.severity_label}")
            print(f"    消息: {log.message[:100]}")
            
    except Exception as e:
        print(f"查询失败: {e}")
        
    finally:
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
