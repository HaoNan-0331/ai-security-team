"""
邮件网关配置向导

首次使用时运行此脚本进行配置
"""

import os
import sys
import getpass
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import config_manager, whitelist_manager


def clear_screen():
    """清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """打印标题"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           AI Security Team - 邮件网关配置向导                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")


def step1_welcome():
    """步骤1: 欢迎信息"""
    print_header()
    print("此向导将帮助您配置邮件网关，让orchestrator能够收发邮件。\n")
    print("配置内容:")
    print("  1. 邮箱账户配置 (QQ邮箱)")
    print("  2. 发件人白名单")
    print("  3. 轮询设置\n")

    input("按 Enter 键继续...")
    clear_screen()


def step2_email_config():
    """步骤2: 邮箱配置"""
    print_header()
    print("【步骤 1/3】邮箱配置\n")
    print("请准备以下信息:")
    print("  - QQ邮箱地址 (如: 123456789@qq.com)")
    print("  - QQ邮箱授权码 (非QQ密码，需在邮箱设置中生成)")
    print()

    email_address = input("请输入QQ邮箱地址: ").strip()
    if not email_address or "@" not in email_address:
        print("错误: 无效的邮箱地址")
        return None

    print()
    print("提示: 授权码需要在 QQ邮箱 → 设置 → 账户 → POP3/IMAP/SMTP 服务 中生成")
    auth_code = getpass.getpass("请输入QQ邮箱授权码 (输入时不显示): ").strip()
    if not auth_code:
        print("错误: 授权码不能为空")
        return None

    display_name = input("请输入发件人显示名称 [AI Security Team]: ").strip()
    if not display_name:
        display_name = "AI Security Team"

    print()
    print("请设置一个主密码，用于加密存储邮箱授权码。")
    print("请妥善保管此密码，丢失后无法恢复邮箱配置。")
    master_password = getpass.getpass("请输入主密码: ").strip()
    if not master_password:
        print("错误: 主密码不能为空")
        return None

    confirm_password = getpass.getpass("请再次输入主密码确认: ").strip()
    if master_password != confirm_password:
        print("错误: 两次密码不一致")
        return None

    # 保存配置
    try:
        config_manager.setup_email(
            email_address=email_address,
            auth_code=auth_code,
            master_password=master_password,
            display_name=display_name,
        )
        print("\n✓ 邮箱配置保存成功!")
        return master_password
    except Exception as e:
        print(f"\n✗ 配置保存失败: {e}")
        return None


def step3_whitelist():
    """步骤3: 白名单配置"""
    print_header()
    print("【步骤 2/3】发件人白名单配置\n")
    print("只有白名单中的发件人发送的邮件才会被处理。")
    print("建议至少添加一个管理员邮箱。\n")

    while True:
        print("\n当前白名单:")
        senders = whitelist_manager.get_all_senders()
        if senders:
            for i, sender in enumerate(senders, 1):
                print(f"  {i}. {sender['name']} <{sender['email']}> - {sender['role']}")
        else:
            print("  (空)")

        print("\n选项:")
        print("  1. 添加管理员")
        print("  2. 添加操作员")
        print("  3. 添加观察者")
        print("  4. 删除发件人")
        print("  0. 完成配置")

        choice = input("\n请选择 [0-4]: ").strip()

        if choice == "0":
            break
        elif choice in ["1", "2", "3"]:
            role_map = {"1": "admin", "2": "operator", "3": "viewer"}
            role = role_map[choice]

            email = input("请输入邮箱地址: ").strip()
            if not email or "@" not in email:
                print("错误: 无效的邮箱地址")
                continue

            name = input("请输入姓名: ").strip()
            desc = input("请输入描述 (可选): ").strip()

            if whitelist_manager.add_sender(email, name, desc, role):
                print(f"✓ 已添加: {name} <{email}>")
            else:
                print("✗ 添加失败 (可能已存在)")
        elif choice == "4":
            if not senders:
                print("白名单为空")
                continue
            try:
                idx = int(input("请输入要删除的序号: ").strip()) - 1
                if 0 <= idx < len(senders):
                    removed = senders[idx]
                    if whitelist_manager.remove_sender(removed["email"]):
                        print(f"✓ 已删除: {removed['email']}")
                    else:
                        print("✗ 删除失败")
                else:
                    print("错误: 无效的序号")
            except ValueError:
                print("错误: 请输入数字")


def step4_polling():
    """步骤4: 轮询设置"""
    print_header()
    print("【步骤 3/3】轮询设置\n")

    current = config_manager.get_polling_config()
    print(f"当前轮询间隔: {current.get('interval', 60)} 秒\n")

    try:
        interval = input("请输入轮询间隔（秒）[60]: ").strip()
        if interval:
            interval = int(interval)
            if interval < 10:
                print("警告: 间隔太短可能导致服务器拒绝，已设置为最小值 10 秒")
                interval = 10
            config_manager.set_polling_interval(interval)
            print(f"✓ 轮询间隔已设置为 {interval} 秒")
    except ValueError:
        print("使用默认值 60 秒")


def step5_complete(master_password):
    """步骤5: 完成"""
    print_header()
    print("【配置完成】\n")
    print("邮箱配置信息:")
    email_config = config_manager.get_email_config(master_password)
    if email_config:
        print(f"  邮箱地址: {email_config['address']}")
        print(f"  显示名称: {config_manager.get_display_name()}")
        print(f"  SMTP服务器: {email_config['smtp_server']}:{email_config['smtp_port']}")
        print(f"  IMAP服务器: {email_config['imap_server']}:{email_config['imap_port']}")

    print("\n白名单发件人:")
    for sender in whitelist_manager.get_all_senders():
        print(f"  - {sender['name']} <{sender['email']}> ({sender['role']})")

    print(f"\n轮询间隔: {config_manager.get_polling_config().get('interval', 60)} 秒")

    print("""
╔═══════════════════════════════════════════════════════════════╗
║                        使用说明                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Python代码中使用:                                            ║
║                                                               ║
║    from email_gateway import EmailGateway                     ║
║                                                               ║
║    gateway = EmailGateway(master_password="your_password")    ║
║                                                               ║
║    # 发送邮件                                                 ║
║    gateway.send_email(to=["admin@example.com"],               ║
║                       subject="安全报告",                      ║
║                       content="...")                          ║
║                                                               ║
║    # 检查邮件                                                 ║
║    emails = gateway.check_startup_emails()                    ║
║                                                               ║
║    # 启动轮询监听                                             ║
║    gateway.start_polling()                                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")
    print("\n请妥善保管您的主密码!")


def main():
    """主函数"""
    try:
        step1_welcome()

        master_password = step2_email_config()
        if not master_password:
            print("\n配置已取消")
            return

        clear_screen()
        step3_whitelist()

        clear_screen()
        step4_polling()

        clear_screen()
        step5_complete(master_password)

    except KeyboardInterrupt:
        print("\n\n配置已取消")
    except Exception as e:
        print(f"\n配置过程出错: {e}")


if __name__ == "__main__":
    main()
