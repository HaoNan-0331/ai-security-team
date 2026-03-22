#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASG防火墙API客户端全功能验证脚本
验证asg_api_client.py中的所有功能方法
"""

import sys
import json
import io
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加scripts目录到路径
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from asg_api_client import ASGApiClient


class ASGFunctionVerifier:
    """ASG防火墙API功能验证器"""

    def __init__(self, host: str, token: str):
        """初始化验证器"""
        self.client = ASGApiClient(host, token, verify_ssl=False)
        self.results = []
        self.test_start_time = datetime.now()

    def log_test(self, module: str, func_name: str, success: bool, result: dict = None, error: str = None):
        """记录测试结果"""
        self.results.append({
            'module': module,
            'function': func_name,
            'success': success,
            'result': str(result)[:500] if result else None,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {module}.{func_name}")
        if error:
            print(f"      错误: {error}")

    def verify_method(self, module: str, func_name: str, func, *args, **kwargs) -> bool:
        """验证单个方法"""
        try:
            result = func(*args, **kwargs)
            success = 'error' not in result
            self.log_test(module, func_name, success, result)
            return success
        except Exception as e:
            self.log_test(module, func_name, False, error=str(e))
            return False

    def verify_all(self):
        """验证所有功能"""
        print("=" * 70)
        print("ASG防火墙API客户端全功能验证")
        print(f"目标: {self.client.host}")
        print(f"开始时间: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # ==================== 1. 网络接口模块 ====================
        print("\n[1/15] 网络接口模块")
        print("-" * 40)

        self.verify_method("网络接口", "get_vlan_interfaces", self.client.get_vlan_interfaces)
        self.verify_method("网络接口", "get_gre_tunnels", self.client.get_gre_tunnels)
        self.verify_method("网络接口", "get_loopback_interfaces", self.client.get_loopback_interfaces)
        self.verify_method("网络接口", "get_bypass_config", self.client.get_bypass_config)
        self.verify_method("网络接口", "get_port_mirror", self.client.get_port_mirror)

        # ==================== 2. 路由配置模块 ====================
        print("\n[2/15] 路由配置模块")
        print("-" * 40)

        self.verify_method("路由配置", "get_static_routes", self.client.get_static_routes)
        self.verify_method("路由配置", "get_static_routes_ipv6", self.client.get_static_routes_ipv6)
        self.verify_method("路由配置", "get_pbr_routes", self.client.get_pbr_routes)
        self.verify_method("路由配置", "get_pbr_routes_ipv6", self.client.get_pbr_routes_ipv6)
        self.verify_method("路由配置", "get_isp_routes", self.client.get_isp_routes)

        # ==================== 3. SSL VPN模块 ====================
        print("\n[3/15] SSL VPN模块")
        print("-" * 40)

        self.verify_method("SSL VPN", "get_sslvpn_config", self.client.get_sslvpn_config)
        self.verify_method("SSL VPN", "get_sslvpn_monitor", self.client.get_sslvpn_monitor)
        self.verify_method("SSL VPN", "get_sslvpn_userbind", self.client.get_sslvpn_userbind)
        self.verify_method("SSL VPN", "get_sslvpn_tunn_if", self.client.get_sslvpn_tunn_if)

        # ==================== 4. 策略管理模块 ====================
        print("\n[4/15] 策略管理模块")
        print("-" * 40)

        self.verify_method("策略管理", "get_policies", self.client.get_policies)
        self.verify_method("策略管理", "get_policies (IPv6)",
                          lambda: self.client.get_policies(protocol="2"))

        # ==================== 5. 黑名单模块 ====================
        print("\n[5/15] 黑名单模块")
        print("-" * 40)

        self.verify_method("黑名单", "get_ip_blacklist", self.client.get_ip_blacklist)
        self.verify_method("黑名单", "get_ip_blacklist (IPv6)",
                          lambda: self.client.get_ip_blacklist(ip_type="2"))
        self.verify_method("黑名单", "get_domain_blacklist", self.client.get_domain_blacklist)

        # ==================== 6. 威胁情报模块 ====================
        print("\n[6/15] 威胁情报模块")
        print("-" * 40)

        self.verify_method("威胁情报", "get_threat_intelligence_switch",
                          self.client.get_threat_intelligence_switch)
        self.verify_method("威胁情报", "get_reliable_config", self.client.get_reliable_config)
        self.verify_method("威胁情报", "get_intelligence_level", self.client.get_intelligence_level)
        self.verify_method("威胁情报", "get_cloud_intelligence_config",
                          self.client.get_cloud_intelligence_config)
        self.verify_method("威胁情报", "check_online_status", self.client.check_online_status)
        self.verify_method("威胁情报", "get_intelligence_database", self.client.get_intelligence_database)
        self.verify_method("威胁情报", "check_update", self.client.check_update)
        self.verify_method("威胁情报", "get_ioc_lasttime", self.client.get_ioc_lasttime)
        self.verify_method("威胁情报", "get_custom_intelligence", self.client.get_custom_intelligence)

        # ==================== 7. 入侵防护模块 ====================
        print("\n[7/15] 入侵防护模块")
        print("-" * 40)

        self.verify_method("入侵防护", "get_ips_templates", self.client.get_ips_templates)
        self.verify_method("入侵防护", "get_ips_sets", self.client.get_ips_sets)

        # ==================== 8. 病毒防护模块 ====================
        print("\n[8/15] 病毒防护模块")
        print("-" * 40)

        self.verify_method("病毒防护", "get_av_templates", self.client.get_av_templates)
        self.verify_method("病毒防护", "get_av_filetypes", self.client.get_av_filetypes)

        # ==================== 9. EDR联动模块 ====================
        print("\n[9/15] EDR联动模块")
        print("-" * 40)

        self.verify_method("EDR联动", "get_edr_center", self.client.get_edr_center)
        self.verify_method("EDR联动", "get_edr_install", self.client.get_edr_install)
        self.verify_method("EDR联动", "get_edr_policies", self.client.get_edr_policies)
        self.verify_method("EDR联动", "get_edr_https", self.client.get_edr_https)
        self.verify_method("EDR联动", "get_edr_users", self.client.get_edr_users)

        # ==================== 10. 引流策略模块 ====================
        print("\n[10/15] 引流策略模块")
        print("-" * 40)

        self.verify_method("引流策略", "get_divert_policies", self.client.get_divert_policies)

        # ==================== 11. 镜像策略模块 ====================
        print("\n[11/15] 镜像策略模块")
        print("-" * 40)

        self.verify_method("镜像策略", "get_mirror_policies", self.client.get_mirror_policies)

        # ==================== 12. 用户认证模块 ====================
        print("\n[12/15] 用户认证模块")
        print("-" * 40)

        self.verify_method("用户认证", "get_auth_users", self.client.get_auth_users)
        self.verify_method("用户认证", "get_snmp_sync", self.client.get_snmp_sync)
        self.verify_method("用户认证", "get_wechat_config", self.client.get_wechat_config)

        # ==================== 13. 日志与监控模块 ====================
        print("\n[13/15] 日志与监控模块")
        print("-" * 40)

        self.verify_method("日志监控", "get_syslog_config", self.client.get_syslog_config)
        self.verify_method("日志监控", "get_syslog_docking", self.client.get_syslog_docking)

        # ==================== 14. 系统管理模块 ====================
        print("\n[14/15] 系统管理模块")
        print("-" * 40)

        self.verify_method("系统管理", "get_sdwan_config", self.client.get_sdwan_config)
        self.verify_method("系统管理", "get_backup_version", self.client.get_backup_version)
        self.verify_method("系统管理", "get_update_log", self.client.get_update_log)
        self.verify_method("系统管理", "get_auto_update_config", self.client.get_auto_update_config)

        # ==================== 15. 地址对象模块 ====================
        print("\n[15/15] 地址对象模块")
        print("-" * 40)

        self.verify_method("地址对象", "get_addresses", self.client.get_addresses)
        self.verify_method("地址对象", "get_address_groups", self.client.get_address_groups)

        # ==================== 验证总结 ====================
        self.print_summary()

    def print_summary(self):
        """打印验证总结"""
        print("\n" + "=" * 70)
        print("验证总结")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed

        print(f"总计: {total} 个方法")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {passed/total*100:.1f}%")

        # 按模块分组统计
        module_stats = {}
        for r in self.results:
            module = r['module']
            if module not in module_stats:
                module_stats[module] = {'total': 0, 'passed': 0, 'funcs': []}
            module_stats[module]['total'] += 1
            if r['success']:
                module_stats[module]['passed'] += 1
            module_stats[module]['funcs'].append(r['function'])

        print("\n按模块统计:")
        for module, stats in sorted(module_stats.items()):
            rate = stats['passed'] / stats['total'] * 100
            status = "OK" if stats['passed'] == stats['total'] else "FAIL"
            print(f"  [{status}] {module}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")

        # 列出所有验证的方法
        print("\n验证的方法列表:")
        for module, stats in sorted(module_stats.items()):
            print(f"\n  {module}:")
            for func in stats['funcs']:
                print(f"    - {func}")

        # 失败方法详情
        if failed > 0:
            print("\n失败方法详情:")
            for r in self.results:
                if not r['success']:
                    error_msg = r.get('error', '未知错误')
                    print(f"  [{r['module']}] {r['function']}: {error_msg}")

        # 保存验证结果
        self.save_results()

        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

    def save_results(self):
        """保存验证结果到文件"""
        results_dir = Path(__file__).parent.parent / 'logs'
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f'verify_results_{timestamp}.json'

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_start': self.test_start_time.isoformat(),
                'test_end': datetime.now().isoformat(),
                'host': self.client.host,
                'results': self.results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n验证结果已保存到: {results_file}")


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python verify_all_functions.py <host> <token>")
        print("示例: python verify_all_functions.py https://192.168.31.249 YOUR_TOKEN")
        sys.exit(1)

    host = sys.argv[1]
    token = sys.argv[2]

    verifier = ASGFunctionVerifier(host, token)
    verifier.verify_all()


if __name__ == '__main__':
    main()
