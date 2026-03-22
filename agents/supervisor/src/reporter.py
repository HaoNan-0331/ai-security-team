"""
监管员报告生成器

功能：
- 从JSON Lines文件读取监控数据
- 生成Markdown格式的报告（日报、周报、月报）
- 生成统计图表（文本格式）
- 生成Agent对比分析

使用示例：
    from reporter import Reporter

    reporter = Reporter()

    # 生成日报
    daily_report = reporter.generate_daily_report(date="2026-02-19")
    reporter.save_report(daily_report, "daily/2026-02-19.md")

    # 生成周报
    weekly_report = reporter.generate_weekly_report(week="2026-W08")
    reporter.save_report(weekly_report, "weekly/2026-W08.md")
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter



class Reporter:
    """
    报告生成器

    负责：
    - 从JSONL读取数据
    - 生成Markdown报告
    - 统计分析和对比
    - 报告文件管理

    Attributes:
        data_dir: 数据目录（JSONL文件）
        reports_dir: 报告输出目录
        template_dir: 模板目录（可选）
    """

    # 报告模板
    DAILY_REPORT_TEMPLATE = """# 监管日报 - {date}

## 概览

| 指标 | 数值 |
|------|------|
| 监控Agent数 | {total_agents} |
| 总消息数 | {total_messages} |
| 平均评分 | {avg_score} |
| 违规次数 | {total_violations} |
| 告警次数 | {total_alerts} |

## Agent评分排行

| 排名 | Agent | 综合评分 | 评级 |
|------|-------|----------|------|
{ranking_table}

## 违规记录

{violations_section}

## 告警记录

{alerts_section}

## 待关注

{watch_list}

---

*本报告由监管员自动生成*
*生成时间: {generation_time}*
"""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        reports_dir: Optional[Path] = None
    ):
        """
        初始化报告生成器

        Args:
            data_dir: 数据目录（默认上级目录的data/raw）
            reports_dir: 报告输出目录（默认上级目录的reports）
        """
        self.data_dir = data_dir or (Path(__file__).parent.parent / "data" / "raw")
        self.reports_dir = reports_dir or (Path(__file__).parent.parent / "reports")

        # 确保目录存在
        self._init_directories()

        print(f"[Reporter] 报告生成器初始化完成")
        print(f"[Reporter] 数据目录: {self.data_dir}")
        print(f"[Reporter] 报告目录: {self.reports_dir}")

    def _init_directories(self):
        """初始化存储目录"""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        (self.reports_dir / "daily").mkdir(exist_ok=True)
        (self.reports_dir / "weekly").mkdir(exist_ok=True)
        (self.reports_dir / "monthly").mkdir(exist_ok=True)

    def _read_jsonl(self, filename: str) -> List[Dict[str, Any]]:
        """读取JSON Lines文件"""
        filepath = self.data_dir / filename
        records = []

        if not filepath.exists():
            return records

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError:
                    continue

        return records

    def generate_daily_report(self, date: Optional[str] = None) -> str:
        """
        生成日报

        Args:
            date: 日期（默认昨天），格式：YYYY-MM-DD


        Returns:
            str: Markdown格式的日报
        """
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')


        print(f"[Reporter] 生成日报: {date}")

        # 读取数据
        communications = self._read_jsonl('communications.jsonl')
        executions = self._read_jsonl('executions.jsonl')
        evaluations = self._read_jsonl('evaluations.jsonl')
        violations = self._read_jsonl('violations.jsonl')
        alerts = self._read_jsonl('alerts.jsonl')
        # 过滤指定日期的数据
        def filter_by_date(records: List[Dict], date_str: str) -> List[Dict]:
            return [
                r for r in records
                if r.get('timestamp', '').startswith(date_str)
            ]
        comm_data = filter_by_date(communications, date)
        exec_data = filter_by_date(executions, date)
        eval_data = filter_by_date(evaluations, date)
        viol_data = filter_by_date(violations, date)
        alert_data = filter_by_date(alerts, date)
        # 统计数据
        total_agents = len(set(
            [c.get('from') for c in comm_data] +
            [c.get('to') for c in comm_data]
        ))
        total_messages = len(comm_data)
        avg_score = 0
        if eval_data:
            scores = [e.get('overall_score', 0) for e in eval_data]
            avg_score = sum(scores) / len(scores) if scores else 0
        # Agent评分排行
        agent_scores = {}
        for e in eval_data:
            agent_id = e.get('agent_id')
            if agent_id:
                agent_scores[agent_id] = {
                    'score': e.get('overall_score', 0),
                    'rating': e.get('rating', '')
                }
        ranking_table = ""
        for rank, (agent_id, data) in enumerate(
            sorted(agent_scores.items(), key=lambda x: x[1]['score'], reverse=True)[:10], 1
        ):
            rating_display = {
                'excellent': '优秀',
                'good': '良好',
                'acceptable': '合格',
                'needs_improvement': '待改进',
                'unsatisfactory': '不合格'
            }.get(data['rating'], data['rating'])
            ranking_table += f"| {rank} | {agent_id} | {data['score']} | {rating_display} |\n"
        # 违规记录
        violations_section = ""
        if viol_data:
            for v in viol_data[:5]:  # 只显示前5条
                violations_section += f"""
### {v.get('violation_type', '未知类型')}
- **违规ID**: {v.get('violation_id', 'N/A')}
- **Agent**: {v.get('agent_id', 'N/A')}
- **严重程度**: {v.get('severity', 'N/A')}
- **描述**: {v.get('description', 'N/A')}
- **扣分**: {v.get('score_deduction', 0)}

"""
        else:
            violations_section = "本日无违规记录。"
        # 告警记录
        alerts_section = ""
        if alert_data:
            for a in alert_data[:5]:
                alerts_section += f"""
### {a.get('title', '未知告警')}
- **告警ID**: {a.get('alert_id', 'N/A')}
- **类型**: {a.get('alert_type', 'N/A')}
- **严重程度**: {a.get('severity', 'N/A')}
- **Agent**: {a.get('agent_id', 'N/A')}
- **邮件已发送**: {'是' if a.get('email_sent') else '否'}

"""
        else:
            alerts_section = "本日无告警记录。"
        # 生成报告
        report = self.DAILY_REPORT_TEMPLATE.format(
            date=date,
            total_agents=total_agents,
            total_messages=total_messages,
            avg_score=round(avg_score, 1),
            total_violations=len(viol_data),
            total_alerts=len(alert_data),
            ranking_table=ranking_table,
            violations_section=violations_section,
            alerts_section=alerts_section,
            watch_list="暂无待关注事项。",  # 简化
            generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        print(f"[Reporter] 日报生成完成: {len(report)} 字符")
        return report