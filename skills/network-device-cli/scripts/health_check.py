#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备健康检查和巡检工具
支持自动化巡检和健康评分
使用显式连接参数
"""

import sys
import argparse
import getpass
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))


class HealthChecker:
    """设备健康检查器"""

    def __init__(self, host: str, username: str, password: str,
                 vendor: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.vendor = vendor.lower()
        self.port = port

        # 导入对应的执行器
        if self.vendor == 'h3c':
            from h3c_executor import H3CExecutor
            self.executor_class = H3CExecutor
        elif self.vendor == 'huawei':
            from huawei_executor import HuaweiExecutor
            self.executor_class = HuaweiExecutor
        elif self.vendor == 'cisco':
            from cisco_executor import CiscoExecutor
            self.executor_class = CiscoExecutor
        elif self.vendor == 'ruijie':
            from ruijie_executor import RuijieExecutor
            self.executor_class = RuijieExecutor
        else:
            raise ValueError(f"不支持的厂商: {vendor}")

        self.hostname = self.host.replace('.', '-')
        self.check_results: Dict[str, Any] = {}
        self.score = 100
        self.issues: List[Dict[str, str]] = []

    def _get_cpu_command(self) -> str:
        """获取CPU检查命令"""
        if self.vendor in ['h3c', 'huawei']:
            return 'display cpu-usage'
        else:
            return 'show processes cpu'

    def _get_memory_command(self) -> str:
        """获取内存检查命令"""
        if self.vendor in ['h3c', 'huawei']:
            return 'display memory-usage'
        else:
            return 'show memory statistics'

    def _get_interface_command(self) -> str:
        """获取接口检查命令"""
        if self.vendor in ['h3c', 'huawei']:
            return 'display interface brief'
        else:
            return 'show ip interface brief'

    def _get_log_command(self) -> str:
        """获取日志检查命令"""
        if self.vendor in ['h3c', 'huawei']:
            return 'display logbuffer'
        else:
            return 'show logging'

    def _parse_cpu_usage(self, output: str) -> float:
        """解析CPU使用率"""
        try:
            match = re.search(r'(\d+)%', output)
            if match:
                return float(match.group(1))
            return 0.0
        except Exception:
            return 0.0

    def _parse_memory_usage(self, output: str) -> Dict[str, Any]:
        """解析内存使用情况"""
        try:
            if self.vendor in ['h3c', 'huawei']:
                total_match = re.search(r'Total.*?(\d+)', output)
                used_match = re.search(r'Used.*?(\d+)', output)

                if total_match and used_match:
                    total = int(total_match.group(1))
                    used = int(used_match.group(1))
                    usage_percent = (used / total) * 100 if total > 0 else 0

                    return {
                        'total': total,
                        'used': used,
                        'free': total - used,
                        'usage_percent': usage_percent
                    }

            # Cisco/Ruijie格式
            match = re.search(r'Processor.*?(\d+).*?(\d+).*?(\d+)', output)
            if match:
                total = int(match.group(1))
                used = int(match.group(2))
                free = int(match.group(3))
                usage_percent = (used / total) * 100 if total > 0 else 0

                return {
                    'total': total,
                    'used': used,
                    'free': free,
                    'usage_percent': usage_percent
                }

            return {'total': 0, 'used': 0, 'free': 0, 'usage_percent': 0}

        except Exception:
            return {'total': 0, 'used': 0, 'free': 0, 'usage_percent': 0}

    def _check_log_errors(self, output: str) -> List[Dict[str, str]]:
        """检查日志中的错误和告警"""
        errors = []
        error_keywords = ['error', 'failed', 'down', 'loss', 'timeout',
                         'critical', 'emergency', 'alert']

        try:
            lines = output.split('\n')
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in error_keywords):
                    errors.append({
                        'message': line.strip()[:100],
                        'level': 'high' if 'error' in line_lower or 'critical' in line_lower else 'medium'
                    })

        except Exception:
            pass

        return errors

    def check_cpu_memory(self) -> Dict[str, Any]:
        """检查CPU和内存使用率"""
        print("[INFO] 检查CPU和内存使用率...")

        cpu_result = {'usage': 0, 'status': 'unknown'}
        memory_result = {'usage_percent': 0, 'status': 'unknown'}

        try:
            # 创建执行器并连接
            executor = self.executor_class(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )

            if not executor.connect():
                self.check_results['cpu'] = {'error': '连接失败'}
                self.check_results['memory'] = {'error': '连接失败'}
                return {'cpu': {'error': '连接失败'}, 'memory': {'error': '连接失败'}}

            # 检查CPU
            cpu_output = executor.execute_command(self._get_cpu_command(), timeout=30)
            if cpu_output['success']:
                cpu_usage = self._parse_cpu_usage(cpu_output['output'])
                cpu_result['usage'] = cpu_usage

                if cpu_usage > 90:
                    cpu_result['status'] = 'critical'
                    cpu_result['message'] = f'CPU使用率过高: {cpu_usage}%'
                    self.score -= 20
                    self.issues.append({
                        'category': 'CPU',
                        'severity': 'critical',
                        'message': cpu_result['message']
                    })
                elif cpu_usage > 70:
                    cpu_result['status'] = 'warning'
                    cpu_result['message'] = f'CPU使用率较高: {cpu_usage}%'
                    self.score -= 10
                    self.issues.append({
                        'category': 'CPU',
                        'severity': 'warning',
                        'message': cpu_result['message']
                    })
                else:
                    cpu_result['status'] = 'ok'
                    cpu_result['message'] = f'CPU使用率正常: {cpu_usage}%'

            # 检查内存
            mem_output = executor.execute_command(self._get_memory_command(), timeout=30)
            if mem_output['success']:
                memory_info = self._parse_memory_usage(mem_output['output'])
                memory_result = memory_info
                mem_usage = memory_info.get('usage_percent', 0)

                if mem_usage > 90:
                    memory_result['status'] = 'critical'
                    memory_result['message'] = f'内存使用率过高: {mem_usage:.1f}%'
                    self.score -= 20
                    self.issues.append({
                        'category': 'Memory',
                        'severity': 'critical',
                        'message': memory_result['message']
                    })
                elif mem_usage > 80:
                    memory_result['status'] = 'warning'
                    memory_result['message'] = f'内存使用率较高: {mem_usage:.1f}%'
                    self.score -= 10
                    self.issues.append({
                        'category': 'Memory',
                        'severity': 'warning',
                        'message': memory_result['message']
                    })
                else:
                    memory_result['status'] = 'ok'
                    memory_result['message'] = f'内存使用率正常: {mem_usage:.1f}%'

            executor.disconnect()

            self.check_results['cpu'] = cpu_result
            self.check_results['memory'] = memory_result

            return {'cpu': cpu_result, 'memory': memory_result}

        except Exception as e:
            self.check_results['cpu'] = {'error': str(e)}
            self.check_results['memory'] = {'error': str(e)}
            return {'cpu': {'error': str(e)}, 'memory': {'error': str(e)}}

    def check_interfaces(self) -> Dict[str, Any]:
        """检查接口状态"""
        print("[INFO] 检查接口状态...")

        try:
            executor = self.executor_class(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )

            if not executor.connect():
                self.check_results['interfaces'] = {'error': '连接失败'}
                return {'error': '连接失败'}

            output = executor.execute_command(self._get_interface_command(), timeout=30)
            executor.disconnect()

            if not output['success']:
                self.check_results['interfaces'] = {'error': output.get('error')}
                return {'error': output.get('error')}

            # 简单统计
            lines = output['output'].split('\n')
            up_count = 0
            down_count = 0

            for line in lines:
                if 'up' in line.lower():
                    up_count += 1
                elif 'down' in line.lower() and 'administratively' not in line.lower():
                    down_count += 1

            result = {
                'up_count': up_count,
                'down_count': down_count,
                'total_count': up_count + down_count
            }

            if down_count > 0:
                result['status'] = 'warning'
                result['message'] = f'有 {down_count} 个接口处于down状态'
                self.score -= 5 * min(down_count, 5)
                self.issues.append({
                    'category': 'Interface',
                    'severity': 'warning',
                    'message': result['message']
                })
            else:
                result['status'] = 'ok'
                result['message'] = '所有接口状态正常'

            self.check_results['interfaces'] = result
            return result

        except Exception as e:
            self.check_results['interfaces'] = {'error': str(e)}
            return {'error': str(e)}

    def check_logs(self) -> Dict[str, Any]:
        """检查日志中的错误和告警"""
        print("[INFO] 检查系统日志...")

        try:
            executor = self.executor_class(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port
            )

            if not executor.connect():
                self.check_results['logs'] = {'error': '连接失败'}
                return {'error': '连接失败'}

            output = executor.execute_command(self._get_log_command(), timeout=30)
            executor.disconnect()

            if not output['success']:
                self.check_results['logs'] = {'error': output.get('error')}
                return {'error': output.get('error')}

            errors = self._check_log_errors(output['output'])

            if errors:
                critical_count = sum(1 for e in errors if e['level'] == 'high')
                if critical_count > 5:
                    self.score -= 15
                    status = 'critical'
                elif critical_count > 0:
                    self.score -= 5
                    status = 'warning'
                else:
                    self.score -= 2
                    status = 'info'

                self.issues.extend(errors[:10])

                result = {
                    'status': status,
                    'error_count': len(errors),
                    'errors': errors[:10]
                }
            else:
                result = {
                    'status': 'ok',
                    'message': '日志中无明显错误',
                    'error_count': 0
                }

            self.check_results['logs'] = result
            return result

        except Exception as e:
            self.check_results['logs'] = {'error': str(e)}
            return {'error': str(e)}

    def run_full_check(self) -> Dict[str, Any]:
        """运行完整的健康检查"""
        print(f"\n[INFO] 设备健康检查: {self.hostname}")
        print(f"[INFO] 厂商: {self.vendor}")

        start_time = datetime.now()

        # 运行各项检查
        self.check_cpu_memory()
        self.check_interfaces()
        self.check_logs()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 汇总结果
        self.check_results['summary'] = {
            'hostname': self.hostname,
            'host': self.host,
            'vendor': self.vendor,
            'score': max(0, self.score),
            'issue_count': len(self.issues),
            'duration': f'{duration:.2f}s',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 确定总体状态
        if self.score >= 90:
            overall_status = 'excellent'
        elif self.score >= 70:
            overall_status = 'good'
        elif self.score >= 50:
            overall_status = 'warning'
        else:
            overall_status = 'critical'

        self.check_results['summary']['status'] = overall_status

        return self.check_results

    def display_results(self):
        """显示检查结果"""
        print("\n")
        print("=" * 60)

        # 健康评分
        score = self.check_results['summary']['score']
        status = self.check_results['summary']['status'].upper()

        print(f"健康评分: {score}/100 ({status})")
        print(f"检查时间: {self.check_results['summary']['timestamp']}")
        print(f"检查耗时: {self.check_results['summary']['duration']}")

        # CPU和内存状态
        if 'cpu' in self.check_results and 'memory' in self.check_results:
            cpu = self.check_results['cpu']
            memory = self.check_results['memory']

            print("\n资源使用:")
            if 'usage' in cpu:
                print(f"  CPU: {cpu['usage']}% ({cpu.get('status', 'unknown')})")
            if 'usage_percent' in memory:
                print(f"  内存: {memory['usage_percent']:.1f}% ({memory.get('status', 'unknown')})")

        # 接口状态
        if 'interfaces' in self.check_results:
            iface = self.check_results['interfaces']
            if 'up_count' in iface:
                print(f"\n接口状态:")
                print(f"  UP: {iface['up_count']}, DOWN: {iface['down_count']}")

        # 问题列表
        if self.issues:
            print(f"\n发现的问题 ({len(self.issues)}):")
            for issue in self.issues[:20]:
                print(f"  [{issue['severity'].upper()}] {issue['category']}: {issue['message']}")

        print("=" * 60)

    def save_report(self, output_file: str, format: str = 'json'):
        """保存检查报告"""
        try:
            if format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.check_results, f, indent=2, ensure_ascii=False)

            elif format == 'md':
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# 设备健康检查报告\n\n")
                    f.write(f"**设备**: {self.hostname}\n")
                    f.write(f"**IP**: {self.host}\n")
                    f.write(f"**时间**: {self.check_results['summary']['timestamp']}\n")
                    f.write(f"**评分**: {self.check_results['summary']['score']}/100\n")
                    f.write(f"**状态**: {self.check_results['summary']['status']}\n\n")

                    if self.issues:
                        f.write(f"## 发现的问题 ({len(self.issues)})\n\n")
                        for issue in self.issues:
                            f.write(f"- [{issue['severity'].upper()}] {issue['category']}: {issue['message']}\n")

            print(f"[OK] 报告已保存到: {output_file}")

        except Exception as e:
            print(f"[ERROR] 保存报告失败: {str(e)}")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="设备健康检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # H3C设备健康检查
  python health_check.py --host 192.168.1.1 --username admin --vendor h3c

  # 生成JSON报告
  python health_check.py --host 192.168.1.1 --username admin --vendor huawei --format json --output report.json

  # 生成Markdown报告
  python health_check.py --host 192.168.1.1 --username admin --vendor cisco --format md --output report.md
        """
    )

    # 连接参数（必填）
    parser.add_argument("--host", required=True, help="设备IP地址")
    parser.add_argument("--username", required=True, help="用户名")
    parser.add_argument("--password", help="密码（不指定则交互式输入）")
    parser.add_argument("--vendor", required=True,
                       choices=['h3c', 'huawei', 'cisco', 'ruijie'],
                       help="设备厂商")
    parser.add_argument("--port", type=int, default=22, help="SSH端口")

    # 输出参数
    parser.add_argument("--format", choices=['json', 'md'], default='json',
                       help="报告格式")
    parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    # 获取密码
    password = args.password
    if not password:
        password = getpass.getpass("密码: ")

    # 创建健康检查器
    try:
        checker = HealthChecker(
            host=args.host,
            username=args.username,
            password=password,
            vendor=args.vendor,
            port=args.port
        )

        # 运行完整检查
        results = checker.run_full_check()

        # 显示结果
        checker.display_results()

        # 保存报告
        if args.output:
            checker.save_report(args.output, args.format)

        sys.exit(0 if results['summary']['score'] >= 70 else 1)

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
