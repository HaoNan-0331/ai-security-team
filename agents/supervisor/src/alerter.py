"""
监管员告警模块

功能：
- 检测告警触发条件
- 生成告警内容
- 调用邮件网关发送邮件到 1466160825@qq.com
- 记录告警历史到JSON Lines文件

使用示例：
    from alerter import Alerter

    alerter = Alerter()

    # 检查并发送告警
    alert = alerter.check_and_alert(
        agent_id="pentest",
        violation_type="collaboration_rule_violation",
        consecutive_count=3
    )
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class AlertRecord:
    """告警记录"""
    timestamp: str
    alert_id: str
    alert_type: str  # consecutive_violation / low_score_streak / serious_violation / score_improvement
    severity: str  # critical / warning / info
    agent_id: str
    title: str
    message: str
    related_violations: List[str]
    email_sent: bool = False
    email_recipient: str = ""
    email_timestamp: str = ""
    status: str = "pending"  # pending / sent / failed

    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = f"ALT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'type': 'alert',
            'alert_id': self.alert_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'agent_id': self.agent_id,
            'title': self.title,
            'message': self.message,
            'related_violations': self.related_violations,
            'email_sent': self.email_sent,
            'email_recipient': self.email_recipient,
            'email_timestamp': self.email_timestamp,
            'status': self.status
        }


class Alerter:
    """
    告警模块

    负责：
    - 检测告警触发条件
    - 生成告警内容
    - 调用邮件网关发送邮件
    - 记录告警历史

    Attributes:
        data_dir: 数据存储目录
        alerts_file: 告警记录文件路径
        email_recipient: 默认邮件收件人（1466160825@qq.com）
        alert_rules: 告警规则配置
    """

    # 告警规则配置
    ALERT_RULES = {
        'consecutive_violations': {
            'name': '同类型违规连续发生',
            'description': '同一种违规类型在24小时内发生多次',
            'threshold': 3,
            'time_window': '24h',
            'severity': 'critical',
            'message_template': 'Agent {agent_id} 在过去24小时内，同一种违规类型（{violation_type}）已发生 {count} 次，达到严重告警阈值。'
        },
        'low_score_streak': {
            'name': '低分连续',
            'description': '综合评分连续多次低于60分',
            'threshold': 3,
            'severity': 'warning',
            'message_template': 'Agent {agent_id} 的综合评分已连续 {count} 次低于60分，当前评分 {current_score}，需要关注和改进。'
        },
        'serious_violation': {
            'name': '严重违规',
            'description': '发生严重级别的违规（如严重越权）',
            'threshold': 1,
            'severity': 'critical',
            'message_template': '【紧急】Agent {agent_id} 发生严重违规（{violation_type}）：{description}，请立即处理！'
        },
        'score_improvement': {
            'name': '评分连续提升',
            'description': 'Agent评分连续多次提升',
            'threshold': 3,
            'severity': 'info',
            'message_template': 'Agent {agent_id} 的评分已连续 {count} 次提升，从 {initial_score} 提升到 {current_score}，表现优秀！'
        }
    }

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        email_recipient: str = "1466160825@qq.com"
    ):
        """
        初始化告警模块

        Args:
            data_dir: 数据存储目录（默认上级目录的data/raw）
            email_recipient: 默认邮件收件人（默认1466160825@qq.com）
        """
        self.data_dir = data_dir or (Path(__file__).parent.parent / "data" / "raw")
        self.alerts_file = self.data_dir / "alerts.jsonl"
        self.email_recipient = email_recipient

        # 确保目录存在
        self._init_directories()

        # 邮件网关（懒加载）
        self._email_gateway = None

        print(f"[Alerter] 告警模块初始化完成")
        print(f"[Alerter] 数据目录: {self.data_dir}")
        print(f"[Alerter] 邮件收件人: {self.email_recipient}")

    def _init_directories(self):
        """初始化存储目录"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_email_gateway(self):
        """获取邮件网关（懒加载）"""
        if self._email_gateway is None:
            # 导入邮件网关
            import sys
            gateway_path = Path(__file__).parent.parent.parent.parent / "tools" / "email-gateway"
            if str(gateway_path) not in sys.path:
                sys.path.insert(0, str(gateway_path))

            from email_gateway import EmailGateway
            self._email_gateway = EmailGateway()

        return self._email_gateway

    def _generate_alert_message(
        self,
        alert_type: str,
        agent_id: str,
        **kwargs
    ) -> Tuple[str, str, str]:
        """
        生成告警内容

        Returns:
            (标题, 消息内容, 严重程度)
        """
        rule = self.ALERT_RULES.get(alert_type, {})
        severity = rule.get('severity', 'warning')
        template = rule.get('message_template', '告警: {agent_id}')

        # 生成标题
        titles = {
            'critical': '【紧急告警】',
            'warning': '【警告】',
            'info': '【通知】'
        }
        title = titles.get(severity, '【告警】') + rule.get('name', '未知告警')

        # 生成消息
        message = template.format(agent_id=agent_id, **kwargs)

        return title, message, severity

    def check_and_alert(
        self,
        agent_id: str,
        violation_type: str,
        consecutive_count: int,
        description: str = "",
        **kwargs
    ) -> Optional[AlertRecord]:
        """
        检查并发送告警

        Args:
            agent_id: Agent标识符
            violation_type: 违规类型
            consecutive_count: 连续违规次数
            description: 违规描述
            **kwargs: 其他参数

        Returns:
            AlertRecord: 告警记录（如触发告警），否则None
        """
        # 确定告警类型
        alert_type = None

        if violation_type == 'unauthorized_execution' and consecutive_count >= 1:
            alert_type = 'serious_violation'
        elif consecutive_count >= 3:
            alert_type = 'consecutive_violations'
        elif kwargs.get('low_score_streak', 0) >= 3:
            alert_type = 'low_score_streak'

        if not alert_type:
            print(f"[Alerter] {agent_id}: 未达到告警阈值（连续{consecutive_count}次）")
            return None

        # 生成告警内容
        title, message, severity = self._generate_alert_message(
            alert_type=alert_type,
            agent_id=agent_id,
            violation_type=violation_type,
            count=consecutive_count,
            description=description,
            **kwargs
        )

        print(f"[Alerter] 触发告警: {title} ({severity})")

        # 创建告警记录
        record = AlertRecord(
            timestamp=datetime.now().isoformat(),
            alert_id=f"ALT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            alert_type=alert_type,
            severity=severity,
            agent_id=agent_id,
            title=title,
            message=message,
            related_violations=kwargs.get('violation_ids', []),
            email_sent=False,
            email_recipient=self.email_recipient,
            status='pending'
        )

        # 写入文件
        self._write_alert(record)

        # 发送邮件
        try:
            self._send_alert_email(record)
            record.email_sent = True
            record.email_timestamp = datetime.now().isoformat()
            record.status = 'sent'

            # 更新文件中的状态
            self._update_alert_status(record)

            print(f"[Alerter] 邮件已发送至 {self.email_recipient}")

        except Exception as e:
            record.status = 'failed'
            print(f"[Alerter] 邮件发送失败: {e}")

        return record

    def _write_alert(self, record: AlertRecord):
        """写入告警记录到JSON Lines文件"""
        with open(self.alerts_file, 'a', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, ensure_ascii=False)
            f.write('
')

    def _update_alert_status(self, record: AlertRecord):
        """更新告警状态（简化实现：追加新记录）"""
        # 实际生产环境应该用数据库或文件锁
        # 这里简化处理：追加一条状态更新记录
        status_update = {
            'timestamp': datetime.now().isoformat(),
            'type': 'alert_status_update',
            'alert_id': record.alert_id,
            'email_sent': record.email_sent,
            'email_timestamp': record.email_timestamp,
            'status': record.status
        }

        with open(self.alerts_file, 'a', encoding='utf-8') as f:
            json.dump(status_update, f, ensure_ascii=False)
            f.write('
')

    def _send_alert_email(self, record: AlertRecord):
        """发送告警邮件"""
        gateway = self._get_email_gateway()

        # 根据严重程度选择发送方式
        if record.severity == 'critical':
            # 严重告警：使用incident_alert方法
            gateway.send_incident_alert(
                incident_type=record.alert_type,
                severity=record.severity,
                description=record.title,
                details={
                    'message': record.message,
                    'agent_id': record.agent_id,
                    'alert_id': record.alert_id
                }
            )
        else:
            # 普通告警：直接发送邮件
            gateway.send_email(
                to=[self.email_recipient],
                subject=record.title,
                content=f"""
                <h3>{record.title}</h3>
                <p><strong>Agent:</strong> {record.agent_id}</p>
                <p><strong>严重程度:</strong> {record.severity}</p>
                <p><strong>告警ID:</strong> {record.alert_id}</p>
                <hr>
                <p>{record.message}</p>
                """,
                content_type="html",
                priority="high" if record.severity == "critical" else "normal"
            )


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("监管员告警模块 - 使用示例")
    print("=" * 60)

    # 创建告警器
    alerter = Alerter(
        email_recipient="1466160825@qq.com"
    )

    print("\n【示例1】连续违规告警（达到阈值）")
    print("-" * 60)

    # 模拟连续3次违规，触发告警
    alert = alerter.check_and_alert(
        agent_id="pentest",
        violation_type="collaboration_rule_violation",
        consecutive_count=3,
        description="未先寻求Agent协作直接上报人类",
        violation_ids=["VIO-20250219-001", "VIO-20250219-002", "VIO-20250219-003"]
    )

    if alert:
        print(f"✓ 告警已触发: {alert.title}")
        print(f"  告警ID: {alert.alert_id}")
        print(f"  严重程度: {alert.severity}")
        print(f"  邮件状态: {'已发送' if alert.email_sent else '发送失败'}")
    else:
        print("✗ 未达到告警阈值")

    print("\n【示例2】严重违规告警（立即触发）")
    print("-" * 60)

    # 严重违规，1次就触发
    alert2 = alerter.check_and_alert(
        agent_id="network-ops",
        violation_type="unauthorized_execution",
        consecutive_count=1,
        description="执行了超出能力范围的防火墙配置，应属于policy-exec职责",
        violation_ids=["VIO-20250219-005"]
    )

    if alert2:
        print(f"✓ 告警已触发: {alert2.title}")
        print(f"  告警ID: {alert2.alert_id}")
        print(f"  严重程度: {alert2.severity}")
        print(f"  邮件收件人: {alert2.email_recipient}")

    print("\n【示例3】未达到告警阈值")
    print("-" * 60)

    # 只有2次违规，未达到3次阈值
    alert3 = alerter.check_and_alert(
        agent_id="vuln-assessment",
        violation_type="execution_error",
        consecutive_count=2,
        description="执行操作产生错误",
        violation_ids=["VIO-20250219-010", "VIO-20250219-011"]
    )

    if alert3:
        print(f"✓ 告警已触发")
    else:
        print(f"✗ 未达到告警阈值（连续2次，需要3次）")

    print("\n" + "=" * 60)
    print("告警模块示例运行完成！")
    print("=" * 60)
