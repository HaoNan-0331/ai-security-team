"""
监管员评估引擎

功能：
- 四维度评分（执行能力、合规性、协作能力、响应时效）
- 评级计算（优秀/良好/合格/待改进/不合格）
- 趋势分析（评分变化趋势）
- 将评估记录写入JSON Lines文件

使用示例：
    from evaluator import Evaluator

    evaluator = Evaluator()

    # 评估单个Agent
    evaluation = evaluator.evaluate_agent(
        agent_id="log-analysis",
        execution_score=85,
        compliance_score=90,
        collaboration_score=80,
        timeliness_score=75
    )

    # 批量评估
    results = evaluator.evaluate_batch(evaluations_data)
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class EvaluationScores:
    """四维度评分"""
    execution_capability: int    # 执行能力 (0-100)
    compliance: int              # 合规性 (0-100)
    collaboration: int           # 协作能力 (0-100)
    timeliness: int              # 响应时效 (0-100)

    def calculate_overall(self, weights: Dict[str, float]) -> float:
        """计算综合得分"""
        overall = (
            self.execution_capability * weights['execution_capability'] +
            self.compliance * weights['compliance'] +
            self.collaboration * weights['collaboration'] +
            self.timeliness * weights['timeliness']
        )
        return round(overall, 1)


@dataclass
class EvaluationRecord:
    """评估记录"""
    timestamp: str
    agent_id: str
    period: str
    scores: EvaluationScores
    overall_score: float
    rating: str
    details: str
    evaluation_id: str = ""

    def __post_init__(self):
        if not self.evaluation_id:
            self.evaluation_id = f"EVAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        return {
            'timestamp': self.timestamp,
            'type': 'evaluation',
            'evaluation_id': self.evaluation_id,
            'agent_id': self.agent_id,
            'period': self.period,
            'scores': {
                'execution_capability': self.scores.execution_capability,
                'compliance': self.scores.compliance,
                'collaboration': self.scores.collaboration,
                'timeliness': self.scores.timeliness
            },
            'overall_score': self.overall_score,
            'rating': self.rating,
            'details': self.details
        }


class Evaluator:
    """
    评估引擎

    负责：
    - 四维度评分
    - 评级计算
    - 趋势分析
    - 写入JSON Lines文件

    Attributes:
        data_dir: 数据存储目录
        weights: 四维度权重
        rating_thresholds: 评级阈值
        evaluations_file: 评估记录文件路径
        trend_window: 趋势分析窗口（天）
    """

    # 默认权重配置
    DEFAULT_WEIGHTS = {
        'execution_capability': 0.30,  # 执行能力 30%
        'compliance': 0.30,            # 合规性 30%
        'collaboration': 0.20,       # 协作能力 20%
        'timeliness': 0.20           # 响应时效 20%
    }

    # 评级阈值
    RATING_THRESHOLDS = {
        'excellent': (90, 100, '优秀'),
        'good': (80, 89, '良好'),
        'acceptable': (70, 79, '合格'),
        'needs_improvement': (60, 69, '待改进'),
        'unsatisfactory': (0, 59, '不合格')
    }

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        weights: Optional[Dict[str, float]] = None,
        trend_window: int = 7
    ):
        """
        初始化评估引擎

        Args:
            data_dir: 数据存储目录（默认上级目录的data/raw）
            weights: 四维度权重（默认DEFAULT_WEIGHTS）
            trend_window: 趋势分析窗口天数（默认7天）
        """
        self.data_dir = data_dir or (Path(__file__).parent.parent / "data" / "raw")
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.trend_window = trend_window
        self.evaluations_file = self.data_dir / "evaluations.jsonl"

        # 确保目录存在
        self._init_directories()

        print(f"[Evaluator] 评估引擎初始化完成")
        print(f"[Evaluator] 数据目录: {self.data_dir}")
        print(f"[Evaluator] 权重配置: {self.weights}")

    def _init_directories(self):
        """初始化存储目录"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def calculate_rating(self, overall_score: float) -> Tuple[str, str]:
        """
        根据综合得分计算评级

        Args:
            overall_score: 综合得分（0-100）

        Returns:
            (评级代码, 评级名称)

        Raises:
            ValueError: 得分超出有效范围
        """
        if not 0 <= overall_score <= 100:
            raise ValueError(f"得分 {overall_score} 超出有效范围 [0, 100]")

        for rating_code, (min_score, max_score, rating_name) in self.RATING_THRESHOLDS.items():
            if min_score <= overall_score <= max_score:
                return rating_code, rating_name

        # 默认返回不合格（理论上不会执行到这里）
        return 'unsatisfactory', '不合格'

    def evaluate_scores(
        self,
        execution_capability: int,
        compliance: int,
        collaboration: int,
        timeliness: int
    ) -> Tuple[float, str, str, Dict[str, int]]:
        """
        评估四维度得分，计算综合得分和评级

        Args:
            execution_capability: 执行能力 (0-100)
            compliance: 合规性 (0-100)
            collaboration: 协作能力 (0-100)
            timeliness: 响应时效 (0-100)

        Returns:
            (综合得分, 评级代码, 评级名称, 各维度得分字典)

        Raises:
            ValueError: 任何维度得分超出有效范围
        """
        # 验证输入范围
        scores = {
            'execution_capability': execution_capability,
            'compliance': compliance,
            'collaboration': collaboration,
            'timeliness': timeliness
        }

        for name, score in scores.items():
            if not 0 <= score <= 100:
                raise ValueError(f"{name} 得分 {score} 超出有效范围 [0, 100]")

        # 创建评分对象
        scores_obj = EvaluationScores(
            execution_capability=execution_capability,
            compliance=compliance,
            collaboration=collaboration,
            timeliness=timeliness
        )

        # 计算综合得分
        overall_score = scores_obj.calculate_overall(self.weights)

        # 计算评级
        rating_code, rating_name = self.calculate_rating(overall_score)

        return overall_score, rating_code, rating_name, scores

    def evaluate_agent(
        self,
        agent_id: str,
        execution_score: int,
        compliance_score: int,
        collaboration_score: int,
        timeliness_score: int,
        period: Optional[str] = None,
        details: str = ""
    ) -> EvaluationRecord:
        """
        评估单个Agent，创建评估记录

        Args:
            agent_id: Agent标识符
            execution_score: 执行能力得分 (0-100)
            compliance_score: 合规性得分 (0-100)
            collaboration_score: 协作能力得分 (0-100)
            timeliness_score: 响应时效得分 (0-100)
            period: 评估周期（默认当前小时）
            details: 详细说明

        Returns:
            EvaluationRecord: 评估记录对象
        """
        # 计算评估
        overall_score, rating_code, rating_name, scores = self.evaluate_scores(
            execution_capability=execution_score,
            compliance=compliance_score,
            collaboration=collaboration_score,
            timeliness=timeliness_score
        )

        # 创建评分对象
        scores_obj = EvaluationScores(
            execution_capability=scores['execution_capability'],
            compliance=scores['compliance'],
            collaboration=scores['collaboration'],
            timeliness=scores['timeliness']
        )

        # 生成周期
        if period is None:
            now = datetime.now()
            period = f"{now.strftime('%Y-%m-%d %H')}:00-{(now.hour+1):02d}:00"

        # 创建评估记录
        record = EvaluationRecord(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            period=period,
            scores=scores_obj,
            overall_score=overall_score,
            rating=rating_code,
            details=details or f"综合得分 {overall_score}，评级 {rating_name}"
        )

        # 写入文件
        self._write_evaluation(record)

        print(f"[Evaluator] 评估完成: {agent_id} = {overall_score} ({rating_name})")

        return record

    def _write_evaluation(self, record: EvaluationRecord):
        """写入评估记录到JSON Lines文件"""
        with open(self.evaluations_file, 'a', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, ensure_ascii=False)
            f.write('
')

    def evaluate_batch(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> List[EvaluationRecord]:
        """
        批量评估多个Agent

        Args:
            evaluations: 评估数据列表，每个元素是一个字典，包含：
                - agent_id: Agent标识符
                - execution_score: 执行能力得分
                - compliance_score: 合规性得分
                - collaboration_score: 协作能力得分
                - timeliness_score: 响应时效得分
                - period: 评估周期（可选）
                - details: 详细说明（可选）

        Returns:
            List[EvaluationRecord]: 评估记录列表
        """
        records = []

        print(f"[Evaluator] 开始批量评估，共 {len(evaluations)} 个Agent...")

        for i, eval_data in enumerate(evaluations, 1):
            try:
                record = self.evaluate_agent(
                    agent_id=eval_data['agent_id'],
                    execution_score=eval_data['execution_score'],
                    compliance_score=eval_data['compliance_score'],
                    collaboration_score=eval_data['collaboration_score'],
                    timeliness_score=eval_data['timeliness_score'],
                    period=eval_data.get('period'),
                    details=eval_data.get('details', '')
                )
                records.append(record)
                print(f"[Evaluator] [{i}/{len(evaluations)}] {eval_data['agent_id']} 评估完成")

            except Exception as e:
                print(f"[Evaluator] [{i}/{len(evaluations)}] {eval_data.get('agent_id', 'unknown')} 评估失败: {e}")
                continue

        print(f"[Evaluator] 批量评估完成，成功 {len(records)}/{len(evaluations)} 个")
        return records

    def get_trend(
        self,
        agent_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取Agent的评分趋势

        Args:
            agent_id: Agent标识符
            days: 查询天数（默认7天）

        Returns:
            List[Dict]: 每日评分记录列表
        """
        if not self.evaluations_file.exists():
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        records = []

        with open(self.evaluations_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get('agent_id') != agent_id:
                        continue

                    record_time = datetime.fromisoformat(record.get('timestamp', ''))
                    if record_time < cutoff_date:
                        continue

                    records.append({
                        'timestamp': record['timestamp'],
                        'period': record.get('period', ''),
                        'overall_score': record.get('overall_score', 0),
                        'rating': record.get('rating', ''),
                        'scores': record.get('scores', {})
                    })

                except (json.JSONDecodeError, ValueError):
                    continue

        # 按时间排序
        records.sort(key=lambda x: x['timestamp'])
        return records

    def compare_agents(
        self,
        agent_ids: List[str],
        period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        对比多个Agent的评分

        Args:
            agent_ids: Agent标识符列表
            period: 评估周期（默认最新周期）

        Returns:
            Dict: 对比结果
        """
        comparison = {
            'agents': {},
            'ranking': [],
            'average_scores': {},
            'best_performers': {},
            'needs_improvement': []
        }

        for agent_id in agent_ids:
            trend = self.get_trend(agent_id, days=1)
            if not trend:
                continue

            latest = trend[-1]
            comparison['agents'][agent_id] = latest

        if not comparison['agents']:
            return comparison

        # 计算排名
        sorted_agents = sorted(
            comparison['agents'].items(),
            key=lambda x: x[1]['overall_score'],
            reverse=True
        )
        comparison['ranking'] = [
            {'rank': i+1, 'agent_id': aid, 'score': data['overall_score']}
            for i, (aid, data) in enumerate(sorted_agents)
        ]

        # 计算平均分
        for dimension in ['execution_capability', 'compliance', 'collaboration', 'timeliness']:
            scores = [
                agent['scores'].get(dimension, 0)
                for agent in comparison['agents'].values()
            ]
            comparison['average_scores'][dimension] = round(sum(scores) / len(scores), 1) if scores else 0

        # 最佳表现者
        for dimension in ['execution_capability', 'compliance', 'collaboration', 'timeliness']:
            best = max(
                comparison['agents'].items(),
                key=lambda x: x[1]['scores'].get(dimension, 0)
            )
            comparison['best_performers'][dimension] = {
                'agent_id': best[0],
                'score': best[1]['scores'].get(dimension, 0)
            }

        # 需要改进的Agent
        comparison['needs_improvement'] = [
            {
                'agent_id': aid,
                'score': data['overall_score'],
                'rating': data['rating']
            }
            for aid, data in sorted_agents
            if data['overall_score'] < 70
        ]

        return comparison


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("监管员评估引擎 - 使用示例")
    print("=" * 60)

    # 创建评估器
    evaluator = Evaluator()

    print("\n【示例1】单个Agent评估")
    print("-" * 60)

    evaluation = evaluator.evaluate_agent(
        agent_id="log-analysis",
        execution_score=85,
        compliance_score=90,
        collaboration_score=80,
        timeliness_score=75,
        details="日志分析任务执行良好，但响应时效有提升空间"
    )

    print(f"Agent: {evaluation.agent_id}")
    print(f"综合得分: {evaluation.overall_score}")
    print(f"评级: {evaluation.rating}")
    print(f"详情: {evaluation.details}")

    print("\n【示例2】批量评估")
    print("-" * 60)

    batch_data = [
        {
            'agent_id': 'pentest',
            'execution_score': 95,
            'compliance_score': 60,
            'collaboration_score': 90,
            'timeliness_score': 85
        },
        {
            'agent_id': 'threat-response',
            'execution_score': 88,
            'compliance_score': 92,
            'collaboration_score': 85,
            'timeliness_score': 90
        }
    ]

    results = evaluator.evaluate_batch(batch_data)

    for record in results:
        print(f"Agent: {record.agent_id}, 得分: {record.overall_score}, 评级: {record.rating}")

    print("\n【示例3】评分趋势查询")
    print("-" * 60)

    # 这里假设已经有一些历史评估数据
    trend = evaluator.get_trend("log-analysis", days=7)

    if trend:
        print(f"近7天评分趋势（{len(trend)}条记录）：")
        for record in trend:
            print(f"  {record['timestamp']}: {record['overall_score']} ({record['rating']})")
    else:
        print("暂无历史数据")

    print("\n【示例4】Agent对比")
    print("-" * 60)

    comparison = evaluator.compare_agents(
        agent_ids=['log-analysis', 'pentest', 'threat-response']
    )

    if comparison['ranking']:
        print("排名：")
        for rank_info in comparison['ranking']:
            print(f"  第{rank_info['rank']}名: {rank_info['agent_id']} ({rank_info['score']}分)")

    print("\n评估引擎示例运行完成！")
    print("=" * 60)
