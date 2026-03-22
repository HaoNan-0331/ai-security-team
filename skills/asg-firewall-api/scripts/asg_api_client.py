#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASG防火墙REST API客户端
支持单次和批量操作，自动记录操作日志
"""

import requests
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ASGApiClient:
    """ASG防火墙API客户端"""

    def __init__(self, host: str, token: str, verify_ssl: bool = False, log_dir: str = None,
                 enable_experience_logging: bool = True):
        """
        初始化API客户端

        Args:
            host: 防火墙IP地址，格式: https://<IP> 或 http://<IP>
            token: 从Web界面生成的认证Token
            verify_ssl: 是否验证SSL证书，默认False
            log_dir: 日志目录路径，默认为logs/
            enable_experience_logging: 是否启用自动经验记录，默认True
        """
        self.host = host.rstrip('/')
        self.token = token
        self.verify_ssl = verify_ssl
        self.enable_experience_logging = enable_experience_logging
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.api_prefix = '/api'  # ASG防火墙API前缀
        self.default_params = {'api_key': token, 'lang': 'cn'}

        # 设置日志目录
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / 'logs'
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 初始化经验管理器（延迟加载，避免循环导入）
        self._experience_manager = None

    @property
    def experience_manager(self):
        """延迟加载经验管理器"""
        if self._experience_manager is None and self.enable_experience_logging:
            try:
                from experience_manager import ExperienceManager
                self._experience_manager = ExperienceManager()
            except ImportError:
                # 如果经验管理器不可用，禁用经验记录
                self.enable_experience_logging = False
        return self._experience_manager

    def _log_operation(self, method: str, endpoint: str, params: Dict = None,
                       data: Dict = None, response: Any = None):
        """记录操作日志到API日志文件"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'endpoint': endpoint,
            'params': params,
            'data': data,
            'response': response if isinstance(response, dict) else str(response)[:1000]
        }

        log_file = self.log_dir / f'api_log_{datetime.now().strftime("%Y%m%d")}.json'
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')

        # 同时记录到经验库（如果启用）
        if self.enable_experience_logging and self.experience_manager:
            try:
                # 推断操作类型
                operation = self._infer_operation(endpoint, method)

                # 记录到经验库
                self.experience_manager.log_operation(
                    operation=operation,
                    endpoint=endpoint,
                    params=params,
                    data=data,
                    response=response,
                    notes=f"自动记录于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except Exception as exp_error:
                # 经验记录失败不应影响请求结果
                pass

    def _infer_operation(self, endpoint: str, method: str) -> str:
        """从端点和HTTP方法推断操作类型"""
        # 移除前导斜杠
        endpoint = endpoint.lstrip('/')

        # 根据端点路径推断操作
        if 'policy' in endpoint:
            if method == 'GET':
                return 'get_policies'
            elif method == 'POST':
                return 'add_policy'
            elif method == 'PUT':
                return 'update_policy'
            elif method == 'DELETE':
                return 'delete_policy'
        elif 'blacklist' in endpoint:
            if method == 'GET':
                return 'get_blacklist'
            elif method == 'POST':
                return 'add_blacklist'
            elif method == 'DELETE':
                return 'delete_blacklist'
        elif 'address' in endpoint:
            if method == 'GET':
                return 'get_addresses'
            elif method == 'POST':
                return 'add_address'
            elif method == 'PUT':
                return 'update_address'
            elif method == 'DELETE':
                return 'delete_address'
        elif 'route' in endpoint:
            if method == 'GET':
                return 'get_routes'
            elif method == 'POST':
                return 'add_route'
            elif method == 'PUT':
                return 'update_route'
            elif method == 'DELETE':
                return 'delete_route'

        # 默认返回方法+端点组合
        return f"{method.lower()}_{endpoint.replace('/', '_').replace('-', '_')}"

    def request(self, method: str, endpoint: str, params: Dict = None,
                data: Dict = None) -> Dict:
        """
        发送API请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点路径
            params: URL查询参数
            data: 请求体数据

        Returns:
            API响应JSON数据
        """
        # 合并默认参数
        if params is None:
            params = {}
        merged_params = {**self.default_params, **params}

        url = f"{self.host}{self.api_prefix}/{endpoint.lstrip('/')}"
        response = None  # 初始化 response 变量，避免未定义错误
        response_data = None

        try:
            # 发送HTTP请求
            if method.upper() == 'GET':
                response = self.session.get(
                    url,
                    params=merged_params,
                    verify=self.verify_ssl,
                    timeout=30
                )
            elif method.upper() == 'POST':
                response = self.session.post(
                    url,
                    params=merged_params,
                    json=data,
                    verify=self.verify_ssl,
                    timeout=30
                )
            elif method.upper() == 'PUT':
                response = self.session.put(
                    url,
                    params=merged_params,
                    json=data,
                    verify=self.verify_ssl,
                    timeout=30
                )
            elif method.upper() == 'DELETE':
                response = self.session.delete(
                    url,
                    params=merged_params,
                    json=data,
                    verify=self.verify_ssl,
                    timeout=30
                )
            else:
                return {'error': f'不支持的HTTP方法: {method}'}

            # 检查HTTP状态码
            if response.status_code >= 400:
                error_msg = f'HTTP错误: {response.status_code}'
                try:
                    error_detail = response.json()
                    if 'str' in error_detail:
                        error_msg += f' - {error_detail["str"]}'
                    elif 'message' in error_detail:
                        error_msg += f' - {error_detail["message"]}'
                except:
                    if response.text:
                        error_msg += f' - {response.text[:200]}'
                return {'error': error_msg, 'status_code': response.status_code}

            # 处理响应
            if not response.text.strip():
                # 空响应表示成功（某些API成功时返回空）
                response_data = {'success': True}
            else:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    # 如果无法解析为JSON，返回原始文本
                    response_data = {
                        'raw_response': response.text,
                        'warning': '响应无法解析为JSON'
                    }

            # 记录日志（使用try-except避免日志失败影响请求）
            try:
                self._log_operation(method, endpoint, merged_params, data, response_data)
            except Exception as log_error:
                # 日志记录失败不应影响请求结果
                pass

            return response_data

        except requests.exceptions.SSLError as e:
            return {'error': 'SSL证书验证失败，请设置verify_ssl=False或使用http://', 'detail': str(e)}
        except requests.exceptions.Timeout as e:
            return {'error': '请求超时，请检查网络连接', 'detail': str(e)}
        except requests.exceptions.ConnectionError as e:
            return {'error': '连接失败，请检查防火墙地址是否正确', 'detail': str(e)}
        except Exception as e:
            error_msg = f'未知错误: {str(e)}'
            if response is not None:
                error_msg += f' (响应: {response.text[:200] if response.text else "空"})'
            return {'error': error_msg}

    def batch_request(self, requests_list: List[Dict]) -> List[Dict]:
        """
        批量发送API请求

        Args:
            requests_list: 请求列表，每个元素包含 {method, endpoint, params, data}

        Returns:
            响应列表
        """
        results = []
        for req in requests_list:
            result = self.request(
                method=req.get('method', 'GET'),
                endpoint=req.get('endpoint', ''),
                params=req.get('params'),
                data=req.get('data')
            )
            results.append({
                'request': req,
                'response': result
            })
        return results

    # ==================== 网络接口模块 ====================

    def get_vlan_interfaces(self) -> Dict:
        """获取VLAN接口列表"""
        return self.request('GET', '/interface-vlan')

    def add_vlan_interface(self, data: Dict) -> Dict:
        """添加VLAN接口"""
        return self.request('POST', '/interface-vlan', data=data)

    def update_vlan_interface(self, data: Dict) -> Dict:
        """修改VLAN接口"""
        return self.request('PUT', '/interface-vlan', data=data)

    def delete_vlan_interface(self, data: Dict) -> Dict:
        """删除VLAN接口"""
        return self.request('DELETE', '/interface-vlan', data=data)

    def get_gre_tunnels(self) -> Dict:
        """获取GRE隧道列表"""
        return self.request('GET', '/interface-gre')

    def add_gre_tunnel(self, data: Dict) -> Dict:
        """添加GRE隧道"""
        return self.request('POST', '/interface-gre', data=data)

    def update_gre_tunnel(self, data: Dict) -> Dict:
        """修改GRE隧道"""
        return self.request('PUT', '/interface-gre', data=data)

    def delete_gre_tunnel(self, data: Dict) -> Dict:
        """删除GRE隧道"""
        return self.request('DELETE', '/interface-gre', data=data)

    def get_loopback_interfaces(self) -> Dict:
        """获取环回接口列表"""
        return self.request('GET', '/interface-loopback')

    def add_loopback_interface(self, data: Dict) -> Dict:
        """添加环回接口"""
        return self.request('POST', '/interface-loopback', data=data)

    def update_loopback_interface(self, data: Dict) -> Dict:
        """修改环回接口"""
        return self.request('PUT', '/interface-loopback', data=data)

    def delete_loopback_interface(self, data: Dict) -> Dict:
        """删除环回接口"""
        return self.request('DELETE', '/interface-loopback', data=data)

    def get_bypass_config(self) -> Dict:
        """获取旁路部署配置"""
        return self.request('GET', '/bypass')

    def add_bypass_config(self, data: Dict) -> Dict:
        """添加旁路部署配置"""
        return self.request('POST', '/bypass', data=data)

    def update_bypass_config(self, data: Dict) -> Dict:
        """修改旁路部署配置"""
        return self.request('PUT', '/bypass', data=data)

    def delete_bypass_config(self, data: Dict) -> Dict:
        """删除旁路部署配置"""
        return self.request('DELETE', '/bypass', data=data)

    def get_port_mirror(self) -> Dict:
        """获取端口镜像配置"""
        return self.request('GET', '/port-mirror')

    def add_port_mirror(self, data: Dict) -> Dict:
        """添加端口镜像配置"""
        return self.request('POST', '/port-mirror', data=data)

    def update_port_mirror(self, data: Dict) -> Dict:
        """修改端口镜像配置"""
        return self.request('PUT', '/port-mirror', data=data)

    def delete_port_mirror(self, data: Dict) -> Dict:
        """删除端口镜像配置"""
        return self.request('DELETE', '/port-mirror', data=data)

    # ==================== 路由配置模块 ====================

    def get_static_routes(self) -> Dict:
        """获取IPv4静态路由列表"""
        return self.request('GET', '/route-static')

    def add_static_route(self, data: Dict) -> Dict:
        """添加IPv4静态路由"""
        return self.request('POST', '/route-static', data=data)

    def update_static_route(self, data: Dict) -> Dict:
        """修改IPv4静态路由"""
        return self.request('PUT', '/route-static', data=data)

    def delete_static_route(self, data: Dict) -> Dict:
        """删除IPv4静态路由"""
        return self.request('DELETE', '/route-static', data=data)

    def get_static_routes_ipv6(self) -> Dict:
        """获取IPv6静态路由列表"""
        return self.request('GET', '/route-static-ipv6')

    def add_static_route_ipv6(self, data: Dict) -> Dict:
        """添加IPv6静态路由"""
        return self.request('POST', '/route-static-ipv6', data=data)

    def update_static_route_ipv6(self, data: Dict) -> Dict:
        """修改IPv6静态路由"""
        return self.request('PUT', '/route-static-ipv6', data=data)

    def delete_static_route_ipv6(self, data: Dict) -> Dict:
        """删除IPv6静态路由"""
        return self.request('DELETE', '/route-static-ipv6', data=data)

    def get_pbr_routes(self) -> Dict:
        """获取IPv4策略路由列表"""
        return self.request('GET', '/pbr-route')

    def add_pbr_route(self, data: Dict) -> Dict:
        """添加IPv4策略路由"""
        return self.request('POST', '/pbr-route', data=data)

    def update_pbr_route(self, data: Dict) -> Dict:
        """修改IPv4策略路由"""
        return self.request('PUT', '/pbr-route', data=data)

    def delete_pbr_route(self, data: Dict) -> Dict:
        """删除IPv4策略路由"""
        return self.request('DELETE', '/pbr-route', data=data)

    def get_pbr_routes_ipv6(self) -> Dict:
        """获取IPv6策略路由列表"""
        return self.request('GET', '/pbr-route-ipv6')

    def add_pbr_route_ipv6(self, data: Dict) -> Dict:
        """添加IPv6策略路由"""
        return self.request('POST', '/pbr-route-ipv6', data=data)

    def update_pbr_route_ipv6(self, data: Dict) -> Dict:
        """修改IPv6策略路由"""
        return self.request('PUT', '/pbr-route-ipv6', data=data)

    def delete_pbr_route_ipv6(self, data: Dict) -> Dict:
        """删除IPv6策略路由"""
        return self.request('DELETE', '/pbr-route-ipv6', data=data)

    def get_isp_routes(self) -> Dict:
        """获取ISP路由列表"""
        return self.request('GET', '/isp-route')

    def add_isp_route(self, data: Dict) -> Dict:
        """添加ISP路由"""
        return self.request('POST', '/isp-route', data=data)

    def update_isp_route(self, data: Dict) -> Dict:
        """修改ISP路由"""
        return self.request('PUT', '/isp-route', data=data)

    def delete_isp_route(self, data: Dict) -> Dict:
        """删除ISP路由"""
        return self.request('DELETE', '/isp-route', data=data)

    # ==================== SSL VPN模块 ====================

    def get_sslvpn_config(self) -> Dict:
        """获取SSL VPN配置"""
        return self.request('GET', '/sslvpn-config')

    def update_sslvpn_config(self, data: Dict) -> Dict:
        """修改SSL VPN配置"""
        return self.request('PUT', '/sslvpn-config', data=data)

    def get_sslvpn_monitor(self) -> Dict:
        """查询SSLVPN监控"""
        return self.request('GET', '/sslvpn-monitor')

    def clear_sslvpn_monitor(self, data: Dict) -> Dict:
        """清除SSLVPN监控"""
        return self.request('DELETE', '/sslvpn-monitor', data=data)

    def get_sslvpn_userbind(self) -> Dict:
        """查询SSLVPN用户绑定"""
        return self.request('GET', '/sslvpn-userbind')

    def add_sslvpn_userbind(self, data: Dict) -> Dict:
        """添加SSLVPN用户绑定"""
        return self.request('POST', '/sslvpn-userbind', data=data)

    def update_sslvpn_userbind(self, data: Dict) -> Dict:
        """修改SSLVPN用户绑定"""
        return self.request('PUT', '/sslvpn-userbind', data=data)

    def delete_sslvpn_userbind(self, data: Dict) -> Dict:
        """删除SSLVPN用户绑定"""
        return self.request('DELETE', '/sslvpn-userbind', data=data)

    def get_sslvpn_tunn_if(self) -> Dict:
        """查询SSLVPN接口配置"""
        return self.request('GET', '/sslvpn-tunn-if')

    def update_sslvpn_tunn_if(self, data: Dict) -> Dict:
        """编辑SSLVPN接口配置"""
        return self.request('PUT', '/sslvpn-tunn-if', data=data)

    # ==================== 策略管理模块 ====================

    def get_policies(self, protocol: str = "1", vrf: str = "vrf0", page: int = 1, page_size: int = 10, **kwargs) -> Dict:
        """
        获取一体化策略列表

        Args:
            protocol: 协议类型，1表示IPv4，2表示IPv6，默认为1
            vrf: VRF实例名称，默认为vrf0
            page: 页码，默认为1
            page_size: 每页条数，默认为10
            **kwargs: 其他查询参数

        Returns:
            策略列表响应数据
        """
        params = {'protocol': protocol, 'vrf': vrf, 'page': page, 'pageSize': page_size, **kwargs}
        return self.request('GET', '/policy', params=params)

    def add_policy(self, data: Dict) -> Dict:
        """添加一体化策略"""
        return self.request('POST', '/policy', data=data)

    def update_policy(self, data: Dict) -> Dict:
        """修改一体化策略"""
        return self.request('PUT', '/policy', data=data)

    def delete_policy(self, data: Dict) -> Dict:
        """删除一体化策略"""
        return self.request('DELETE', '/policy', data=data)

    def update_policy_state(self, data: Dict) -> Dict:
        """修改策略启用状态"""
        return self.request('PUT', '/policy-state', data=data)

    def move_policy(self, data: Dict) -> Dict:
        """移动策略位置"""
        return self.request('PUT', '/policy', data=data)

    def _get_address_name_by_ip(self, ip_address: str) -> Optional[str]:
        """
        通过IP地址查找对应的地址对象名称

        Args:
            ip_address: IP地址

        Returns:
            地址对象名称，如果不存在则返回None
        """
        try:
            addresses = self.get_addresses()
            for addr in addresses.get('data', []):
                items = addr.get('item', {})
                group = items.get('group', [])
                for item in group:
                    if item.get('host') == ip_address:
                        return addr.get('name')
            return None
        except Exception:
            return None

    def _create_address_for_ip(self, ip_address: str, prefix: str = 'src') -> Dict:
        """
        为IP地址创建地址对象

        Args:
            ip_address: IP地址
            prefix: 地址对象前缀，默认为'src'，也可以是'dst'

        Returns:
            创建结果
        """
        # 将IP地址中的点替换为下划线，作为对象名称
        addr_name = f"{prefix}_{ip_address.replace('.', '_')}"

        data = {
            'name': addr_name,
            'desc': f'{prefix}地址{ip_address}',
            'type': 0,
            'item': [
                {
                    'host': ip_address,
                    'type': 0
                }
            ]
        }
        return self.add_address(data)

    def add_policy_simple(self, source_ip: str, dest_ip: str,
                         policy_id: str = None,
                         action: str = 'permit',
                         description: str = None,
                         **kwargs) -> Dict:
        """
        简化的策略添加方法 - 自动处理地址对象

        Args:
            source_ip: 源IP地址
            dest_ip: 目标IP地址
            policy_id: 策略ID（可选，自动获取下一个可用ID）
            action: 动作，'permit'（允许）或 'deny'（拒绝）
            description: 策略描述
            **kwargs: 其他策略参数（protocol, if_in, if_out, sev等）

        Returns:
            添加结果
        """
        # 获取现有策略以确定下一个可用ID
        if policy_id is None:
            policies = self.get_policies(page_size=1000)
            existing_ids = []
            for p in policies.get('data', []):
                try:
                    existing_ids.append(int(p.get('id', 0)))
                except ValueError:
                    pass
            policy_id = str(max(existing_ids) + 1) if existing_ids else '1'

        # 处理源地址对象
        src_addr_name = self._get_address_name_by_ip(source_ip)
        if not src_addr_name:
            result = self._create_address_for_ip(source_ip, 'src')
            if not result.get('success') and result.get('code'):
                return result
            src_addr_name = f"src_{source_ip.replace('.', '_')}"

        # 处理目标地址对象
        dst_addr_name = self._get_address_name_by_ip(dest_ip)
        if not dst_addr_name:
            result = self._create_address_for_ip(dest_ip, 'dst')
            if not result.get('success') and result.get('code'):
                return result
            dst_addr_name = f"dst_{dest_ip.replace('.', '_')}"

        # 构建策略数据
        policy_data = {
            'id': policy_id,
            'protocol': kwargs.get('protocol', '1'),
            'if_in': kwargs.get('if_in', 'any'),
            'if_out': kwargs.get('if_out', 'any'),
            'sip': src_addr_name,
            'dip': dst_addr_name,
            'sev': kwargs.get('sev', 'any'),
            'user': kwargs.get('user', 'any'),
            'app': kwargs.get('app', 'any'),
            'tr': kwargs.get('tr', 'always'),
            'mode': '1' if action.lower() == 'permit' else '2',
            'enable': kwargs.get('enable', '1'),
            'refer_id': kwargs.get('refer_id', '0'),
            'syslog': kwargs.get('syslog', '1'),
            'log_level': kwargs.get('log_level', '6'),
            'desc': description or f"{'允许' if action.lower() == 'permit' else '拒绝'}{source_ip}访问{dest_ip}"
        }

        return self.add_policy(policy_data)

    # ==================== 黑名单模块 ====================

    def get_ip_blacklist(self, ip_type: str = "1", **kwargs) -> Dict:
        """获取IP黑名单列表"""
        params = {'ip_type': ip_type, **kwargs}
        return self.request('GET', '/blacklist', params=params)

    def add_ip_blacklist(self, data: Dict) -> Dict:
        """添加IP黑名单"""
        return self.request('POST', '/blacklist', data=data)

    def update_ip_blacklist(self, data: Dict) -> Dict:
        """修改IP黑名单"""
        return self.request('PUT', '/blacklist', data=data)

    def delete_ip_blacklist(self, data: Dict) -> Dict:
        """删除IP黑名单"""
        return self.request('DELETE', '/blacklist', data=data)

    def get_domain_blacklist(self) -> Dict:
        """获取域名黑名单列表"""
        return self.request('GET', '/blacklist-domain')

    def add_domain_blacklist(self, data: Dict) -> Dict:
        """添加域名黑名单"""
        return self.request('POST', '/blacklist-domain', data=data)

    def update_domain_blacklist(self, data: Dict) -> Dict:
        """修改域名黑名单"""
        return self.request('PUT', '/blacklist-domain', data=data)

    def delete_domain_blacklist(self, data: Dict) -> Dict:
        """删除域名黑名单"""
        return self.request('DELETE', '/blacklist-domain', data=data)

    # ==================== 威胁情报模块 ====================

    def get_threat_intelligence_switch(self) -> Dict:
        """获取威胁情报开关状态"""
        return self.request('GET', '/ecd-item')

    def update_threat_intelligence_switch(self, data: Dict) -> Dict:
        """修改威胁情报开关状态"""
        return self.request('PUT', '/ecd-item', data=data)

    def get_reliable_config(self) -> Dict:
        """获取威胁情报信誉值配置"""
        return self.request('GET', '/reliable-config')

    def update_reliable_config(self, data: Dict) -> Dict:
        """修改威胁情报信誉值配置"""
        return self.request('PUT', '/reliable-config', data=data)

    def get_intelligence_level(self) -> Dict:
        """获取风险级别日志级别配置"""
        return self.request('GET', '/intelligence-level')

    def update_intelligence_level(self, data: Dict) -> Dict:
        """修改风险级别日志级别配置"""
        return self.request('PUT', '/intelligence-level', data=data)

    def get_cloud_intelligence_config(self) -> Dict:
        """获取云端情报联动配置"""
        return self.request('GET', '/coo-def-cloud')

    def check_online_status(self) -> Dict:
        """获取与云端威胁情报中心连接状态"""
        return self.request('GET', '/check-online')

    def get_intelligence_database(self) -> Dict:
        """获取云端威胁情报情报库升级历史"""
        return self.request('GET', '/intelligence-database')

    def check_update(self) -> Dict:
        """获取云端威胁情报情报库情况"""
        return self.request('GET', '/check-update')

    def get_ioc_lasttime(self) -> Dict:
        """获取云端威胁情报最近一次升级时间"""
        return self.request('GET', '/ioc-lasttime')

    def get_custom_intelligence(self, **kwargs) -> Dict:
        """获取自定义威胁情报列表"""
        params = {'source': 'local_coo_def', **kwargs}
        return self.request('GET', '/defense', params=params)

    def add_custom_intelligence(self, data: Dict) -> Dict:
        """添加自定义威胁情报"""
        return self.request('POST', '/defense', data=data)

    def update_custom_intelligence(self, data: Dict) -> Dict:
        """修改自定义威胁情报"""
        return self.request('PUT', '/defense', data=data)

    def delete_custom_intelligence(self, data: Dict) -> Dict:
        """删除自定义威胁情报"""
        return self.request('DELETE', '/defense', data=data)

    # ==================== 入侵防护模块 ====================

    def get_ips_templates(self) -> Dict:
        """获取入侵防护模板列表"""
        return self.request('GET', '/ips-rule')

    def add_ips_template(self, data: Dict) -> Dict:
        """添加入侵防护模板"""
        return self.request('POST', '/ips-rule', data=data)

    def update_ips_template(self, data: Dict) -> Dict:
        """修改入侵防护模板"""
        return self.request('PUT', '/ips-rule', data=data)

    def delete_ips_template(self, data: Dict) -> Dict:
        """删除入侵防护模板"""
        return self.request('DELETE', '/ips-rule', data=data)

    def get_ips_sets(self) -> Dict:
        """获取事件集策略列表"""
        return self.request('GET', '/ips-set')

    def add_ips_set(self, data: Dict) -> Dict:
        """添加事件集策略"""
        return self.request('POST', '/ips-set', data=data)

    def update_ips_set(self, data: Dict) -> Dict:
        """修改事件集策略"""
        return self.request('PUT', '/ips-set', data=data)

    def delete_ips_set(self, data: Dict) -> Dict:
        """删除事件集策略"""
        return self.request('DELETE', '/ips-set', data=data)

    def get_ips_set_detail(self, set_name: str, **kwargs) -> Dict:
        """获取事件集详情"""
        params = {'set_name': set_name, **kwargs}
        return self.request('GET', '/ips-set-detail', params=params)

    def add_ips_set_member(self, data: Dict) -> Dict:
        """将预定义事件集添加到事件集"""
        return self.request('POST', '/ips-sig-node', data=data)

    def update_ips_set_detail(self, data: Dict) -> Dict:
        """修改事件集详情"""
        return self.request('PUT', '/ips-set-detail', data=data)

    def delete_ips_set_detail(self, data: Dict) -> Dict:
        """删除事件集详情"""
        return self.request('DELETE', '/ips-set-detail', data=data)

    # ==================== 病毒防护模块 ====================

    def get_av_templates(self) -> Dict:
        """获取病毒防护模板列表"""
        return self.request('GET', '/av-rule')

    def add_av_template(self, data: Dict) -> Dict:
        """添加病毒防护模板"""
        return self.request('POST', '/av-rule', data=data)

    def update_av_template(self, data: Dict) -> Dict:
        """修改病毒防护模板"""
        return self.request('PUT', '/av-rule', data=data)

    def delete_av_template(self, data: Dict) -> Dict:
        """删除病毒防护模板"""
        return self.request('DELETE', '/av-rule', data=data)

    def get_av_filetypes(self) -> Dict:
        """获取扫描文件类型配置"""
        return self.request('GET', '/av-filetype')

    def add_av_filetype(self, data: Dict) -> Dict:
        """添加扫描文件类型"""
        return self.request('POST', '/av-filetype', data=data)

    def update_av_filetype(self, data: Dict) -> Dict:
        """修改扫描文件类型"""
        return self.request('PUT', '/av-filetype', data=data)

    def delete_av_filetype(self, data: Dict) -> Dict:
        """删除扫描文件类型"""
        return self.request('DELETE', '/av-filetype', data=data)

    # ==================== EDR联动模块 ====================

    def get_edr_center(self) -> Dict:
        """获取EDR中心配置"""
        return self.request('GET', '/edr-center')

    def update_edr_center(self, data: Dict) -> Dict:
        """修改EDR中心配置"""
        return self.request('PUT', '/edr-center', data=data)

    def get_edr_install(self) -> Dict:
        """获取EDR安装路径"""
        return self.request('GET', '/edr-install')

    def update_edr_install(self, data: Dict) -> Dict:
        """修改EDR安装路径"""
        return self.request('PUT', '/edr-install', data=data)

    def get_edr_policies(self, **kwargs) -> Dict:
        """获取EDR联动策略列表"""
        return self.request('GET', '/edr-policy', params=kwargs)

    def add_edr_policy(self, data: Dict) -> Dict:
        """添加EDR联动策略"""
        return self.request('POST', '/edr-policy', data=data)

    def update_edr_policy(self, data: Dict) -> Dict:
        """修改EDR联动策略"""
        return self.request('PUT', '/edr-policy', data=data)

    def delete_edr_policy(self, data: Dict) -> Dict:
        """删除EDR联动策略"""
        return self.request('DELETE', '/edr-policy', data=data)

    def move_edr_policy(self, data: Dict) -> Dict:
        """移动EDR联动策略"""
        return self.request('PUT', '/edr-policy', data=data)

    def get_edr_https(self) -> Dict:
        """获取EDR联动HTTPS触发状态"""
        return self.request('GET', '/edr-https')

    def update_edr_https(self, data: Dict) -> Dict:
        """修改EDR联动HTTPS触发状态"""
        return self.request('PUT', '/edr-https', data=data)

    def get_edr_users(self, **kwargs) -> Dict:
        """获取EDR资产列表"""
        return self.request('GET', '/edr-user', params=kwargs)

    def release_edr_user(self, data: Dict) -> Dict:
        """临时放行EDR资产"""
        return self.request('PUT', '/edr-user', data=data)

    # ==================== 引流策略模块 ====================

    def get_divert_policies(self) -> Dict:
        """获取引流策略列表"""
        return self.request('GET', '/divert-policy')

    def add_divert_policy(self, data: Dict) -> Dict:
        """添加引流策略"""
        return self.request('POST', '/divert-policy', data=data)

    def update_divert_policy(self, data: Dict) -> Dict:
        """修改引流策略"""
        return self.request('PUT', '/divert-policy', data=data)

    def delete_divert_policy(self, data: Dict) -> Dict:
        """删除引流策略"""
        return self.request('DELETE', '/divert-policy', data=data)

    def clear_divert_policy_hits(self, data: Dict) -> Dict:
        """清除引流策略命中数"""
        return self.request('PUT', '/divert-policy', data=data)

    def move_divert_policy(self, data: Dict) -> Dict:
        """移动引流策略"""
        return self.request('PUT', '/divert-policy', data=data)

    # ==================== 镜像策略模块 ====================

    def get_mirror_policies(self) -> Dict:
        """获取镜像策略列表"""
        return self.request('GET', '/mirror-policy')

    def add_mirror_policy(self, data: Dict) -> Dict:
        """添加镜像策略"""
        return self.request('POST', '/mirror-policy', data=data)

    def update_mirror_policy(self, data: Dict) -> Dict:
        """修改镜像策略"""
        return self.request('PUT', '/mirror-policy', data=data)

    def delete_mirror_policy(self, data: Dict) -> Dict:
        """删除镜像策略"""
        return self.request('DELETE', '/mirror-policy', data=data)

    # ==================== 用户认证模块 ====================

    def get_auth_users(self, **kwargs) -> Dict:
        """获取用户列表"""
        return self.request('GET', '/auth-user', params=kwargs)

    def add_auth_user(self, data: Dict) -> Dict:
        """添加用户"""
        return self.request('POST', '/auth-user', data=data)

    def update_auth_user(self, data: Dict) -> Dict:
        """修改用户"""
        return self.request('PUT', '/auth-user', data=data)

    def delete_auth_user(self, data: Dict) -> Dict:
        """删除用户"""
        return self.request('DELETE', '/auth-user', data=data)

    def get_snmp_sync(self, **kwargs) -> Dict:
        """获取SNMP用户同步列表"""
        return self.request('GET', '/snmp-sync', params=kwargs)

    def add_snmp_sync(self, data: Dict) -> Dict:
        """添加SNMP用户同步"""
        return self.request('POST', '/snmp-sync', data=data)

    def update_snmp_sync(self, data: Dict) -> Dict:
        """修改SNMP用户同步"""
        return self.request('PUT', '/snmp-sync', data=data)

    def delete_snmp_sync(self, data: Dict) -> Dict:
        """删除SNMP用户同步"""
        return self.request('DELETE', '/snmp-sync', data=data)

    def get_wechat_config(self) -> Dict:
        """获取微信认证配置"""
        return self.request('GET', '/wechat-cnf')

    def update_wechat_config(self, data: Dict) -> Dict:
        """修改微信认证配置"""
        return self.request('POST', '/wechat-cnf', data=data)

    # ==================== 日志与监控模块 ====================

    def get_firewall_logs(self, sid: str, **kwargs) -> Dict:
        """查询防火墙日志"""
        params = {'module': 'filter', 'sid': sid, **kwargs}
        return self.request('GET', '/audit-log', params=params)

    def export_firewall_logs(self, export_type: str, num: int = 1, **kwargs) -> Dict:
        """导出防火墙日志"""
        params = {'download': '1', 'num': num, 'type': export_type, 'module': 'filter', **kwargs}
        return self.request('GET', '/audit-log', params=params)

    def get_syslog_config(self) -> Dict:
        """获取Syslog配置"""
        return self.request('GET', '/syslog-server')

    def update_syslog_config(self, data: Dict) -> Dict:
        """修改Syslog配置"""
        return self.request('PUT', '/syslog-server', data=data)

    def get_syslog_docking(self) -> Dict:
        """获取Syslog对接标准"""
        return self.request('GET', '/syslog-docking')

    def update_syslog_docking(self, data: Dict) -> Dict:
        """修改Syslog对接标准"""
        return self.request('PUT', '/syslog-docking', data=data)

    def update_snmp_config(self, data: Dict) -> Dict:
        """修改SNMP配置"""
        return self.request('PUT', '/snmp-config', data=data)

    # ==================== 系统管理模块 ====================

    def get_sdwan_config(self) -> Dict:
        """获取SD-WAN配置"""
        return self.request('GET', '/cloud-agent')

    def update_sdwan_config(self, data: Dict) -> Dict:
        """修改SD-WAN配置"""
        return self.request('PUT', '/cloud-agent', data=data)

    def get_backup_version(self) -> Dict:
        """获取当前固件版本"""
        return self.request('GET', '/backup-version')

    def backup_system(self) -> Dict:
        """备份当前系统"""
        return self.request('POST', '/backup-version')

    def delete_backup(self) -> Dict:
        """删除备份系统"""
        return self.request('DELETE', '/backup-version')

    def reboot_system(self, operation: int = 0) -> Dict:
        """重启设备"""
        return self.request('PUT', '/reboot', data={'operation': operation})

    def get_update_log(self) -> Dict:
        """获取升级历史"""
        return self.request('GET', '/update-log')

    def manual_update(self, filename: str, filetype: str) -> Dict:
        """手动升级"""
        return self.request('POST', '/manual-update', data={'filename': filename, 'filetype': filetype})

    def get_auto_update_config(self) -> Dict:
        """获取自动升级配置"""
        return self.request('GET', '/auto-update')

    def update_auto_update_config(self, data: Dict) -> Dict:
        """应用自动升级配置"""
        return self.request('PUT', '/auto-update', data=data)

    def immediate_update(self, data: Dict) -> Dict:
        """立刻升级"""
        return self.request('POST', '/auto-update', data=data)

    def authorize_active(self) -> Dict:
        """授权激活"""
        return self.request('POST', '/authorize-active')

    # ==================== 地址对象模块 ====================

    def get_addresses(self) -> Dict:
        """获取地址对象列表"""
        return self.request('GET', '/address')

    def add_address(self, data: Dict) -> Dict:
        """添加地址对象"""
        return self.request('POST', '/address', data=data)

    def update_address(self, data: Dict) -> Dict:
        """修改地址对象"""
        return self.request('PUT', '/address', data=data)

    def delete_address(self, data: Dict) -> Dict:
        """删除地址对象"""
        return self.request('DELETE', '/address', data=data)

    def get_address_groups(self) -> Dict:
        """获取地址组对象列表"""
        return self.request('GET', '/address-group')

    def add_address_group(self, data: Dict) -> Dict:
        """添加地址组对象"""
        return self.request('POST', '/address-group', data=data)

    def delete_address_group(self, data: Dict) -> Dict:
        """删除地址组对象"""
        return self.request('DELETE', '/address-group', data=data)


def main():
    """命令行入口"""
    if len(sys.argv) < 3:
        print("用法: python asg_api_client.py <host> <token> [操作] [参数...]")
        print("\n示例:")
        print("  查看策略: python asg_api_client.py https://172.17.108.86 YOUR_TOKEN get_policies")
        print("  添加策略: python asg_api_client.py https://172.17.108.86 YOUR_TOKEN add_policy '{...}'")
        print("\n  简化策略添加（推荐）:")
        print("    python asg_api_client.py https://192.168.55.249 TOKEN add_policy_simple '{")
        print("      \"source\": \"192.168.66.5\",")
        print("      \"destination\": \"223.5.5.5\",")
        print("      \"action\": \"permit\"")
        print("    }'")
        print("\n支持的操作:")
        print("  网络接口:")
        print("    get_vlan_interfaces, add_vlan_interface, delete_vlan_interface")
        print("    get_gre_tunnels, add_gre_tunnel, delete_gre_tunnel")
        print("  路由配置:")
        print("    get_static_routes, add_static_route, delete_static_route")
        print("    get_pbr_routes, add_pbr_route, delete_pbr_route")
        print("  策略管理:")
        print("    get_policies")
        print("    add_policy - 需要完整JSON参数（包括地址对象名称）")
        print("    add_policy_simple - 简化版，自动创建地址对象（推荐）")
        print("    update_policy, delete_policy")
        print("  黑名单:")
        print("    get_ip_blacklist, add_ip_blacklist, delete_ip_blacklist")
        print("    get_domain_blacklist, add_domain_blacklist, delete_domain_blacklist")
        print("  威胁情报:")
        print("    get_threat_intelligence_switch, get_custom_intelligence")
        print("    add_custom_intelligence, delete_custom_intelligence")
        print("  入侵防护:")
        print("    get_ips_templates, add_ips_template, delete_ips_template")
        print("  病毒防护:")
        print("    get_av_templates, add_av_template, delete_av_template")
        print("  日志查询:")
        print("    get_firewall_logs, export_firewall_logs")
        print("  系统管理:")
        print("    get_backup_version, reboot_system, get_update_log")
        print("  地址对象:")
        print("    get_addresses, add_address, update_address, delete_address")
        print("\n注意:")
        print("  - add_policy_simple 会自动创建源/目标地址对象（如果不存在）")
        print("  - 地址对象命名格式: src_<IP> 和 dst_<IP>")
        print("  - 策略ID自动获取，也可手动指定")
        sys.exit(1)

    host = sys.argv[1]
    token = sys.argv[2]

    client = ASGApiClient(host, token, verify_ssl=False)

    if len(sys.argv) < 4:
        # 默认获取策略列表
        result = client.get_policies()
    else:
        operation = sys.argv[3]
        params = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None

        # 操作映射
        operations = {
            # 网络接口
            'get_vlan_interfaces': lambda: client.get_vlan_interfaces(),
            'add_vlan_interface': lambda: client.add_vlan_interface(params),
            'update_vlan_interface': lambda: client.update_vlan_interface(params),
            'delete_vlan_interface': lambda: client.delete_vlan_interface(params),
            'get_gre_tunnels': lambda: client.get_gre_tunnels(),
            'add_gre_tunnel': lambda: client.add_gre_tunnel(params),
            'delete_gre_tunnel': lambda: client.delete_gre_tunnel(params),
            # 路由配置
            'get_static_routes': lambda: client.get_static_routes(),
            'add_static_route': lambda: client.add_static_route(params),
            'update_static_route': lambda: client.update_static_route(params),
            'delete_static_route': lambda: client.delete_static_route(params),
            'get_pbr_routes': lambda: client.get_pbr_routes(),
            'add_pbr_route': lambda: client.add_pbr_route(params),
            'delete_pbr_route': lambda: client.delete_pbr_route(params),
            # 策略管理
            'get_policies': lambda: client.get_policies(),
            'add_policy': lambda: client.add_policy(params),
            'add_policy_simple': lambda: client.add_policy_simple(
                params.get('source', params.get('src')),
                params.get('destination', params.get('dest')),
                policy_id=params.get('id'),
                action=params.get('action', 'permit'),
                description=params.get('desc'),
                **{k: v for k, v in params.items() if k not in ['source', 'src', 'destination', 'dest', 'id', 'action', 'desc']}
            ),
            'update_policy': lambda: client.update_policy(params),
            'delete_policy': lambda: client.delete_policy(params),
            'update_policy_state': lambda: client.update_policy_state(params),
            # 黑名单
            'get_ip_blacklist': lambda: client.get_ip_blacklist(),
            'add_ip_blacklist': lambda: client.add_ip_blacklist(params),
            'update_ip_blacklist': lambda: client.update_ip_blacklist(params),
            'delete_ip_blacklist': lambda: client.delete_ip_blacklist(params),
            'get_domain_blacklist': lambda: client.get_domain_blacklist(),
            'add_domain_blacklist': lambda: client.add_domain_blacklist(params),
            'delete_domain_blacklist': lambda: client.delete_domain_blacklist(params),
            # 威胁情报
            'get_threat_intelligence_switch': lambda: client.get_threat_intelligence_switch(),
            'update_threat_intelligence_switch': lambda: client.update_threat_intelligence_switch(params),
            'get_custom_intelligence': lambda: client.get_custom_intelligence(),
            'add_custom_intelligence': lambda: client.add_custom_intelligence(params),
            'update_custom_intelligence': lambda: client.update_custom_intelligence(params),
            'delete_custom_intelligence': lambda: client.delete_custom_intelligence(params),
            # 入侵防护
            'get_ips_templates': lambda: client.get_ips_templates(),
            'add_ips_template': lambda: client.add_ips_template(params),
            'update_ips_template': lambda: client.update_ips_template(params),
            'delete_ips_template': lambda: client.delete_ips_template(params),
            # 病毒防护
            'get_av_templates': lambda: client.get_av_templates(),
            'add_av_template': lambda: client.add_av_template(params),
            'update_av_template': lambda: client.update_av_template(params),
            'delete_av_template': lambda: client.delete_av_template(params),
            # 日志查询
            'get_firewall_logs': lambda: client.get_firewall_logs(params.get('sid', '1')),
            'export_firewall_logs': lambda: client.export_firewall_logs(
                params.get('type', 'TXT'),
                params.get('num', 1)
            ),
            # 系统管理
            'get_backup_version': lambda: client.get_backup_version(),
            'reboot_system': lambda: client.reboot_system(params.get('operation', 0)),
            'get_update_log': lambda: client.get_update_log(),
            # 地址对象
            'get_addresses': lambda: client.get_addresses(),
            'add_address': lambda: client.add_address(params),
            'update_address': lambda: client.update_address(params),
            'delete_address': lambda: client.delete_address(params),
        }

        if operation in operations:
            result = operations[operation]()
        else:
            result = {'error': f'不支持的操作: {operation}'}

    # 输出结果（原始JSON）
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
