"""
客户端主入口
"""
import asyncio
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import requests
import ssl
from urllib3.util.ssl_ import create_urllib3_context

# 配置 urllib3 禁用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加项目根目录到路径
if getattr(sys, 'frozen', False):
    # 打包后的环境
    sys.path.insert(0, str(Path(sys.executable).parent))
else:
    # 开发环境
    sys.path.insert(0, str(Path(__file__).parent.parent))

from client.config import ConfigManager, get_app_dir
from client.websocket_client import WebSocketClient


def setup_logging(config):
    """配置日志系统"""
    # 日志目录 - 使用应用目录
    log_dir = get_app_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 日志文件名（带日期）
    log_file = log_dir / f"client_{datetime.now().strftime('%Y%m%d')}.log"

    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.log_max_bytes,
        backupCount=config.log_backup_count,
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

    return log_file


logger = logging.getLogger(__name__)


class SSLAdapter(requests.adapters.HTTPAdapter):
    """自定义 SSL 适配器，处理旧版本服务器的兼容性问题"""
    def init_poolmanager(self, *args, **kwargs):
        # 创建 SSL 上下文 - 使用 TLS 1.2 以提高与旧版本服务器的兼容性
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # 尝试设置密码套件为更宽松的配置
        try:
            context.set_ciphers('HIGH:!DH:!aNULL')
        except (ssl.SSLError, AttributeError):
            pass

        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


def print_banner():
    """打印启动横幅"""
    print("""
╔═══════════════════════════════════════════════════════╗
║        分布式命令执行系统 - 客户端 v2.1                 ║
║                   (需要认证)                             ║
╚═══════════════════════════════════════════════════════╝
    """)


def print_menu():
    """打印菜单"""
    print("\n=== 命令菜单 ===")
    print("1. 启动客户端")
    print("2. 修改配置")
    print("3. 查看识别码")
    print("4. 退出")


def get_access_token(config, username: str, password: str) -> str:
    """
    通过API获取访问Token

    Returns:
        str: 访问Token

    Raises:
        Exception: 登录失败时
    """
    # 构建API URL
    protocol = "https" if config.use_tls else "http"
    api_url = f"{protocol}://{config.server_host}:{config.api_port}/api/login"

    # 创建带自定义 SSL 适配器的会话
    session = requests.Session()
    if config.use_tls:
        # 挂载自定义 SSL 适配器
        session.mount('https://', SSLAdapter())

    # 调用登录API
    response = session.post(
        api_url,
        json={"username": username, "password": password},
        timeout=10,
        verify=False  # 忽略SSL证书验证（自签名证书）
    )

    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        raise Exception(f"登录失败: {response.status_code} - {response.text}")


async def start_client():
    """启动客户端"""
    # 检查配置
    if not ConfigManager.config_exists():
        print("\n首次运行，需要配置服务端连接信息...")
        ConfigManager.create_config_interactive()

    # 加载配置并设置日志
    config = ConfigManager.load_config()
    log_file = setup_logging(config)
    logger = logging.getLogger(__name__)

    # 输入用户名和密码
    print("\n═════════════════════════════════════════════════════════")
    print("  用户认证")
    print("═════════════════════════════════════════════════════════")
    username = input("\n请输入用户名: ").strip()
    password = input("请输入密码: ").strip()

    # 获取访问Token
    print("\n正在登录...")
    try:
        access_token = get_access_token(config, username, password)
        print("✅ 登录成功！")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        print("\n可能的原因:")
        print("  1. 用户名或密码错误")
        print("  2. 服务端未启动")
        print("  3. 网络连接失败")
        return

    # 创建客户端并传入Token
    client = WebSocketClient(access_token=access_token, username=username)

    # 显示识别码
    print(f"\n═════════════════════════════════════════════════════════")
    print(f"  客户端识别码: {client.get_client_id()}")
    print(f"  登录用户: {username}")
    print(f"═════════════════════════════════════════════════════════")
    print(f"\n正在连接到服务端...")
    print(f"服务端地址: {client.config.server_host}:{client.config.server_port}")
    print(f"API端口: {client.config.api_port}")
    print(f"使用TLS: {client.config.use_tls}")
    print(f"日志文件: {log_file}")
    print(f"\n按 Ctrl+C 停止客户端\n")

    logger.info(f"客户端启动 - 识别码: {client.get_client_id()}, 用户: {username}")

    # 运行客户端
    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("客户端已停止")
        print("\n\n客户端已停止")


def main():
    """主函数"""
    print_banner()

    # 检查配置
    has_config = ConfigManager.config_exists()

    while True:
        print_menu()
        choice = input("\n请选择操作 [1-4]: ").strip()

        if choice == "1":
            # 启动客户端
            asyncio.run(start_client())
            break

        elif choice == "2":
            # 修改配置
            ConfigManager.update_config_interactive()

        elif choice == "3":
            # 查看识别码
            if not has_config:
                print("\n请先启动客户端以生成识别码")
            else:
                client = WebSocketClient()
                print(f"\n客户端识别码: {client.get_client_id()}")

        elif choice == "4":
            # 退出
            print("\n再见!")
            sys.exit(0)

        else:
            print("\n无效的选择，请重新输入")


if __name__ == "__main__":
    main()
