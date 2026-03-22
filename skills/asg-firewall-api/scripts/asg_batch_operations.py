#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASG防火墙批量操作脚本
支持从JSON或YAML文件读取批量操作请求
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from asg_api_client import ASGApiClient


def load_batch_file(file_path: str) -> List[Dict]:
    """
    从文件加载批量操作

    支持的格式:
    - JSON: .json
    - YAML: .yaml, .yml (需要PyYAML)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    suffix = path.suffix.lower()

    if suffix == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif suffix in ['.yaml', '.yml']:
        if not YAML_AVAILABLE:
            raise ImportError("YAML支持需要安装PyYAML: pip install pyyaml")
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")


def main():
    parser = argparse.ArgumentParser(
        description='ASG防火墙批量操作工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 从JSON文件执行批量操作
  python asg_batch_operations.py https://172.17.108.86 YOUR_TOKEN batch_ops.json

  # 从YAML文件执行批量操作
  python asg_batch_operations.py https://172.17.108.86 YOUR_TOKEN batch_ops.yaml

批量操作文件格式 (JSON):
[
  {
    "method": "POST",
    "endpoint": "/api/policy",
    "params": {"lang": "cn"},
    "data": {
      "id": "1",
      "protocol": "1",
      "if_in": "any",
      "if_out": "any",
      "sip": "any",
      "dip": "any",
      "sev": "any",
      "user": "any",
      "app": "any",
      "tr": "always",
      "mode": "1",
      "enable": "1"
    }
  },
  {
    "method": "GET",
    "endpoint": "/api/policy",
    "params": {"lang": "cn"}
  }
]

批量操作文件格式 (YAML):
- method: POST
  endpoint: /api/blacklist
  params:
    lang: cn
  data:
    ip_type: "1"
    ip: "1.1.1.1"
    age: "300"
    enable: "1"

- method: GET
  endpoint: /api/blacklist
  params:
    lang: cn
    ip_type: "1"
        '''
    )

    parser.add_argument('host', help='防火墙地址 (如: https://172.17.108.86)')
    parser.add_argument('token', help='认证Token')
    parser.add_argument('file', help='批量操作文件路径 (.json/.yaml/.yml)')
    parser.add_argument('--verify-ssl', action='store_true', help='验证SSL证书')

    args = parser.parse_args()

    # 加载批量操作文件
    try:
        requests_list = load_batch_file(args.file)
    except Exception as e:
        print(f"错误: 无法加载批量操作文件: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(requests_list, list):
        print("错误: 批量操作文件必须包含一个操作列表", file=sys.stderr)
        sys.exit(1)

    print(f"加载了 {len(requests_list)} 个操作")
    print()

    # 创建客户端并执行批量操作
    client = ASGApiClient(
        host=args.host,
        token=args.token,
        verify_ssl=args.verify_ssl
    )

    results = client.batch_request(requests_list)

    # 输出结果
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
