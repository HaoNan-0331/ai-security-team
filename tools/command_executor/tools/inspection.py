#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows服务器巡检脚本
通过分布式命令执行系统API连接服务端，对Windows服务器执行巡检任务并生成Markdown报告
"""

import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
import ssl
import base64
import requests
from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SSLAdapter(HTTPAdapter):
    """自定义SSL适配器，支持旧版TLS协议和不安全加密套件"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        # 设置最低版本为TLS 1.0（已弃用但为了兼容性）
        try:
            ctx.minimum_version = ssl.TLSVersion.TLSv1
        except:
            pass
        # 启用旧版服务器连接支持
        ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
        # 设置默认密码套件为默认值
        ctx.set_ciphers('DEFAULT@SECLEVEL=0')
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


class InspectionClient:
    """分布式命令执行系统API客户端"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.timeout = 60
        # 创建带有SSL适配器的session
        self.session = requests.Session()
        self.session.mount('https://', SSLAdapter())

    def login(self) -> bool:
        """登录获取Token"""
        try:
            url = f"{self.base_url}/api/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            response = self.session.post(
                url,
                json=payload,
                verify=False,
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token") or data.get("token")
                if self.token:
                    print(f"[+] 登录成功，Token: {self.token[:20]}...")
                    return True
            print(f"[-] 登录失败: {response.status_code} - {response.text}")
            return False
        except RequestException as e:
            print(f"[-] 登录请求异常: {e}")
            return False

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_online_clients(self) -> list:
        """获取在线客户端列表"""
        try:
            url = f"{self.base_url}/api/clients/online"
            response = self.session.get(
                url,
                headers=self._get_headers(),
                verify=False,
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                # 适配不同的响应格式
                clients = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(clients, list):
                    return clients
            print(f"[-] 获取在线设备失败: {response.status_code}")
            return []
        except RequestException as e:
            print(f"[-] 获取在线设备异常: {e}")
            return []

    def execute_local_command(self, client_id: str, command: str) -> Optional[str]:
        """执行本地命令，返回session_id"""
        try:
            url = f"{self.base_url}/api/local/execute"
            payload = {
                "client_id": client_id,
                "command": command,
                "timeout": self.timeout,
                "encoding": "gbk"
            }
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                verify=False,
                timeout=self.timeout + 10
            )
            if response.status_code == 200:
                data = response.json()
                session_id = data.get("session_id")
                return session_id
            else:
                print(f"[-] 执行命令失败: {response.status_code}")
            return None
        except Exception as e:
            print(f"[-] 执行命令异常: {e}")
            return None

    def get_session_result(self, session_id: str, max_wait: int = 120) -> dict:
        """轮询获取命令执行结果"""
        url = f"{self.base_url}/api/sessions/{session_id}"
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    verify=False,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    result = response.json()

                    # 根据API规范，response_data不为空表示执行完成
                    if result.get("response_data") is not None:
                        if result.get("success"):
                            return {
                                "status": "success",
                                "output": result["response_data"].get("stdout", ""),
                                "stderr": result["response_data"].get("stderr", ""),
                                "exit_code": result["response_data"].get("exit_code", 0)
                            }
                        else:
                            return {
                                "status": "failed",
                                "error": result.get("error_message", "执行失败"),
                                "output": result.get("response_data", {}).get("stdout", "")
                            }

                time.sleep(2)
            except RequestException:
                time.sleep(2)

        return {"status": "timeout", "error": "执行超时"}


class ConfigParser:
    """巡检配置解析器"""

    # 分类定义
    CATEGORIES = {
        "01": "基础信息检查",
        "02": "补丁检查",
        "03": "账户安全",
        "04": "网络/进程/服务",
        "05": "文件系统",
        "06": "审核配置",
        "07": "注册表安全",
        "08": "日志分析"
    }

    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.items: list = []
        self._load_config()

    def _load_config(self):
        """加载并解析XML配置"""
        try:
            tree = ET.parse(self.xml_path)
            root = tree.getroot()

            for item in root.findall("item"):
                item_data = {
                    "id": item.get("id", ""),
                    "name": item.get("name", ""),
                    "risk": item.get("risk", "低风险"),
                    "description": item.findtext("description", ""),
                    "detection_logic": item.findtext("detection_logic", ""),
                    "commands": {}
                }

                # 解析命令（优先PowerShell）
                for cmd in item.findall("command"):
                    cmd_type = cmd.get("type", "cmd")
                    item_data["commands"][cmd_type] = cmd.text or ""

                self.items.append(item_data)

            print(f"[+] 已加载 {len(self.items)} 个巡检项")
        except Exception as e:
            print(f"[-] 加载配置文件失败: {e}")
            self.items = []

    def get_categories(self) -> dict:
        """获取所有分类及其项目数量"""
        categories = {}
        for item in self.items:
            cat_id = item["id"][:2]
            if cat_id not in categories:
                categories[cat_id] = {"name": self.CATEGORIES.get(cat_id, "未知分类"), "count": 0, "items": []}
            categories[cat_id]["count"] += 1
            categories[cat_id]["items"].append(item)
        return categories

    def get_items_by_category(self, category_ids: list) -> list:
        """按分类ID获取巡检项"""
        return [item for item in self.items if item["id"][:2] in category_ids]

    def get_all_items(self) -> list:
        """获取所有巡检项"""
        return self.items


class ReportGenerator:
    """Markdown报告生成器"""

    def __init__(self):
        self.results: list = []
        self.start_time = datetime.now()

    def add_device_result(self, device_info: dict, inspection_results: list):
        """添加设备巡检结果"""
        self.results.append({
            "device": device_info,
            "results": inspection_results
        })

    def _escape_markdown(self, text: str) -> str:
        """转义Markdown特殊字符"""
        if not text:
            return ""
        # 转义反引号
        text = text.replace("`", "\\`")
        return text

    def generate_markdown(self) -> str:
        """生成Markdown报告内容"""
        lines = []

        # 报告头部
        lines.append("# Windows服务器巡检报告")
        lines.append("")
        lines.append(f"**生成时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**巡检设备数**: {len(self.results)}")

        # 统计总项目数
        total_items = sum(len(r["results"]) for r in self.results)
        lines.append(f"**巡检项目数**: {total_items}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 各设备巡检结果
        for idx, device_result in enumerate(self.results, 1):
            device = device_result["device"]
            results = device_result["results"]

            lines.append(f"## {idx}. {device.get('hostname', device.get('name', '未知设备'))}")
            lines.append("")
            lines.append(f"**客户端ID**: {device.get('client_id', device.get('id', '未知'))}")
            lines.append(f"**操作系统**: {device.get('os', device.get('os_type', '未知'))}")
            lines.append("")

            # 统计
            success_count = sum(1 for r in results if r.get("status") == "success")
            fail_count = len(results) - success_count
            high_risk_count = sum(1 for r in results if "高风险" in r.get("risk", ""))

            if success_count > 0 or fail_count > 0:
                lines.append(f"**执行统计**: 成功 {success_count} 项, 失败 {fail_count} 项, 高风险项 {high_risk_count} 个")
                lines.append("")

            # 各巡检项结果
            for r_idx, result in enumerate(results, 1):
                item_name = result.get("name", "未知巡检项")
                risk = result.get("risk", "低风险")

                lines.append(f"### {idx}.{r_idx} {item_name} [{risk}]")
                lines.append("")

                # 执行命令
                command = result.get("command", "")
                if command:
                    lines.append("**执行命令**:")
                    lines.append("")
                    lines.append("```")
                    # 截断过长的命令
                    if len(command) > 500:
                        command = command[:500] + "..."
                    lines.append(command)
                    lines.append("```")
                    lines.append("")

                # 执行结果
                lines.append("**执行结果**:")
                lines.append("")
                output = result.get("output", "")
                status = result.get("status", "unknown")

                if status != "success":
                    lines.append(f"执行状态: {status}")
                    error = result.get("error", "")
                    if error:
                        lines.append(f"错误信息: {error}")
                else:
                    lines.append("```")
                    # 截断过长的输出
                    if len(output) > 5000:
                        output = output[:5000] + "\n... (输出已截断)"
                    lines.append(output)
                    lines.append("```")

                lines.append("")
                lines.append("---")
                lines.append("")

        # 巡检汇总表
        lines.append("## 巡检汇总")
        lines.append("")
        lines.append("| 设备 | 成功项 | 失败项 | 高风险项 |")
        lines.append("|------|--------|--------|----------|")

        for device_result in self.results:
            device = device_result["device"]
            results = device_result["results"]

            hostname = device.get("hostname", device.get("name", "未知设备"))
            success = sum(1 for r in results if r.get("status") == "success")
            fail = len(results) - success
            high_risk = sum(1 for r in results if "高风险" in r.get("risk", ""))

            lines.append(f"| {hostname} | {success} | {fail} | {high_risk} |")

        lines.append("")

        return "\n".join(lines)

    def save_report(self, output_path: str) -> bool:
        """保存报告到文件"""
        try:
            content = self.generate_markdown()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"[-] 保存报告失败: {e}")
            return False


def prompt_server_info() -> tuple:
    """提示输入服务端信息"""
    print("\n" + "=" * 50)
    print("请输入分布式命令执行系统服务端信息")
    print("=" * 50)

    base_url = input("服务端地址 (例如 https://192.168.1.100:8080): ").strip()

    # 自动修正URL中的中文字符
    char_map = {
        "：": ":",  # 中文冒号
        "。": ".",  # 中文句号
        "，": ",",  # 中文逗号
        "／": "/",  # 中文斜杠
        "　": " ",  # 全角空格
    }
    for cn_char, en_char in char_map.items():
        base_url = base_url.replace(cn_char, en_char)

    # 移除多余空格
    base_url = base_url.replace(" ", "")

    if not base_url:
        print("[-] 服务端地址不能为空")
        return None, None, None

    username = input("用户名: ").strip()
    if not username:
        print("[-] 用户名不能为空")
        return None, None, None

    password = input("密码: ").strip()
    if not password:
        print("[-] 密码不能为空")
        return None, None, None

    return base_url, username, password


def select_clients(clients: list) -> list:
    """选择要巡检的设备"""
    if not clients:
        print("[-] 没有在线设备")
        return []

    print("\n" + "=" * 80)
    print("在线设备列表")
    print("=" * 80)
    print(f"{'序号':<6}{'客户端ID':<20}{'主机名':<25}{'操作系统':<25}{'最后在线时间':<20}")
    print("-" * 80)

    for idx, client in enumerate(clients, 1):
        client_id = client.get("client_id", client.get("id", "未知"))
        hostname = client.get("hostname", client.get("name", "未知"))[:22]
        os_type = client.get("os_type", client.get("os", "未知"))[:22]
        last_seen = client.get("last_seen", client.get("last_online", "未知"))
        if last_seen and len(last_seen) > 19:
            last_seen = last_seen[:19]

        print(f"[{idx:<4}]{client_id:<20}{hostname:<25}{os_type:<25}{last_seen:<20}")

    print("-" * 80)
    print(f"共 {len(clients)} 台设备在线")

    while True:
        choice = input("\n请选择设备（输入序号，多个用逗号分隔，输入 'all' 全选）: ").strip().lower()

        if choice == "all":
            print(f"[+] 已选择全部 {len(clients)} 台设备")
            return clients

        try:
            indices = [int(x.strip()) for x in choice.split(",")]
            selected = []
            for i in indices:
                if 1 <= i <= len(clients):
                    selected.append(clients[i - 1])
                else:
                    print(f"[-] 序号 {i} 超出范围")

            if selected:
                print(f"[+] 已选择 {len(selected)} 台设备")
                return selected
            else:
                print("[-] 未选择任何有效设备，请重新输入")
        except ValueError:
            print("[-] 输入格式错误，请重新输入")


def select_inspection_items(config_parser: ConfigParser) -> list:
    """选择巡检项目"""
    categories = config_parser.get_categories()

    print("\n" + "=" * 60)
    print("巡检项目分类")
    print("=" * 60)

    cat_list = sorted(categories.items())
    for idx, (cat_id, cat_info) in enumerate(cat_list, 1):
        print(f"[{idx}] {cat_id}-{cat_info['name']} ({cat_info['count']}项)")

    print("-" * 60)
    print(f"共 {len(config_parser.items)} 个巡检项")

    while True:
        choice = input("\n请选择分类（输入序号，多个用逗号分隔，输入 'all' 全选）: ").strip().lower()

        if choice == "all":
            items = config_parser.get_all_items()
            print(f"[+] 已选择全部 {len(items)} 个巡检项")
            return items

        try:
            indices = [int(x.strip()) for x in choice.split(",")]
            selected_cat_ids = []
            for i in indices:
                if 1 <= i <= len(cat_list):
                    selected_cat_ids.append(cat_list[i - 1][0])
                else:
                    print(f"[-] 序号 {i} 超出范围")

            if selected_cat_ids:
                items = config_parser.get_items_by_category(selected_cat_ids)
                print(f"[+] 已选择 {len(items)} 个巡检项")
                return items
            else:
                print("[-] 未选择任何有效分类，请重新输入")
        except ValueError:
            print("[-] 输入格式错误，请重新输入")


def run_inspection(client: InspectionClient, device: dict, items: list) -> list:
    """对单个设备执行巡检"""
    results = []
    client_id = device.get("client_id", device.get("id", ""))
    hostname = device.get("hostname", device.get("name", "未知设备"))

    print(f"\n[*] 开始巡检设备: {hostname} (共 {len(items)} 项)")

    for idx, item in enumerate(items, 1):
        item_name = item.get("name", "未知巡检项")
        print(f"  [{idx}/{len(items)}] {item_name}...", end=" ", flush=True)

        # 优先使用PowerShell命令，否则使用CMD命令
        ps_cmd = item.get("commands", {}).get("powershell")
        cmd_cmd = item.get("commands", {}).get("cmd")

        if ps_cmd:
            # PowerShell命令使用Base64编码避免引号转义问题
            # PowerShell需要UTF-16LE编码的Base64
            encoded_cmd = base64.b64encode(ps_cmd.encode('utf-16-le')).decode('ascii')
            command = f'powershell -ExecutionPolicy Bypass -EncodedCommand {encoded_cmd}'
        elif cmd_cmd:
            command = cmd_cmd
        else:
            command = ""

        if not command:
            print("跳过 (无命令)")
            results.append({
                "name": item_name,
                "risk": item.get("risk", "低风险"),
                "command": "",
                "status": "skipped",
                "output": "",
                "error": "无可用命令"
            })
            continue

        # 执行命令
        session_id = client.execute_local_command(client_id, command)

        if not session_id:
            print("失败 (无法创建会话)")
            results.append({
                "name": item_name,
                "risk": item.get("risk", "低风险"),
                "command": command,
                "status": "failed",
                "output": "",
                "error": "无法创建执行会话"
            })
            continue

        # 获取结果
        result = client.get_session_result(session_id)

        if result.get("status") == "success" or result.get("status") == "completed":
            output = result.get("output", result.get("result", result.get("stdout", "")))
            print("成功")
            results.append({
                "name": item_name,
                "risk": item.get("risk", "低风险"),
                "command": command,
                "status": "success",
                "output": output,
                "error": ""
            })
        else:
            error = result.get("error", result.get("stderr", "执行失败"))
            print(f"失败 ({error})")
            results.append({
                "name": item_name,
                "risk": item.get("risk", "低风险"),
                "command": command,
                "status": result.get("status", "failed"),
                "output": result.get("output", ""),
                "error": error
            })

    return results


def main():
    """主函数"""
    print("=" * 60)
    print("Windows服务器巡检工具")
    print("=" * 60)

    # 1. 获取服务端信息
    base_url, username, password = prompt_server_info()
    if not base_url:
        return

    # 2. 登录认证
    client = InspectionClient(base_url, username, password)
    if not client.login():
        print("[-] 登录失败，程序退出")
        return

    # 3. 获取在线设备
    print("\n[*] 正在获取在线设备列表...")
    online_clients = client.get_online_clients()

    if not online_clients:
        print("[-] 没有在线设备，程序退出")
        return

    # 4. 选择设备
    selected_devices = select_clients(online_clients)
    if not selected_devices:
        print("[-] 未选择任何设备，程序退出")
        return

    # 5. 加载巡检配置
    config_path = os.path.join(os.path.dirname(__file__), "config.xml")
    if not os.path.exists(config_path):
        print(f"[-] 配置文件不存在: {config_path}")
        return

    config_parser = ConfigParser(config_path)

    # 6. 选择巡检项
    selected_items = select_inspection_items(config_parser)
    if not selected_items:
        print("[-] 未选择任何巡检项，程序退出")
        return

    # 7. 执行巡检
    report = ReportGenerator()

    for device in selected_devices:
        results = run_inspection(client, device, selected_items)
        report.add_device_result(device, results)

    # 8. 生成报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"巡检报告_{timestamp}.md"
    report_dir = os.path.join(os.path.dirname(__file__), "reports")

    # 确保报告目录存在
    os.makedirs(report_dir, exist_ok=True)

    report_path = os.path.join(report_dir, report_filename)

    print("\n" + "=" * 60)
    print("[*] 正在生成巡检报告...")

    if report.save_report(report_path):
        print(f"[+] 报告已生成: {report_path}")
    else:
        print("[-] 报告生成失败")

    print("\n[+] 巡检完成!")


if __name__ == "__main__":
    main()
