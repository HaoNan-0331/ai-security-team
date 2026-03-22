#!/usr/bin/env python3
"""
IP信誉评分计算脚本
根据多个情报源的数据计算综合风险评分
"""

import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SourceResult:
    """单个情报源的查询结果"""
    source_name: str
    score: float  # 该来源给出的原始评分 (0-100)
    weight: float  # 该来源的配置权重
    reliability: float  # 该来源的可信度 (0-1)
    details: Dict  # 详细信息
    timestamp: Optional[datetime] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class ThreatInfo:
    """威胁信息"""
    threat_type: str
    weight: float
    description: str
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class IPReputationScorer:
    """IP信誉评分计算器"""

    def __init__(self, sources_config: Dict, scoring_config: Dict):
        """
        初始化评分器

        Args:
            sources_config: 情报源配置
            scoring_config: 评分规则配置
        """
        self.sources_config = sources_config
        # 处理嵌套的scoring配置
        if 'scoring' in scoring_config:
            self.scoring_config = scoring_config['scoring']
        else:
            self.scoring_config = scoring_config

    def calculate_detection_score(self, positive: int, total: int) -> float:
        """
        计算检测率评分

        Args:
            positive: 检出恶意的引擎数量
            total: 总引擎数量

        Returns:
            评分 (0-100)
        """
        if total == 0:
            return 0.0
        detection_rate = positive / total
        return detection_rate * 100

    def calculate_report_score(self, report_count: int, use_log: bool = True) -> float:
        """
        计算报告数量评分

        Args:
            report_count: 报告数量
            use_log: 是否使用对数缩放

        Returns:
            评分 (0-100)
        """
        if use_log:
            # 对数缩放: min(100, log2(count + 1) * 15)
            return min(100.0, math.log2(report_count + 1) * 15)
        else:
            # 线性缩放
            return min(100.0, report_count * 2)

    def calculate_threat_weight(self, threat_types: List[str]) -> float:
        """
        根据威胁类型计算权重因子

        Args:
            threat_types: 威胁类型列表

        Returns:
            权重因子 (0-1)
        """
        threat_weights = self.scoring_config.get('threat_weights', {})

        if not threat_types:
            return 0.5  # 默认中等权重

        max_weight = 0.0
        for threat in threat_types:
            weight = threat_weights.get(threat.lower(), 0.5)
            max_weight = max(max_weight, weight)

        return max_weight

    def calculate_freshness_factor(self, last_seen: Optional[datetime]) -> float:
        """
        计算数据新鲜度因子

        Args:
            last_seen: 最后检测时间

        Returns:
            新鲜度因子 (0-1)
        """
        if last_seen is None:
            return 0.3  # 无时间信息，给予较低权重

        now = datetime.now()
        age = now - last_seen

        if age <= timedelta(days=1):
            return 1.0
        elif age <= timedelta(weeks=1):
            return 0.9
        elif age <= timedelta(days=30):
            return 0.7
        elif age <= timedelta(days=90):
            return 0.5
        else:
            return 0.3

    def normalize_weights(self, source_results: List[SourceResult]) -> List[SourceResult]:
        """
        归一化权重（当某些来源失败时）

        Args:
            source_results: 情报源结果列表

        Returns:
            归一化后的结果列表
        """
        # 筛选成功的来源
        successful = [r for r in source_results if r.success]

        if not successful:
            return source_results

        # 计算原始权重总和
        total_weight = sum(r.weight for r in successful)

        # 归一化权重
        for result in source_results:
            if result.success:
                result.weight = result.weight / total_weight

        return source_results

    def calculate_overall_score(self, source_results: List[SourceResult]) -> float:
        """
        计算综合风险评分

        Args:
            source_results: 所有情报源的结果

        Returns:
            综合评分 (0-100)
        """
        # 归一化权重
        normalized_results = self.normalize_weights(source_results)

        # 计算加权平均
        weighted_sum = 0.0
        for result in normalized_results:
            if result.success:
                # 综合评分 = 来源评分 × 权重 × 可信度
                contribution = result.score * result.weight * result.reliability
                weighted_sum += contribution

        return min(100.0, max(0.0, weighted_sum))

    def get_risk_level(self, score: float) -> Dict:
        """
        根据评分获取风险等级

        Args:
            score: 综合评分

        Returns:
            包含等级信息的字典
        """
        thresholds = self.scoring_config.get('thresholds', {})
        levels = self.scoring_config.get('levels', {})

        if score <= thresholds.get('low', 20):
            level_key = 'very_low'
        elif score <= thresholds.get('medium', 40):
            level_key = 'low'
        elif score <= thresholds.get('high', 60):
            level_key = 'medium'
        elif score <= thresholds.get('critical', 80):
            level_key = 'high'
        else:
            level_key = 'critical'

        level_info = levels.get(level_key, {
            'name': '未知',
            'description': '无法确定风险等级',
            'color': 'gray',
            'action': '请进一步调查'
        })

        return {
            'key': level_key,
            'name': level_info['name'],
            'description': level_info['description'],
            'color': level_info.get('color', 'gray'),
            'action': level_info.get('action', '请进一步调查'),
            'score': score
        }


def parse_virustotal_response(data: Dict) -> Dict:
    """
    解析VirusTotal响应数据

    Args:
        data: 从VT获取的数据

    Returns:
        标准化结果
    """
    # 这里需要根据实际的VT响应格式调整
    return {
        'detection_ratio': f"{data.get('positive', 0)}/{data.get('total', 0)}",
        'positive': data.get('positive', 0),
        'total': data.get('total', 0),
        'last_scan': data.get('last_scan'),
        'threat_types': data.get('threat_types', [])
    }


def parse_abuseipdb_response(data: Dict) -> Dict:
    """
    解析AbuseIPDB响应数据

    Args:
        data: 从AbuseIPDB获取的数据

    Returns:
        标准化结果
    """
    return {
        'report_count': data.get('reports', 0),
        'confidence': data.get('confidence_score', 0),
        'last_report': data.get('last_reported'),
        'categories': data.get('categories', [])
    }


# 示例用法
if __name__ == "__main__":
    # 示例配置
    sources_config = {
        'virustotal': {'weight': 0.30, 'reliability': 0.95},
        'abuseipdb': {'weight': 0.25, 'reliability': 0.90}
    }

    scoring_config = {
        'thresholds': {'low': 20, 'medium': 40, 'high': 60, 'critical': 80},
        'levels': {
            'very_low': {'name': '低风险', 'color': 'green'},
            'low': {'name': '较低风险', 'color': 'blue'},
            'medium': {'name': '中等风险', 'color': 'yellow'},
            'high': {'name': '高风险', 'color': 'orange'},
            'critical': {'name': '严重风险', 'color': 'red'}
        },
        'threat_weights': {
            'malware': 1.0,
            'botnet': 1.0,
            'spam': 0.4
        }
    }

    scorer = IPReputationScorer(sources_config, scoring_config)

    # 示例：计算检测率评分
    score = scorer.calculate_detection_score(positive=15, total=70)
    print(f"检测率评分: {score:.2f}")

    # 示例：计算报告数量评分
    report_score = scorer.calculate_report_score(report_count=25)
    print(f"报告数量评分: {report_score:.2f}")

    # 示例：获取风险等级
    risk_level = scorer.get_risk_level(score=75)
    print(f"风险等级: {risk_level['name']} - {risk_level['description']}")
