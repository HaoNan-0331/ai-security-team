#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加上元信安防火墙安全策略（含地址对象创建）
"""

import sys
import json
from pathlib import Path

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from asg_api_client import ASGApiClient


def get_or_create_address_object(client: ASGApiClient, ip_addr: str, addr_type: str = "src"):
    """
    获取或创建地址对象

    Args:
        client: ASG API客户端
        ip_addr: IP地址
        addr_type: 地址类型（src=源地址，dst=目的地址）

    Returns:
        地址对象名称
    """
    # 生成地址对象名称（保持原始IP格式，带前缀）
    addr_name = f"{addr_type}_{ip_addr}"

    # 先查询现有地址对象
    print(f"检查地址对象: {addr_name}")
    existing_addrs = client.get_addresses()

    if 'error' in existing_addrs:
        print(f"查询地址对象失败: {existing_addrs['error']}")
        return None

    # 检查是否已存在
    for addr in existing_addrs.get('data', []):
        if addr.get('name') == addr_name:
            print(f"  [OK] 地址对象已存在")
            return addr_name

    # 创建新的地址对象
    print(f"  正在创建地址对象...")
    addr_data = {
        "name": addr_name,
        "desc": f"{addr_type == 'src' and '源地址' or '目的地址'}{ip_addr}",
        "type": 0,  # 0表示主机类型
        "item": [
            {
                "type": 0,  # 0表示主机
                "host": ip_addr
            }
        ]
    }

    result = client.add_address(addr_data)

    # 调试：打印原始响应
    print(f"  调试 - API响应: {json.dumps(result, ensure_ascii=False)}")

    if 'error' in result:
        print(f"  [X] 创建地址对象失败: {result['error']}")
        return None

    if 'code' in result and result['code'] != '0':
        print(f"  [X] 创建地址对象失败: {result.get('str', '未知错误')}")
        return None

    print(f"  [OK] 地址对象创建成功")
    return addr_name


def add_block_policy(client: ASGApiClient, src_ip: str, dst_ip: str, policy_id: str = None):
    """
    添加拒绝访问的安全策略

    Args:
        client: ASG API客户端
        src_ip: 源IP地址
        dst_ip: 目的IP地址
        policy_id: 策略ID，如果为None则自动获取下一个可用ID
    """
    print(f"\n{'='*60}")
    print("添加拒绝访问安全策略")
    print(f"{'='*60}\n")

    # 先创建或获取源地址对象
    print("步骤1: 处理源地址对象")
    src_addr_name = get_or_create_address_object(client, src_ip, "src")
    if src_addr_name is None:
        return False
    print()

    # 创建或获取目的地址对象
    print("步骤2: 处理目的地址对象")
    dst_addr_name = get_or_create_address_object(client, dst_ip, "dst")
    if dst_addr_name is None:
        return False
    print()

    # 如果没有指定策略ID，先查询现有策略以找到可用的ID
    if policy_id is None:
        print("步骤3: 获取可用的策略ID...")
        existing_policies = client.get_policies(protocol="1", vrf="vrf0", page=1, page_size=100)

        if 'error' in existing_policies:
            print(f"  查询现有策略失败: {existing_policies['error']}")
            return False

        existing_ids = []
        for policy in existing_policies.get('data', []):
            try:
                existing_ids.append(int(policy.get('id', 0)))
            except ValueError:
                pass

        # 找到下一个可用的ID（从1开始）
        policy_id = 1
        while policy_id in existing_ids:
            policy_id += 1

        print(f"  自动选择策略ID: {policy_id}")
    print()

    # 构造策略数据
    print("步骤4: 添加安全策略")
    policy_data = {
        "id": str(policy_id),
        "protocol": "1",          # IPv4
        "if_in": "any",           # 任意入接口
        "if_out": "any",          # 任意出接口
        "sip": src_addr_name,     # 源地址对象名称
        "dip": dst_addr_name,     # 目的地址对象名称
        "sev": "any",             # 任意服务
        "user": "any",            # 任意用户
        "app": "any",             # 任意应用
        "tr": "always",           # 始终
        "mode": "2",              # 2表示DENY（拒绝）
        "enable": "1",            # 启用
        "syslog": "1",            # 记录日志
        "log_level": "4"          # 日志级别：4-警示
    }

    print("  策略详情:")
    print(f"    策略ID: {policy_data['id']}")
    print(f"    源地址: {src_ip} (对象名: {src_addr_name})")
    print(f"    目的地址: {dst_ip} (对象名: {dst_addr_name})")
    print(f"    动作: 拒绝 (DENY)")
    print(f"    启用状态: 是")
    print(f"    记录日志: 是")
    print()

    # 添加策略
    result = client.add_policy(policy_data)

    # 调试：打印原始响应
    print(f"  调试 - API响应: {json.dumps(result, ensure_ascii=False)}")

    if 'error' in result:
        print(f"  [X] 添加策略失败: {result['error']}")
        return False

    # 检查是否有错误码
    if 'code' in result and result['code'] != '0':
        print(f"  [X] 添加策略失败:")
        print(f"    错误码: {result.get('code')}")
        print(f"    错误描述: {result.get('str', '未知错误')}")
        return False

    print("  [OK] 策略添加成功!")
    print(f"\n{'='*60}")
    print("策略配置完成!")
    print(f"  策略ID: {policy_id}")
    print(f"  策略内容: 禁止 {src_ip} 访问 {dst_ip}")
    print(f"{'='*60}")

    return True


def main():
    """主函数"""
    if len(sys.argv) < 4:
        print("用法: python add_policy_with_address.py <host> <token> <src_ip> <dst_ip> [policy_id]")
        print("\n示例:")
        print("  python add_policy_with_address.py https://192.168.10.249 YOUR_TOKEN 10.12.12.1 223.5.5.5")
        print("  python add_policy_with_address.py https://192.168.10.249 YOUR_TOKEN 10.12.12.1 223.5.5.5 3")
        print("\n参数说明:")
        print("  host      - 防火墙IP地址")
        print("  token     - 认证Token")
        print("  src_ip    - 源IP地址")
        print("  dst_ip    - 目的IP地址")
        print("  policy_id - 策略ID（可选，不指定则自动分配）")
        sys.exit(1)

    host = sys.argv[1]
    token = sys.argv[2]
    src_ip = sys.argv[3]
    dst_ip = sys.argv[4]
    policy_id = sys.argv[5] if len(sys.argv) > 5 else None

    # 确保host格式正确
    if not host.startswith('http://') and not host.startswith('https://'):
        host = 'https://' + host

    print(f"\n连接上元信安防火墙...")
    print(f"  地址: {host}")

    # 创建客户端
    client = ASGApiClient(host, token, verify_ssl=False)

    # 添加拒绝策略
    success = add_block_policy(client, src_ip, dst_ip, policy_id)

    if success:
        print(f"\n[OK] 操作完成!\n")
    else:
        print(f"\n[X] 操作失败!\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
