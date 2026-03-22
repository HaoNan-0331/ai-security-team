"""
客户端直接启动脚本（用于测试）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.websocket_client import WebSocketClient

async def main():
    client = WebSocketClient()
    print(f"""
╔═══════════════════════════════════════════════════════╗
║        分布式命令执行系统 - 客户端 v1.0                 ║
╚═══════════════════════════════════════════════════════╝

  客户端识别码: {client.get_client_id()}
  服务端地址: {client.config.server_host}:{client.config.server_port}
  使用TLS: {client.config.use_tls}

正在连接到服务端...
按 Ctrl+C 停止客户端
    """)

    await client.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n客户端已停止")
