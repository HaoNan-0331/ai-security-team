"""
监管员违规检测引擎

功能：
- 三种违规类型检测：越权执行、违反协作规则、错误执行
- 连续违规统计（24小时窗口）
- 违规记录写入JSON Lines文件
- 触发告警条件判断

使用示例：
    from detector import Detector

    detector = Detector()

    # 检测越权执行
    violation = detector.check_unauthorized_execution(
        agent_id="network-ops",
        action_type="configure_firewall",
        target_resource="firewall-01"
    )
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict



@dataclass
class ViolationRecord:
    """违规记录"""
    timestamp: str
    violation_id: str
    agent_id: str
    violation_type: str  # unauthorized_execution / collaboration_rule_violation / execution_error
    subtype: Optional[str]  # 子类型
    severity: str  # critical / high / medium / low
    description: str
    evidence: Dict[str, Any]  # 证据信息
    score_deduction: int
    consecutive_count: int  # 连续违规次数
    triggered_alert: bool = False
    alert_id: str = ""


    def __post_init__(self):
        if not self.violation_id:
            self.violation_id = f"VIO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        return {
            'timestamp': self.timestamp,
            'type': 'violation',
            'violation_id': self.violation_id,
            'agent_id': self.agent_id,
            'violation_type': self.violation_type,
            'subtype': self.subtype,
            'severity': self.severity,
            'description': self.description,
            'evidence': self.evidence,
            'score_deduction': self.score_deduction,
            'consecutive_count': self.consecutive_count,
            'triggered_alert': self.triggered_alert,
            'alert_id': self.alert_id
        }



class Detector:
    """
    违规检测引擎

    负责：
    - 三种违规类型检测
    - 连续违规统计
    - 违规记录写入JSONL
    - 触发告警条件判断

    """

    # 违规类型定义
    VIOLATION_TYPES = {
        'unauthorized_execution': {
            'name': '越权执行',
            'description': '执行了超出能力范围的任务',
            'severity_map': {
                'critical': 'critical',
                'high': 'high',
                'medium': 'medium',
                'low': 'low'
            },
            'score_deduction': 40
        },
        'collaboration_rule_violation': {
            'name': '违反协作规则',
            'description': '未优先寻求Agent协作，直接上报人类或擅自处理',
            'severity_map': {
                'direct_escalation': 'medium',
                'unauthorized_handling': 'high'
            },
            'score_deduction': 30
        },
        'execution_error': {
            'name': '错误执行',
            'description': '执行操作产生错误或失败',
            'severity_map': {
                'critical': 'high',
                'high': 'medium',
                'medium': 'low',
                'low': 'info'
            },
            'score_deduction': 50
        }
    }

    # 能力边界定义（用于越权检测）
    AGENT_CAPABILITIES = {
        'orchestrator': ['task_assign', 'task_coordination', 'result_aggregation', 'human_communication'],
        'log-analysis': ['log_collection', 'log_parsing', 'anomaly_detection', 'behavior_analysis', 'trend_analysis'],
        'alert-judgment': ['alert_classification', 'priority_sorting', 'false_positive_filtering', 'event_correlation'],
                'asset-mgmt': ['asset_scanning', 'asset_identification', 'asset_classification', 'change_monitoring'],
        'threat-response': ['threat_containment', 'threat_elimination', 'system_repair', 'recovery_verification'],
        'incident-response': ['response_initiation', 'plan_execution', 'resource_coordination', 'progress_tracking'],
        'forensic': ['evidence_collection', 'evidence_preservation', 'memory_analysis', 'disk_analysis', 'traceability_analysis'],
        'policy-exec': ['policy_parsing', 'device_configuration', 'policy_deployment', 'compliance_checking'],
        'vuln-assessment': ['vulnerability_scanning', 'vulnerability_verification', 'risk_assessment', 'remediation_priority'],
        'pentest': ['penetration_testing', 'vulnerability_exploitation', 'attack_simulation', 'security_assessment'],
        'compliance': ['compliance_checking', 'control_assessment', 'evidence_collection', 'gap_analysis'],
        'risk-assessment': ['risk_identification', 'risk_analysis', 'risk_quantification', 'remediation_recommendation'],
        'network-ops': ['network_device_config', 'route_management', 'troubleshooting', 'performance_monitoring'],
        'server-ops': ['server_management', 'service_deployment', 'performance_monitoring', 'fault_handling'],
        'endpoint-ops': ['endpoint_management', 'software_management', 'config_management', 'security_policy_enforcement'],
        'change-mgmt': ['change_request_processing', 'risk_assessment', 'approval_workflow', 'implementation_scheduling'],
        'patch-mgmt': ['patch_scanning', 'testing_verification', 'deployment_scheduling', 'compliance_checking']
    }

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        consecutive_window: int = 86400  # 24小时 = 86400秒
    ):
        """
        初始化违规检测引擎

        Args:
            data_dir: 数据存储目录（默认上级目录的data/raw）
            consecutive_window: 连续违规统计窗口（秒，默认24小时）
        """
        self.data_dir = data_dir or (Path(__file__).parent.parent / "data" / "raw")
        self.violations_file = self.data_dir / "violations.jsonl"
        self.consecutive_window = consecutive_window

        # 内存缓存：每个Agent的违规历史
        # 格式：{agent_id: [violation1, violation2, ...]}
        self.agent_violations: Dict[str, List[Dict[str, Any]] = defaultdict(list)
        # 确保目录存在
        self._init_directories()
        print(f"[Detector] 违规检测引擎初始化完成")
        print(f"[Detector] 数据目录: {self.data_dir}")
        print(f"[Detector] 连续违规窗口: {consecutive_window}秒 ({consecutive_window // 3600}小时)")

    def _init_directories(self):
        """初始化存储目录"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_consecutive_violation_count(
        self,
        agent_id: str,
        violation_type: str
    ) -> int:
        """获取连续违规次数"""
        violations = self.agent_violations.get(agent_id, [])
        # 筛选同类型的违规
        same_type_violations = [
            v for v in violations
            if v.get('violation_type') == violation_type
        ]
        # 计算在时间窗口内的连续违规
        cutoff_time = datetime.now() - timedelta(seconds=self.consecutive_window)
        consecutive_count = 0
        for v in reversed(same_type_violations):
            v_time = datetime.fromisoformat(v.get('timestamp', ''))
            if v_time >= cutoff_time:
                consecutive_count += 1
            else:
                break
        return consecutive_count

    def check_unauthorized_execution(
        self,
        agent_id: str,
        action_type: str,
        target_resource: str,
        impact_level: str = "medium",
        evidence: Optional[Dict[str, Any]] = None
    ) -> Optional[ViolationRecord]:
        """
        检测越权执行违规

        Args:
            agent_id: Agent标识符
            action_type: 动作类型
            target_resource: 目标资源
            impact_level: 影响程度（critical/high/medium/low）
            evidence: 证据信息

        Returns:
            ViolationRecord: 违规记录（如检测到违规），否则None
        """
        # 获取Agent的能力列表
        capabilities = self.AGENT_CAPABILITIES.get(agent_id, [])
        # 检查动作是否在能力范围内
        if action_type in capabilities:
            # 在能力范围内，不是违规
            return None
        # 检测为越权执行违规
        print(f"[Detector] 检测到越权执行: {agent_id} 执行 {action_type}（超出能力范围）")
        # 映射严重程度
        severity_map = self.VIOLATION_TYPES['unauthorized_execution']['severity_map']
        severity = severity_map.get(impact_level, 'medium')
        # 计算扣分
        base_deduction = self.VIOLATION_TYPES['unauthorized_execution']['score_deduction']
        # 根据严重程度调整扣分
        severity_multiplier = {
            'critical': 1.5,
            'high': 1.2,
            'medium': 1.0,
            'low': 0.8
        }
        score_deduction = int(base_deduction * severity_multiplier.get(impact_level, 1.0))
        # 统计连续违规
        consecutive_count = self._get_consecutive_violation_count(agent_id, 'unauthorized_execution')
        # 创建违规记录
        violation = ViolationRecord(
            timestamp=datetime.now().isoformat(),
            violation_id=f"VIO-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            agent_id=agent_id,
            violation_type='unauthorized_execution',
            subtype=None,
            severity=severity,
            description=f"Agent {agent_id} 执行了超出能力范围的操作: {action_type} on {target_resource}",
            evidence={
                'action_type': action_type,
                'target_resource': target_resource,
                'agent_capabilities': capabilities,
                'impact_level': impact_level,
                **(evidence or {})
            },
            score_deduction=score_deduction,
            consecutive_count=consecutive_count
        )
        # 检查是否触发告警
        if severity == 'critical' or consecutive_count >= 3:
            violation.triggered_alert = True
            print(f"[Detector] 违规触发告警: {violation.violation_id}")
        # 写入文件
        self._write_violation(violation)
        # 更新内存缓存
        self._update_agent_violations(agent_id, violation)
        return violation

    def _write_violation(self, violation: ViolationRecord):
        """写入违规记录到JSON Lines文件"""
        with open(self.violations_file, 'a', encoding='utf-8') as f:
            json.dump(violation.to_dict(), f, ensure_ascii=False)
            f.write('
')

    def _update_agent_violations(self, agent_id: str, violation: ViolationRecord):
        """更新Agent的违规历史缓存"""
        if agent_id not in self.agent_violations:
            self.agent_violations[agent_id] = []
        self.agent_violations[agent_id].append(violation.to_dict())

        # 清理过期的违规记录（保留30天）
        cutoff_time = datetime.now() - timedelta(days=30)
        self.agent_violations[agent_id] = [
            v for v in self.agent_violations[agent_id]
            if datetime.fromisoformat(v.get('timestamp', '')) >= cutoff_time
        ]


# ==================== 使用示例 ====================


if __name__ == "__main__":
    print("=" * 60)
    print("监管员违规检测引擎 - 使用示例")
    print("=" * 60)

    # 创建检测器
    detector = Detector()


    print("\n【示例1】检测越权执行违规")
    print("-" * 60)

    # network-ops 尝试配置防火墙（超出其能力范围）
    violation1 = detector.check_unauthorized_execution(
        agent_id="network-ops",
        action_type="configure_firewall",
        target_resource="firewall-01",
        impact_level="high",
        evidence={
            'requested_config': 'firewall policy update',
            'reason': 'network-ops does not have firewall management capability'
        }
    )

    if violation1:
        print(f"✓ 检测到越权执行违规!")
        print(f"  违规ID: {violation1.violation_id}")
        print(f"  Agent: {violation1.agent_id}")
        print(f"  严重程度: {violation1.severity}")
        print(f"  扣分: {violation1.score_deduction}")
        print(f"  连续次数: {violation1.consecutive_count}")
        print(f"  触发告警: {'是' if violation1.triggered_alert else '否'}")
    else:
        print("✗ 未检测到违规")

    print("\n【示例2】检测越权执行（在能力范围内，不违规）")
    print("-" * 60)

    # policy-exec 配置防火墙（在其能力范围内，不应检测为违规）
    violation2 = detector.check_unauthorized_execution(
        agent_id="policy-exec",
        action_type="configure_firewall",
        target_resource="firewall-02",
        impact_level="medium"
    )

    if violation2:
        print(f"✓ 检测到违规")
    else:
        print("✗ 未检测到违规（在能力范围内，正常操作）")

    print("\n【示例3】连续违规统计")
    print("-" * 60)


    # 模拟多次违规，测试连续计数
    for i in range(3):
        v = detector.check_unauthorized_execution(
            agent_id="test-agent",
            action_type="unauthorized_action",
            target_resource=f"resource-{i}",
            impact_level="medium"
        )
        if v:
            print(f"  第{i+1}次违规，连续计数: {v.consecutive_count}")

    print("\n违规检测引擎示例运行完成！")
    print("=" * 60)
