"""
客户端配置管理
使用JSON文件存储配置
"""
import json
import os
import sys
import re
import ipaddress
import uuid
import platform
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional


def get_app_dir():
    """获取应用数据目录（兼容打包和开发环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境：使用系统用户目录
        if sys.platform == "win32":
            # Windows: %APPDATA%\command_executor
            app_dir = Path(os.environ.get("APPDATA", "")) / "command_executor"
        else:
            # Linux/macOS: ~/.config/command_executor
            app_dir = Path.home() / ".config" / "command_executor"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir
    else:
        # 开发环境：使用 client 目录
        return Path(__file__).parent


def get_device_fingerprint() -> str:
    """
    获取设备指纹（用于唯一标识设备）

    Returns:
        str: 设备指纹字符串
    """
    try:
        if sys.platform == "win32":
            # Windows: 使用 Machine GUID (注册表)
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography")
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            return f"win_{machine_guid}"
        elif sys.platform == "darwin":
            # macOS: 使用硬件 UUID
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "IOPlatformUUID" in line:
                        uuid_str = line.split('"')[-2]
                        return f"mac_{uuid_str}"
            # 备用方案: 使用主机名
            return f"mac_{platform.node()}"
        else:
            # Linux: 尝试读取 machine-id
            machine_id_files = [
                "/etc/machine-id",
                "/var/lib/dbus/machine-id",
                "/etc/hostid"
            ]
            for file_path in machine_id_files:
                if Path(file_path).exists():
                    with open(file_path, "r") as f:
                        machine_id = f.read().strip()
                        if machine_id:
                            return f"linux_{machine_id}"
            # 备用方案: 使用主机名
            return f"linux_{platform.node()}"
    except Exception:
        # 最终备用方案: 主机名 + MAC 地址
        hostname = platform.node()
        try:
            mac = uuid.getnode()
            return f"fallback_{hostname}_{mac}"
        except Exception:
            return f"fallback_{hostname}"


@dataclass
class ClientConfig:
    """客户端配置"""
    server_host: str
    server_port: int
    api_port: int = 8080
    use_tls: bool = False
    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5


class ConfigValidator:
    """配置校验器"""

    @staticmethod
    def validate_ip_address(value: str) -> tuple[bool, str]:
        """
        校验IP地址或主机名

        返回: (是否有效, 错误信息)
        """
        value = value.strip()

        if not value:
            return False, "值不能为空"

        # 检查是否为 IPv4 地址
        try:
            ip = ipaddress.IPv4Address(value)
            return True, ""
        except ipaddress.AddressValueError:
            pass

        # 检查是否为合法的主机名
        # 主机名规则: 字母、数字、连字符，以字母或数字开头和结尾
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if re.match(hostname_pattern, value):
            if len(value) <= 253:  # 主机名最大长度
                return True, ""
            else:
                return False, "主机名过长（最大253字符）"

        # 检查是否为 localhost
        if value.lower() == "localhost":
            return True, ""

        return False, "请输入有效的IP地址（如: 192.168.1.1）或主机名"

    @staticmethod
    def validate_port(value: str) -> tuple[bool, str]:
        """
        校验端口号

        返回: (是否有效, 错误信息)
        """
        value = value.strip()

        if not value:
            return False, "端口号不能为空"

        try:
            port = int(value)
            if 1 <= port <= 65535:
                return True, ""
            else:
                return False, "端口号必须在 1-65535 之间"
        except ValueError:
            return False, "端口号必须是数字"

    @staticmethod
    def validate_yes_no(value: str) -> tuple[bool, str]:
        """
        校验是/否输入

        返回: (是否有效, 错误信息)
        """
        value = value.strip().lower()
        if value in ("y", "n", "yes", "no"):
            return True, ""
        return False, "请输入 y/n 或 yes/no"


class ConfigManager:
    """配置管理器"""

    CONFIG_FILE = "client_config.json"

    @classmethod
    def get_config_path(cls) -> Path:
        """获取配置文件路径"""
        # 在应用目录下创建配置文件
        return get_app_dir() / cls.CONFIG_FILE

    @classmethod
    def load_config(cls) -> ClientConfig:
        """加载配置"""
        config_path = cls.get_config_path()

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ClientConfig(**data)
        else:
            # 返回默认配置
            return ClientConfig(
                server_host="127.0.0.1",
                server_port=8765,
                use_tls=False
            )

    @classmethod
    def save_config(cls, config: ClientConfig):
        """保存配置"""
        config_path = cls.get_config_path()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, indent=2, ensure_ascii=False)

    @classmethod
    def config_exists(cls) -> bool:
        """检查配置是否存在"""
        return cls.get_config_path().exists()

    @classmethod
    def input_ip_address(cls, prompt: str) -> str:
        """输入IP地址（带校验）"""
        while True:
            value = input(prompt).strip()
            is_valid, error_msg = ConfigValidator.validate_ip_address(value)
            if is_valid:
                # 将 localhost 转换为 127.0.0.1
                if value.lower() == "localhost":
                    return "127.0.0.1"
                return value
            print(f"  ❌ {error_msg}")

    @classmethod
    def input_port(cls, prompt: str) -> int:
        """输入端口号（带校验）"""
        while True:
            value = input(prompt).strip()
            is_valid, error_msg = ConfigValidator.validate_port(value)
            if is_valid:
                return int(value)
            print(f"  ❌ {error_msg}")

    @classmethod
    def input_yes_no(cls, prompt: str) -> bool:
        """输入是/否（带校验）"""
        while True:
            value = input(prompt).strip()
            is_valid, error_msg = ConfigValidator.validate_yes_no(value)
            if is_valid:
                return value.lower() in ("y", "yes")
            print(f"  ❌ {error_msg}")

    @classmethod
    def create_config_interactive(cls) -> ClientConfig:
        """交互式创建配置"""
        print("\n=== 客户端首次配置 ===")
        print("请输入服务端连接信息:")
        print("提示: 输入 'q' 可返回主菜单\n")

        # 输入服务端IP地址
        while True:
            server_host_input = input("服务端IP地址: ").strip()
            if server_host_input.lower() == 'q':
                print("\n已取消配置")
                return None
            is_valid, error_msg = ConfigValidator.validate_ip_address(server_host_input)
            if is_valid:
                # 将 localhost 转换为 127.0.0.1
                if server_host_input.lower() == "localhost":
                    server_host = "127.0.0.1"
                else:
                    server_host = server_host_input
                break
            print(f"  ❌ {error_msg}")

        # 输入端口号
        while True:
            server_port_input = input("服务端端口: ").strip()
            if server_port_input.lower() == 'q':
                print("\n已取消配置")
                return None
            is_valid, error_msg = ConfigValidator.validate_port(server_port_input)
            if is_valid:
                server_port = int(server_port_input)
                break
            print(f"  ❌ {error_msg}")

        # 输入是否使用TLS
        while True:
            use_tls_input = input("使用TLS加密? (y/n): ").strip()
            if use_tls_input.lower() == 'q':
                print("\n已取消配置")
                return None
            is_valid, error_msg = ConfigValidator.validate_yes_no(use_tls_input)
            if is_valid:
                use_tls = use_tls_input.lower() in ("y", "yes")
                break
            print(f"  ❌ {error_msg}")

        config = ClientConfig(
            server_host=server_host,
            server_port=server_port,
            use_tls=use_tls
        )

        cls.save_config(config)
        print("\n✅ 配置已保存!")
        return config

    @classmethod
    def update_config_interactive(cls):
        """交互式更新配置"""
        while True:
            print("\n=== 修改客户端配置 ===")
            current = cls.load_config()
            print(f"当前配置:")
            print(f"  服务端地址: {current.server_host}:{current.server_port}")
            print(f"  使用TLS: {'是' if current.use_tls else '否'}")
            print()

            print("请选择要修改的项:")
            print("1. 修改服务端地址")
            print("2. 修改端口号")
            print("3. 修改TLS设置")
            print("0. 返回主菜单")

            choice = input("\n请选择 [0-3]: ").strip()

            if choice == "0":
                print("\n返回主菜单")
                return

            elif choice == "1":
                # 修改服务端地址
                print("\n--- 修改服务端地址 ---")
                print(f"当前值: {current.server_host}")
                print("提示: 输入 'q' 取消修改")

                while True:
                    new_host = cls.input_ip_address("新地址: ")
                    if new_host.lower() == 'q':
                        print("  已取消")
                        break
                    is_valid, _ = ConfigValidator.validate_ip_address(new_host)
                    if is_valid:
                        if new_host.lower() == "localhost":
                            new_host = "127.0.0.1"
                        current.server_host = new_host
                        cls.save_config(current)
                        print(f"✅ 服务端地址已更新为: {current.server_host}")
                        break

            elif choice == "2":
                # 修改端口号
                print("\n--- 修改端口号 ---")
                print(f"当前值: {current.server_port}")
                print("提示: 输入 'q' 取消修改")

                while True:
                    new_port_input = input("新端口: ").strip()
                    if new_port_input.lower() == 'q':
                        print("  已取消")
                        break
                    is_valid, error_msg = ConfigValidator.validate_port(new_port_input)
                    if is_valid:
                        current.server_port = int(new_port_input)
                        cls.save_config(current)
                        print(f"✅ 端口号已更新为: {current.server_port}")
                        break
                    print(f"  ❌ {error_msg}")

            elif choice == "3":
                # 修改TLS设置
                print("\n--- 修改TLS设置 ---")
                current_tls = current.use_tls
                print(f"当前值: {'是' if current_tls else '否'}")
                print("提示: 输入 'q' 取消修改")

                while True:
                    new_tls_input = input("启用TLS加密? (y/n): ").strip()
                    if new_tls_input.lower() == 'q':
                        print("  已取消")
                        break
                    is_valid, error_msg = ConfigValidator.validate_yes_no(new_tls_input)
                    if is_valid:
                        current.use_tls = new_tls_input.lower() in ("y", "yes")
                        cls.save_config(current)
                        print(f"✅ TLS设置已更新为: {'是' if current.use_tls else '否'}")
                        break
                    print(f"  ❌ {error_msg}")

            else:
                print("\n❌ 无效的选择，请重新输入")
