#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询上元信安防火墙系统日志和安全策略
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from asg_api_client import ASGApiClient


def query_firewall_logs(client: ASGApiClient, days: int = 7):
    """
    查询防火墙系统日志

    Args:
        client: ASG API客户端
        days: 查询天数，默认7天
    """
    print(f"\n{'='*60}")
    print(f"查询近{days}天防火墙系统日志")
    print(f"{'='*60}\n")

    # 时间类型映射
    time_type_map = {
        1: "one_day",    # 最近24小时
        7: "one_week",   # 最近7天
        30: "one_month", # 最近30天
        90: "three_month" # 最近90天
    }

    time_type = time_type_map.get(days, "one_week")

    # 先查询日志时间轴，获取总体统计信息
    timeline_params = {
        'module': 'filter',
        'sid': '1',
        'page': 1,
        'pageSize': 10,
        'Time_type': time_type
    }

    timeline_result = client.request('GET', '/audit-timeline', params=timeline_params)

    if 'error' in timeline_result:
        print(f"查询日志时间轴失败: {timeline_result['error']}")
        return

    print("日志时间轴统计:")
    print(f"  - 总事件数: {timeline_result.get('event_count', 0)}")
    print(f"  - 是否跨天: {'是' if timeline_result.get('cross_day') == 1 else '否'}")
    print(f"  - 查询用时: {timeline_result.get('duration', 0)}秒")

    buckets = timeline_result.get('buckets', [])
    if buckets:
        print(f"\n  时间分段统计:")
        for bucket in buckets:
            count = bucket.get('total_count', 0)
            time_str = bucket.get('earliest_strftime', '')
            print(f"    - {time_str}: {count} 条")

    # 查询具体日志内容
    log_params = {
        'module': 'filter',
        'sid': '1',
        'page': 1,
        'pageSize': 100,  # 每页100条
        'Time_type': time_type
    }

    log_result = client.request('GET', '/audit-log', params=log_params)

    if 'error' in log_result:
        print(f"\n查询日志失败: {log_result['error']}")
        return

    logs = log_result.get('data', [])
    total = log_result.get('total', 0)

    print(f"\n日志详情 (共 {total} 条, 显示前 {min(100, len(logs))} 条):")
    print(f"{'-'*60}")

    if not logs:
        print("  暂无日志记录")
    else:
        for log in logs:
            print(f"\n  时间: {log.get('create_at', 'N/A')}")
            print(f"  源IP: {log.get('srcip', 'N/A')}:{log.get('srcport', 'N/A')} -> "
                  f"目的IP: {log.get('dstip', 'N/A')}:{log.get('dstport', 'N/A')}")
            print(f"  协议: {log.get('protocol', 'N/A')}")
            print(f"  接口: 入{log.get('ininterface', 'N/A')} -> 出{log.get('outinterface', 'N/A')}")
            print(f"  动作: {log.get('action', 'N/A')}")
            print(f"  策略ID: {log.get('fwpolicyid', 'N/A')}")
            print(f"  日志级别: {log.get('level', 'N/A')}")
            content = log.get('content', '')
            if content:
                # 限制内容长度
                if len(content) > 80:
                    content = content[:80] + '...'
                print(f"  内容: {content}")
            print(f"  {'-'*60}")

    return log_result


def query_security_policies(client: ASGApiClient):
    """
    查询安全策略

    Args:
        client: ASG API客户端
    """
    print(f"\n{'='*60}")
    print("查询安全策略")
    print(f"{'='*60}\n")

    # 获取IPv4策略
    policies_result = client.get_policies(protocol="1", vrf="vrf0", page=1, page_size=100)

    if 'error' in policies_result:
        print(f"查询安全策略失败: {policies_result['error']}")
        return

    policies = policies_result.get('data', [])
    total = policies_result.get('total', 0)

    print(f"安全策略列表 (共 {total} 条):")
    print(f"{'-'*60}")

    if not policies:
        print("  暂无安全策略")
    else:
        # 表头
        print(f"  {'ID':<6} {'名称':<20} {'源':<15} {'目的':<15} {'服务':<10} {'动作':<10} {'启用':<6}")
        print(f"  {'-'*90}")

        for policy in policies:
            policy_id = policy.get('id', 'N/A')
            name = policy.get('name', '')
            sip = policy.get('sip', 'any')
            dip = policy.get('dip', 'any')
            service = policy.get('service', 'any')
            action = 'PERMIT' if policy.get('mode') == '1' else 'DENY'
            enable = '是' if policy.get('enable') == '1' else '否'

            # 截断过长字段
            sip_display = sip[:12] + '...' if len(sip) > 12 else sip
            dip_display = dip[:12] + '...' if len(dip) > 12 else dip

            print(f"  {policy_id:<6} {name:<20} {sip_display:<15} {dip_display:<15} "
                  f"{service:<10} {action:<10} {enable:<6}")

    return policies_result


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python query_logs.py <host> <token> [days]")
        print("\n示例:")
        print("  python query_logs.py https://192.168.10.249 YOUR_TOKEN 7")
        print("\n参数说明:")
        print("  host  - 防火墙IP地址，如 https://192.168.10.249 或 http://192.168.10.249")
        print("  token - 认证Token")
        print("  days  - 查询天数，默认7天")
        sys.exit(1)

    host = sys.argv[1]
    token = sys.argv[2]
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 7

    # 确保host格式正确
    if not host.startswith('http://') and not host.startswith('https://'):
        host = 'https://' + host

    print(f"\n连接上元信安防火墙...")
    print(f"  地址: {host}")
    print(f"  Token: {token[:10]}...")  # 只显示前10个字符

    # 创建客户端
    client = ASGApiClient(host, token, verify_ssl=False)

    # 测试连接
    test_result = client.get_policies(page=1, page_size=1)
    if 'error' in test_result and '连接失败' in test_result['error']:
        print(f"\n连接失败: {test_result['error']}")
        print("\n请检查:")
        print("  1. 防火墙IP地址是否正确")
        print("  2. 是否使用正确的协议 (http/https)")
        print("  3. Token是否正确且未过期")
        sys.exit(1)

    print("  连接成功!\n")

    # 查询防火墙日志
    query_firewall_logs(client, days)

    # 查询安全策略
    query_security_policies(client)

    print(f"\n{'='*60}")
    print("查询完成!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
