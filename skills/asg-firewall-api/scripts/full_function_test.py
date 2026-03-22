#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASG防火墙全功能测试脚本
为每个功能模块生成测试数据并执行完整测试
"""

import sys
import json
import io
from datetime import datetime
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加scripts目录到路径
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from asg_api_client import ASGApiClient


class FullFunctionTester:
    """ASG防火墙全功能测试器"""

    def __init__(self, host: str, token: str):
        """初始化测试器"""
        self.client = ASGApiClient(host, token, verify_ssl=False)
        self.results = []
        self.created_objects = []
        self.test_start_time = datetime.now()
        self.timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    def log_test(self, module: str, operation: str, success: bool, result: dict = None, error: str = None):
        """记录测试结果"""
        is_api_error = result and 'code' in result and result['code'] not in ['0', None, '']
        success = success and not is_api_error

        self.results.append({
            'module': module,
            'operation': operation,
            'success': success,
            'result': str(result)[:500] if result else None,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {module} - {operation}")
        if error:
            print(f"      错误: {error}")
        if result and 'code' in result and result['code'] not in ['0', None, '']:
            print(f"      API错误: code={result.get('code')}, str={result.get('str')}")
        return success

    def run_test(self, module: str, operation: str, func, *args, **kwargs):
        """运行单个测试"""
        try:
            result = func(*args, **kwargs)
            success = 'error' not in result
            return self.log_test(module, operation, success, result), result
        except Exception as e:
            self.log_test(module, operation, False, error=str(e))
            return False, {'error': str(e)}

    def test_all_functions(self):
        """测试所有功能"""
        print("=" * 70)
        print("ASG防火墙全功能测试")
        print(f"目标: {self.client.host}")
        print(f"测试时间: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试ID: {self.timestamp}")
        print("=" * 70)

        # ==================== 1. 网络接口模块 ====================
        print("\n[1/15] 网络接口模块测试")
        print("-" * 40)

        # 测试环回接口
        loopback_data = {
            'interface_name': f'lo{self.timestamp[-3:]}',
            'ip': '127.0.0.1',
            'netmask': '255.0.0.0'
        }
        success, result = self.run_test("网络接口", "添加环回接口",
                                       self.client.add_loopback_interface, loopback_data)
        if success and result.get('code', '0') == '0':
            self.created_objects.append(('loopback', {'interface_name': loopback_data['interface_name']}))

        self.run_test("网络接口", "查询环回接口", self.client.get_loopback_interfaces)

        # 测试VLAN接口
        vlan_data = {
            'interface_name': f'vlan{self.timestamp[-3:]}',
            'vlan_id': self.timestamp[-3:],
            'ip': '192.168.254.1',
            'netmask': '255.255.255.0'
        }
        self.run_test("网络接口", "添加VLAN接口", self.client.add_vlan_interface, vlan_data)

        # ==================== 2. 路由配置模块 ====================
        print("\n[2/15] 路由配置模块测试")
        print("-" * 40)

        # 测试静态路由
        route_data = {
            'vrf': 'vrf0',
            'dst_ip': '192.168.253.0/24',
            'nh_type': '0',
            'nh_ip': '192.168.10.254',
            'distance': '1'
        }
        success, result = self.run_test("路由配置", "添加静态路由",
                                       self.client.add_static_route, route_data)
        if success and result.get('code', '0') == '0':
            self.created_objects.append(('route', route_data))

        self.run_test("路由配置", "查询静态路由", self.client.get_static_routes)

        # ==================== 3. SSL VPN模块 ====================
        print("\n[3/15] SSL VPN模块测试")
        print("-" * 40)

        self.run_test("SSL VPN", "查询SSL VPN配置", self.client.get_sslvpn_config)
        self.run_test("SSL VPN", "查询SSL VPN监控", self.client.get_sslvpn_monitor)
        self.run_test("SSL VPN", "查询SSL VPN用户绑定", self.client.get_sslvpn_userbind)
        self.run_test("SSL VPN", "查询SSL VPN接口配置", self.client.get_sslvpn_tunn_if)

        # 测试SSL VPN配置修改 - 只测试空路由
        sslvpn_config = {
            'gw': '0.0.0.0/0',
            'route_items': ''
        }
        self.run_test("SSL VPN", "修改SSL VPN配置", self.client.update_sslvpn_config, sslvpn_config)

        # ==================== 4. 策略管理模块 ====================
        print("\n[4/15] 策略管理模块测试")
        print("-" * 40)

        # 测试简化策略添加 - 使用唯一的IP避免冲突
        test_src_ip = f'192.168.{int(self.timestamp[-4:]) % 250}.{int(self.timestamp[-2:]) % 250}'
        test_dst_ip = f'192.168.{int(self.timestamp[-4:]) % 250}.{(int(self.timestamp[-2:]) + 1) % 250}'
        self.run_test("策略管理", "添加策略(简化方法)",
                     self.client.add_policy_simple,
                     test_src_ip, test_dst_ip,
                     action='deny',
                     description=f'测试策略{self.timestamp}')

        # 查询策略
        self.run_test("策略管理", "查询策略列表", self.client.get_policies)

        # 测试策略状态修改 - 使用现有策略ID
        # 首先获取策略列表找到有效ID
        policies = self.client.get_policies()
        valid_policy_id = '1'
        if policies and 'data' in policies and len(policies['data']) > 0:
            valid_policy_id = policies['data'][0]['id']

        policy_state_data = {
            'id': valid_policy_id,
            'protocol': '1',
            'vrf': 'vrf0',
            'enable': '1'
        }
        self.run_test("策略管理", "修改策略状态", self.client.update_policy_state, policy_state_data)

        # ==================== 5. 黑名单模块 ====================
        print("\n[5/15] 黑名单模块测试")
        print("-" * 40)

        # 测试IP黑名单
        ip_blacklist_data = {
            'ip_type': '1',
            'ip': '10.254.254.254',
            'age': '3600',
            'enable': '1'
        }
        success, result = self.run_test("黑名单", "添加IP黑名单",
                                       self.client.add_ip_blacklist, ip_blacklist_data)
        if success and result.get('code', '0') == '0':
            self.created_objects.append(('blacklist', ip_blacklist_data))

        self.run_test("黑名单", "查询IP黑名单", self.client.get_ip_blacklist)

        # 测试域名黑名单
        domain_blacklist_data = {
            'domain': f'test{self.timestamp}.example.com',
            'age': '3600',
            'enable': '1'
        }
        success, result = self.run_test("黑名单", "添加域名黑名单",
                                       self.client.add_domain_blacklist, domain_blacklist_data)
        if success and result.get('code', '0') == '0':
            self.created_objects.append(('domain_blacklist', domain_blacklist_data))

        self.run_test("黑名单", "查询域名黑名单", self.client.get_domain_blacklist)

        # ==================== 6. 威胁情报模块 ====================
        print("\n[6/15] 威胁情报模块测试")
        print("-" * 40)

        # 获取当前配置
        self.run_test("威胁情报", "查询威胁情报开关", self.client.get_threat_intelligence_switch)
        self.run_test("威胁情报", "查询信誉值配置", self.client.get_reliable_config)
        self.run_test("威胁情报", "查询风险级别配置", self.client.get_intelligence_level)
        self.run_test("威胁情报", "查询云端情报配置", self.client.get_cloud_intelligence_config)
        self.run_test("威胁情报", "检查在线状态", self.client.check_online_status)
        self.run_test("威胁情报", "查询情报库升级历史", self.client.get_intelligence_database)
        self.run_test("威胁情报", "查询情报库情况", self.client.check_update)
        self.run_test("威胁情报", "查询最近升级时间", self.client.get_ioc_lasttime)

        # 测试自定义威胁情报 - 添加content和信誉值参数
        custom_intel_data = {
            'source': 'local_coo_def',
            'name': f'test_intel_{self.timestamp}',
            'type': '1',
            'value': '1.1.1.1',
            'reliable': '50',
            'content': 'test',
            'desc': '测试威胁情报'
        }
        self.run_test("威胁情报", "添加自定义威胁情报",
                     self.client.add_custom_intelligence, custom_intel_data)

        self.run_test("威胁情报", "查询自定义威胁情报", self.client.get_custom_intelligence)

        # 测试威胁情报开关修改
        switch_data = {'ip_switch': '0', 'domain_switch': '0', 'url_switch': '0', 'filehash_switch': '0'}
        self.run_test("威胁情报", "修改威胁情报开关",
                     self.client.update_threat_intelligence_switch, switch_data)

        # ==================== 7. 入侵防护模块 ====================
        print("\n[7/15] 入侵防护模块测试")
        print("-" * 40)

        self.run_test("入侵防护", "查询IPS模板", self.client.get_ips_templates)
        self.run_test("入侵防护", "查询IPS事件集", self.client.get_ips_sets)

        # 测试IPS模板 - 添加事件集名称参数
        ips_template_data = {
            'name': f'test_ips_{self.timestamp}',
            'desc': '测试IPS模板',
            'protect_level': '1',
            'type': '0',
            'set_name': 'All'
        }
        self.run_test("入侵防护", "添加IPS模板", self.client.add_ips_template, ips_template_data)

        # ==================== 8. 病毒防护模块 ====================
        print("\n[8/15] 病毒防护模块测试")
        print("-" * 40)

        self.run_test("病毒防护", "查询病毒防护模板", self.client.get_av_templates)
        self.run_test("病毒防护", "查询扫描文件类型", self.client.get_av_filetypes)

        # 测试病毒防护模板
        av_template_data = {
            'name': f'test_av_{self.timestamp}',
            'desc': 'test',
            'enable': '0',
            'action': '0',
            'http': '0',
            'ftp': '1',
            'smtp': '1',
            'imap': '1',
            'pop3': '0',
            'apt_enable': '1'
        }
        success, result = self.run_test("病毒防护", "添加病毒防护模板",
                                       self.client.add_av_template, av_template_data)
        if success and result.get('code', '0') == '0':
            self.created_objects.append(('av_template', {'name': av_template_data['name']}))

        # 测试文件类型 - 必须以*.开头
        filetype_data = {'pattern': f'*.t{self.timestamp[-3:]}'}
        self.run_test("病毒防护", "添加扫描文件类型",
                     self.client.add_av_filetype, filetype_data)

        # ==================== 9. EDR联动模块 ====================
        print("\n[9/15] EDR联动模块测试")
        print("-" * 40)

        self.run_test("EDR联动", "查询EDR中心配置", self.client.get_edr_center)
        self.run_test("EDR联动", "查询EDR安装路径", self.client.get_edr_install)
        self.run_test("EDR联动", "查询EDR联动策略", self.client.get_edr_policies)
        self.run_test("EDR联动", "查询EDR HTTPS状态", self.client.get_edr_https)
        self.run_test("EDR联动", "查询EDR资产列表", self.client.get_edr_users)

        # 测试EDR中心配置修改
        edr_center_data = {
            'central': 'test.local',
            'tenant_admin': 'admin',
            'auth_type': 'none',
            'asset_sync': '0',
            'enable': '0'
        }
        self.run_test("EDR联动", "修改EDR中心配置",
                     self.client.update_edr_center, edr_center_data)

        # ==================== 10. 引流策略模块 ====================
        print("\n[10/15] 引流策略模块测试")
        print("-" * 40)

        self.run_test("引流策略", "查询引流策略", self.client.get_divert_policies)

        # 测试引流策略 - 添加服务参数
        divert_policy_data = {
            'id': f'{self.timestamp[-4:]}',
            'name': f'test_divert_{self.timestamp}',
            'sip': 'any',
            'dip': '192.168.251.0/24',
            'sev': 'any',
            'action': '1',
            'enable': '1'
        }
        self.run_test("引流策略", "添加引流策略",
                     self.client.add_divert_policy, divert_policy_data)

        # ==================== 11. 镜像策略模块 ====================
        print("\n[11/15] 镜像策略模块测试")
        print("-" * 40)

        self.run_test("镜像策略", "查询镜像策略", self.client.get_mirror_policies)

        # 测试镜像策略 - 移除接口参数
        mirror_policy_data = {
            'id': f'{self.timestamp[-4:]}',
            'name': f'test_mirror_{self.timestamp}',
            'sip': 'any',
            'dip': 'any',
            'mirror_ip': '192.168.1.100',
            'enable': '1'
        }
        self.run_test("镜像策略", "添加镜像策略",
                     self.client.add_mirror_policy, mirror_policy_data)

        # ==================== 12. 用户认证模块 ====================
        print("\n[12/15] 用户认证模块测试")
        print("-" * 40)

        self.run_test("用户认证", "查询用户列表", self.client.get_auth_users)
        self.run_test("用户认证", "查询SNMP同步", self.client.get_snmp_sync)
        self.run_test("用户认证", "查询微信认证配置", self.client.get_wechat_config)

        # 测试用户添加 - 添加更多必填参数
        user_data = {
            'name': f'testuser{self.timestamp[-4:]}',
            'show_name': f'测试用户{self.timestamp[-4:]}',
            'password': 'Test1234',
            'type': 'password',
            'bind_type': 'none',
            'enable': '1',
            'readonly': '0'
        }
        self.run_test("用户认证", "添加用户", self.client.add_auth_user, user_data)

        # 测试微信认证配置
        wechat_data = {
            'cfg_enable': '0',
            'force_interval': '0',
            'kick_interval': '10',
            'user_type': '1'
        }
        self.run_test("用户认证", "修改微信认证配置",
                     self.client.update_wechat_config, wechat_data)

        # ==================== 13. 日志与监控模块 ====================
        print("\n[13/15] 日志与监控模块测试")
        print("-" * 40)

        self.run_test("日志监控", "查询Syslog配置", self.client.get_syslog_config)
        self.run_test("日志监控", "查询Syslog对接标准", self.client.get_syslog_docking)

        # 测试Syslog配置
        syslog_data = {
            'syslog_addr': '192.168.1.200',
            'syslog_port': '514',
            'syslog_tls': '0'
        }
        self.run_test("日志监控", "修改Syslog配置",
                     self.client.update_syslog_config, syslog_data)

        # ==================== 14. 系统管理模块 ====================
        print("\n[14/15] 系统管理模块测试")
        print("-" * 40)

        self.run_test("系统管理", "查询SD-WAN配置", self.client.get_sdwan_config)
        self.run_test("系统管理", "查询固件版本", self.client.get_backup_version)
        self.run_test("系统管理", "查询升级历史", self.client.get_update_log)
        self.run_test("系统管理", "查询自动升级配置", self.client.get_auto_update_config)

        # 测试SD-WAN配置 - 移除接口参数
        sdwan_data = {
            'enable': '0',
            'cloud_domain': '',
            'cloud_ip': '::',
            'cloud_port': '9070'
        }
        self.run_test("系统管理", "修改SD-WAN配置",
                     self.client.update_sdwan_config, sdwan_data)

        # ==================== 15. 地址对象模块 ====================
        print("\n[15/15] 地址对象模块测试")
        print("-" * 40)

        self.run_test("地址对象", "查询地址对象", self.client.get_addresses)
        self.run_test("地址对象", "查询地址组对象", self.client.get_address_groups)

        # 测试地址对象
        address_data = {
            'name': f'test_addr_{self.timestamp}',
            'desc': '测试地址对象',
            'type': 0,
            'item': [
                {'host': '8.8.8.8', 'type': 0},
                {'net': '8.8.4.0/24', 'type': 1}
            ]
        }
        success, result = self.run_test("地址对象", "添加地址对象",
                                       self.client.add_address, address_data)
        if success and result.get('code', '0') == '0':
            self.created_objects.append(('address', {'name': address_data['name']}))

        # 测试地址组
        address_group_data = {
            'name': f'test_group_{self.timestamp}',
            'desc': '测试地址组',
            'member': ['any']
        }
        success, result = self.run_test("地址对象", "添加地址组",
                                       self.client.add_address_group, address_group_data)
        if success and result.get('code', '0') == '0':
            self.created_objects.append(('address_group', {'name': address_group_data['name']}))

        # ==================== 清理测试数据 ====================
        print("\n[清理] 清理测试创建的对象")
        print("-" * 40)
        self.cleanup()

        # ==================== 测试总结 ====================
        self.print_summary()

    def cleanup(self):
        """清理测试创建的对象"""
        for obj_type, obj_data in self.created_objects:
            try:
                if obj_type == 'address':
                    print(f"清理地址对象: {obj_data.get('name')}")
                    self.client.delete_address(obj_data)
                elif obj_type == 'address_group':
                    print(f"清理地址组: {obj_data.get('name')}")
                    self.client.delete_address_group(obj_data)
                elif obj_type == 'blacklist':
                    print(f"清理IP黑名单: {obj_data.get('ip')}")
                    self.client.delete_ip_blacklist(obj_data)
                elif obj_type == 'domain_blacklist':
                    print(f"清理域名黑名单: {obj_data.get('domain')}")
                    self.client.delete_domain_blacklist(obj_data)
                elif obj_type == 'av_template':
                    print(f"清理病毒防护模板: {obj_data.get('name')}")
                    self.client.delete_av_template(obj_data)
                elif obj_type == 'route':
                    print(f"清理静态路由")
                    self.client.delete_static_route(obj_data)
                elif obj_type == 'loopback':
                    print(f"清理环回接口: {obj_data.get('interface_name')}")
                    self.client.delete_loopback_interface(obj_data)
            except Exception as e:
                print(f"清理失败: {e}")

        self.created_objects.clear()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed

        print(f"总计: {total} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {passed/total*100:.1f}%")

        # 按模块分组统计
        module_stats = {}
        for r in self.results:
            module = r['module']
            if module not in module_stats:
                module_stats[module] = {'total': 0, 'passed': 0, 'operations': []}
            module_stats[module]['total'] += 1
            if r['success']:
                module_stats[module]['passed'] += 1
            module_stats[module]['operations'].append(r['operation'])

        print("\n按模块统计:")
        for module, stats in sorted(module_stats.items()):
            rate = stats['passed'] / stats['total'] * 100
            status = "OK" if stats['passed'] == stats['total'] else "FAIL"
            print(f"  [{status}] {module}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")

        # 失败测试详情
        if failed > 0:
            print("\n失败测试详情:")
            for r in self.results:
                if not r['success']:
                    error_msg = r.get('error') or r.get('result', '未知错误')[:100]
                    print(f"  [{r['module']}] {r['operation']}: {error_msg}")

        # 保存测试结果
        self.save_results()

        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

    def save_results(self):
        """保存测试结果到文件"""
        results_dir = Path(__file__).parent.parent / 'logs'
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = results_dir / f'full_test_results_{timestamp}.json'

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_id': self.timestamp,
                'test_start': self.test_start_time.isoformat(),
                'test_end': datetime.now().isoformat(),
                'host': self.client.host,
                'results': self.results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n测试结果已保存到: {results_file}")


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python full_function_test.py <host> <token>")
        print("示例: python full_function_test.py https://192.168.31.249 YOUR_TOKEN")
        sys.exit(1)

    host = sys.argv[1]
    token = sys.argv[2]

    tester = FullFunctionTester(host, token)
    tester.test_all_functions()


if __name__ == '__main__':
    main()
