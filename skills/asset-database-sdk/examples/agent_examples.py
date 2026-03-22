"""
资产库SDK使用示例代码
按Agent类型分类，提供常见场景的代码示例

版本: v4.0
更新日期: 2026-02-26
"""

import sys
sys.path.insert(0, 'teams/ai-security-team/asset-database')
from asset_sdk import AssetClient


# ==================== server-ops 示例 ====================

def server_ops_get_credentials(asset_id):
    """
    server-ops: 获取服务器SSH连接凭据

    场景: 需要SSH连接到服务器执行命令
    """
    client = AssetClient()

    # 获取资产详情
    asset = client.get_asset(asset_id)
    if not asset:
        print(f"资产 {asset_id} 不存在")
        return None

    # 获取密码（解密）
    password = client.get_password(asset_id)

    # 组装连接信息
    credentials = {
        'host': asset['ip_address'],
        'port': asset.get('ssh_port', 22),
        'username': asset['username'],
        'password': password,
        'hostname': asset.get('hostname', '')
    }

    return credentials


def server_ops_list_production_servers():
    """
    server-ops: 列出生产环境服务器

    场景: 需要对生产服务器进行批量操作
    """
    client = AssetClient()

    servers = client.list_assets(
        asset_type="Server",
        environment="production",
        status="active"
    )

    print(f"生产环境活跃服务器: {len(servers)} 台")
    return servers


def server_ops_update_hardware_info(asset_id, cpu_cores, memory_gb, disk_gb):
    """
    server-ops: 更新服务器硬件信息

    场景: 硬件升级后更新资产信息
    """
    client = AssetClient()

    result = client.update_asset(
        asset_id,
        cpu_cores=cpu_cores,
        memory_gb=memory_gb,
        disk_gb=disk_gb,
        changed_by='server-ops',
        change_reason='硬件升级'
    )

    if result:
        print(f"硬件信息已更新")
    else:
        print(f"更新失败")

    return result


# ==================== network-ops 示例 ====================

def network_ops_list_devices_by_role(device_role):
    """
    network-ops: 按设备角色查询网络设备

    场景: 查询核心交换机、汇聚交换机等
    """
    client = AssetClient()

    devices = client.list_assets(
        asset_type="NetworkDevice",
        device_role=device_role
    )

    print(f"设备角色 '{device_role}': {len(devices)} 台")
    return devices


def network_ops_get_vlan_info(asset_id):
    """
    network-ops: 获取设备VLAN信息

    场景: 查看设备配置的VLAN
    """
    client = AssetClient()

    device = client.get_asset(asset_id)
    if not device:
        return None

    vlan_ids = device.get('vlan_ids', [])
    network_segment = device.get('network_segment', '')

    return {
        'vlan_ids': vlan_ids,
        'network_segment': network_segment
    }


def network_ops_query_network_topology():
    """
    network-ops: 查询网络拓扑关系

    场景: 可视化网络设备连接关系
    """
    client = AssetClient()

    # 获取所有网络设备
    devices = client.list_assets(asset_type="NetworkDevice")

    topology = []
    for device in devices:
        # 获取该设备的所有关系
        relationships = client.get_relationships(device['asset_id'])

        for rel in relationships:
            topology.append({
                'source': device['name'],
                'target': rel.get('target_name', rel.get('source_name', '')),
                'type': rel['relation_type'],
                'description': rel['description']
            })

    return topology


# ==================== threat-response 示例 ====================

def threat_response_isolate_asset(asset_id, reason):
    """
    threat-response: 隔离资产

    场景: 检测到安全事件时隔离资产
    """
    client = AssetClient()

    result = client.update_asset(
        asset_id,
        status='isolated',
        isolation_status='network',
        risk_score=85,
        changed_by='threat-response',
        change_reason=reason
    )

    if result:
        print(f"资产已隔离: {asset_id}")
    else:
        print(f"隔离失败")

    return result


def threat_response_get_high_risk_assets(min_score=60):
    """
    threat-response: 获取高风险资产

    场景: 识别需要重点关注的高风险资产
    """
    client = AssetClient()

    high_risk = client.list_assets_by_risk(min_score=min_score, max_score=100)

    print(f"高风险资产 (>={min_score}分): {len(high_risk)} 个")
    return high_risk


def threat_response_get_incident_report():
    """
    threat-response: 生成事件报告

    场景: 安全事件处理后生成报告
    """
    client = AssetClient()

    report = client.get_risk_report(
        min_score=50,
        include_details=True
    )

    return report


# ==================== asset-mgmt 示例 ====================

def asset_mgmt_batch_import(assets):
    """
    asset-mgmt: 批量导入资产

    场景: 从外部系统批量导入资产数据
    """
    client = AssetClient()

    # 试运行
    result = client.batch_create(assets, dry_run=True)
    print(f"预计创建: {result['total']}, 无效: {result['invalid_count']}")

    # 执行导入
    if result['invalid_count'] == 0:
        result = client.batch_create(assets, dry_run=False, changed_by="asset-mgmt")
        print(f"导入成功: {result['success_count']}, 失败: {result['failed_count']}")
    else:
        print("发现无效数据，请修复后重试")

    return result


def asset_mgmt_get_dashboard_stats():
    """
    asset-mgmt: 获取仪表板统计数据

    场景: 资产管理仪表板显示
    """
    client = AssetClient()

    stats = client.get_statistics(
        by_type=True,
        by_status=True,
        by_importance=True
    )

    return stats


def asset_export_assets(output_format='json'):
    """
    asset-mgmt: 导出资产数据

    场景: 导出资产用于审计或迁移
    """
    client = AssetClient()

    data = client.export_assets(format=output_format)

    if output_format == 'json':
        import json
        return json.loads(data)
    return data


# ==================== vuln-assessment 示例 ====================

def vuln_assessment_get_scan_targets():
    """
    vuln-assessment: 获取扫描目标

    场景: 漏洞扫描前获取需要扫描的资产
    """
    client = AssetClient()

    targets = client.list_assets(
        asset_type="Server",
        environment="production",
        status="active"
    )

    print(f"扫描目标: {len(targets)} 台服务器")
    return targets


def vuln_assessment_update_vulnerability_info(asset_id, vuln_count, severity):
    """
    vuln-assessment: 更新漏洞信息

    场景: 漏洞扫描完成后更新资产漏洞数据
    """
    client = AssetClient()

    # 根据严重程度计算风险评分
    risk_score_map = {
        'critical': 90,
        'high': 75,
        'medium': 50,
        'low': 30
    }
    risk_score = risk_score_map.get(severity.lower(), 40)

    result = client.update_asset(
        asset_id,
        vulnerability_count=vuln_count,
        risk_score=risk_score,
        changed_by='vuln-assessment',
        change_reason=f'完成漏洞扫描，发现{vuln_count}个{severity}级漏洞'
    )

    if result:
        print(f"漏洞信息已更新")
    else:
        print(f"更新失败")

    return result


def vuln_assessment_get_high_risk_assets(min_score=60):
    """
    vuln-assessment: 按风险分数查询资产

    场景: 识别需要重点关注的资产
    """
    client = AssetClient()

    high_risk = client.list_assets_by_risk(min_score=min_score)

    print(f"高风险资产 (>{min_score}分): {len(high_risk)} 个")
    return high_risk


def vuln_assessment_generate_vulnerability_report():
    """
    vuln-assessment: 生成漏洞报告

    场景: 定期生成漏洞评估报告
    """
    client = AssetClient()

    report = client.get_risk_report(
        min_score=50,
        include_details=True
    )

    return report


# ==================== compliance 示例 ====================

def compliance_get_critical_assets():
    """
    compliance: 获取关键资产列表

    场景: 合规检查重点审查关键资产
    """
    client = AssetClient()

    critical_assets = client.list_assets(importance='critical')

    print(f"关键资产: {len(critical_assets)} 个")
    return critical_assets


def compliance_get_production_assets():
    """
    compliance: 获取生产环境资产

    场景: 合规检查需要覆盖所有生产资产
    """
    client = AssetClient()

    prod_assets = client.list_assets(environment='production')

    print(f"生产环境资产: {len(prod_assets)} 个")
    return prod_assets


def compliance_get_multi_dimension_stats():
    """
    compliance: 多维度统计分析

    场景: 合规报告需要多维度数据
    """
    client = AssetClient()

    stats = client.get_statistics(
        by_type=True,
        by_status=True,
        by_importance=True
    )

    return stats


# ==================== incident-response 示例 ====================

def incident_response_get_affected_assets():
    """
    incident-response: 获取受影响资产详情

    场景: 安全事件发生后识别受影响范围
    """
    client = AssetClient()

    # 假设资产ID列表
    affected_ids = ["id1", "id2", "id3"]

    # 批量获取受影响资产
    affected_assets = client.batch_get(affected_ids)

    print(f"受影响资产: {len(affected_assets)} 个")
    return affected_assets


def incident_response_get_change_history(asset_id):
    """
    incident-response: 查询资产变更历史

    场景: 分析事件时间线，追踪资产变更
    """
    client = AssetClient()

    history = client.get_change_history(asset_id, limit=50)

    return history


def incident_response_get_impact_relationships(asset_id):
    """
    incident-response: 获取资产关系用于影响分析

    场景: 分析资产依赖关系，评估影响范围
    """
    client = AssetClient()

    relations = client.get_relationships(asset_id)

    return relations


# ==================== alert-judgment 示例 ====================

def alert_judgment_get_asset_importance(asset_id):
    """
    alert-judgment: 获取资产重要性信息

    场景: 告警优先级排序时参考资产重要性
    """
    client = AssetClient()

    asset = client.get_asset(asset_id)
    if not asset:
        return None

    importance = asset.get('importance', 'medium')

    return importance


def alert_judgment_batch_get_related_assets(asset_ids):
    """
    alert-judgment: 批量获取相关资产

    场景: 告警事件关联时获取相关资产信息
    """
    client = AssetClient()

    related_assets = client.batch_get(asset_ids)

    return related_assets


def alert_judgment_get_asset_relations(asset_id):
    """
    alert-judgment: 获取资产关系用于事件关联

    场景: 关联多个告警，识别攻击链
    """
    client = AssetClient()

    relations = client.get_relationships(asset_id)

    return relations


# ==================== pentest 示例 ====================

def pentest_get_target_asset(asset_id):
    """
    pentest: 获取测试目标资产

    场景: 渗透测试前获取目标信息
    """
    client = AssetClient()

    asset = client.get_asset(asset_id)
    if not asset:
        return None

    return asset


def pentest_get_credentials(asset_id):
    """
    pentest: 获取资产登录凭据

    场景: 授权渗透测试时需要登录凭证
    """
    client = AssetClient()

    password = client.get_password(asset_id)
    ssh_port = asset.get('ssh_port', 22)
    username = asset['username']

    return {
        'password': password,
        'ssh_port': ssh_port,
        'username': username,
        'ip_address': asset['ip_address']
    }


def pentest_update_test_results(asset_id, vuln_count, vuln_details):
    """
    pentest: 更新测试结果

    场景: 渗透测试完成后记录结果
    """
    client = AssetClient()

    result = client.update_asset(
        asset_id,
        vuln_count=vuln_count,
        changed_by='pentest',
        change_reason='完成渗透测试'
    )

    return result


# ==================== threat-response 示例 ====================

def threat_response_get_audit_logs(asset_id):
    """
    threat-response: 查询资产审计日志

    场景: 分析资产变更历史
    """
    client = AssetClient()

    from datetime import datetime, timedelta

    logs = client.get_audit_logs(
        asset_id=asset_id,
        change_type='update',
        start_date=datetime.now() - timedelta(days=7),
        limit=50
    )

    return logs


# ==================== network-ops 示例 ====================

def network_ops_list_devices():
    """
    network-ops: 列出所有网络设备
    """
    client = AssetClient()

    devices = client.list_assets(asset_type="NetworkDevice")

    print(f"网络设备: {len(devices)} 台")
    return devices


# ==================== server-ops 示例 ====================

def server_ops_list_servers():
    """
    server-ops: 列出所有服务器
    """
    client = AssetClient()

    servers = client.list_assets(asset_type="Server")

    print(f"服务器: {len(servers)} 台")
    return servers


# ==================== asset-mgmt 示例 ====================

def asset_mgmt_health_check(asset_ids):
    """
    asset-mgmt: 批量健康检查

    场景: 定期检查资产状态
    """
    client = AssetClient()

    result = client.health_check(
        asset_ids=asset_ids,
        check_type="connectivity"
    )

    return result


# ==================== 通用示例 ====================

def common_search_assets(keyword):
    """
    通用: 关键字搜索资产

    场景: 不确定具体字段时使用关键字搜索
    """
    client = AssetClient()

    results = client.find_assets(keyword, limit=20)

    print(f"搜索 '{keyword}' 找到 {len(results)} 个结果")
    return results


def common_get_asset_by_any_identifier(identifier):
    """
    通用: 通过任意标识符获取资产

    场景: 可能是IP、名称或ID
    """
    client = AssetClient()

    # 尝试按ID查询
    asset = client.get_asset(identifier)
    if asset:
        return asset

    # 尝试按IP查询
    asset = client.get_asset_by_ip(identifier)
    if asset:
        return asset

    # 尝试按名称查询
    asset = client.get_asset_by_name(identifier)
    if asset:
        return asset

    return None


if __name__ == "__main__":
    # 示例: 列出生产环境服务器
    servers = server_ops_list_production_servers()
