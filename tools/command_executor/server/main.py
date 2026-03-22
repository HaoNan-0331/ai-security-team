"""
服务端主入口
同时启动WebSocket服务和API服务
"""
import asyncio
import logging
import logging.handlers
import threading
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.config import (
    SERVER_HOST, SERVER_PORT, API_PORT,
    LOG_LEVEL, LOG_FORMAT, LOG_DIR, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT
)
from server.database import init_database, SessionManager, get_db
from server.websocket_server import WebSocketServer, set_ws_server
from server.api_server import run_api_server


def setup_logging():
    """配置日志系统"""
    # 确保日志目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(LOG_FORMAT)

    # 文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


# 初始化日志配置
setup_logging()
logger = logging.getLogger(__name__)


def cleanup_old_sessions():
    """定期清理过期会话"""
    import time
    while True:
        try:
            db = next(get_db())
            try:
                deleted = SessionManager.cleanup_old_sessions(db)
                if deleted > 0:
                    logger.info(f"已清理 {deleted} 条过期会话记录")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"清理会话失败: {e}")
        time.sleep(86400)  # 每天执行一次


def run_api_server_in_thread(host: str, port: int):
    """在线程中运行API服务器，显式管理事件循环以兼容Python 3.6"""
    # Python 3.6 需要在新线程中显式创建事件循环
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 导入并运行 API 服务器
    from server.api_server import run_api_server
    run_api_server(host, port)


def main():
    """主函数"""
    # 初始化数据库
    logger.info("正在初始化数据库...")
    init_database()

    # 创建WebSocket服务器实例
    ws_server_instance = WebSocketServer(SERVER_HOST, SERVER_PORT)
    set_ws_server(ws_server_instance)

    # 启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
    cleanup_thread.start()
    logger.info("已启动会话清理线程")

    # 启动API服务（使用线程，显式管理事件循环以兼容 Python 3.6）
    api_thread = threading.Thread(
        target=run_api_server_in_thread,
        args=(SERVER_HOST, API_PORT),
        daemon=True
    )
    api_thread.start()
    logger.info(f"API服务已启动在端口 {API_PORT}")

    # 启动WebSocket服务（主线程）
    logger.info(f"WebSocket服务已启动在端口 {SERVER_PORT}")
    logger.info("服务端已就绪，等待客户端连接...")

    try:
        # Python 3.6 兼容方式
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ws_server_instance.start())
    except KeyboardInterrupt:
        logger.info("服务端正在关闭...")
    except Exception as e:
        logger.error(f"服务端错误: {e}")


if __name__ == "__main__":
    main()
