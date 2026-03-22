---
name: ip-reputation
description: 查询IP地址的信誉情报，通过多个威胁情报源进行综合分析和风险评分。当用户要求检查IP信誉、查询IP威胁情报、验证IP安全性、调查可疑IP地址、分析IP风险、查询IP恶意历史时使用此skill。支持批量IP查询、生成威胁情报报告、SOC安全分析、事件响应等场景。
---

# IP信誉情报查询Skill

这个skill用于查询IP地址的信誉情报，通过多个威胁情报源进行综合分析，并根据配置的权重计算风险评分。

## 何时使用

当用户提到以下需求时使用此skill：
- "检查IP信誉"、"查询IP情报"、"验证IP是否恶意"
- "这个IP安全吗？"、"IP地址风险评估"
- "查询IP的威胁情报"、"IP恶意历史查询"
- "批量检查IP地址"、"IP威胁分析报告"
- "安全事件响应中的IP调查"、"SOC IP分析"

## 工作流程

### 1. 获取IP地址并验证

首先确认用户提供的一个或多个IP地址，验证IP格式：

```python
# 有效的IPv4/IPv6地址
import ipaddress

def validate_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False
```

### 2. 加载情报源配置

读取 `assets/config/sources.yaml` 获取配置的情报源及其权重：

```yaml
# sources.yaml 结构示例
sources:
  virustotal:
    name: "VirusTotal"
    url_template: "https://www.virustotal.com/gui/ip-address/{ip}"
    weight: 0.30
    reliability: 0.95
    requires_api: false
    query_method: "browser"

  abuseipdb:
    name: "AbuseIPDB"
    url_template: "https://www.abuseipdb.com/check/{ip}"
    weight: 0.25
    reliability: 0.90
    requires_api: false
    query_method: "browser"
```

### 3. 使用Browser查询每个情报源

对每个启用的情报源，使用browser工具查询IP情报：

**重要提示：**
- 禁止使用 WebSearch 或 WebReader MCP 工具
- 必须使用 agent-browser CLI 进行所有网页查询
- 使用 Bash 工具执行 agent-browser 命令
- 默认携带 --ignore-https-errors 参数忽略 HTTPS 证书错误
- 从网页中提取结构化的威胁情报数据
- WebSearch 已被禁用 - 请勿使用

**查询命令模板：**
```bash
agent-browser --ignore-https-errors open "https://www.virustotal.com/gui/ip-address/{ip}"
agent-browser wait --load networkidle
agent-browser snapshot -i
```

**查询步骤：**
1. 构建情报源的URL（使用url_template）
2. 调用browser获取页面内容
3. 解析页面提取以下信息：
   - 恶意分数/检测率
   - 最后扫描时间
   - 报告该IP恶意的历史记录
   - 关联的恶意软件/威胁类型
   - 地理位置（如可用）

### 4. 计算综合风险评分

使用 `scripts/scorer.py` 计算综合评分：

```
综合风险评分 = Σ(单个来源评分 × 来源权重 × 来源可信度)
```

评分等级：
- **0-20**: 低风险（可信IP）
- **21-40**: 较低风险
- **41-60**: 中等风险（需关注）
- **61-80**: 高风险（可疑）
- **81-100**: 严重风险（恶意）

### 5. 生成综合报告

按以下格式生成报告：

```markdown
# IP信誉情报报告

## 概要
- **IP地址**: {ip}
- **综合风险评分**: {score}/100
- **风险等级**: {level}
- **查询时间**: {timestamp}
- **情报源数量**: {count}

## 风险评分详情

| 情报源 | 评分 | 权重 | 可信度 | 加权得分 |
|--------|------|------|--------|----------|
| VirusTotal | 85/100 | 0.30 | 0.95 | 24.23 |
| AbuseIPDB | 70/100 | 0.25 | 0.90 | 15.75 |
| ... | ... | ... | ... | ... |
| **总计** | - | - | - | **{total_score}** |

## 情报源详细结果

### VirusTotal
- **检测结果**: {positive_detections}/{total_detections}
- **恶意分数**: {malicious_score}
- **最后扫描**: {last_scan}
- **关联威胁**: {threat_types}

### AbuseIPDB
- **滥用报告数**: {report_count}
- **置信度**: {confidence}
- **最后报告**: {last_report}
- **滥用类型**: {categories}

## 威胁类型汇总
{summary_of_threat_categories}

## 地理位置信息
- **国家**: {country}
- **地区**: {region}
- **ISP**: {isp}
- **ASN**: {asn}

## 建议
{actionable_recommendations}

## 原始数据
{link_to_raw_data_or_appendix}
```

## 配置文件

### sources.yaml

定义启用的情报源及其权重：

```yaml
sources:
  virustotal:
    enabled: true
    name: "VirusTotal"
    url_template: "https://www.virustotal.com/gui/ip-address/{ip}"
    weight: 0.30
    reliability: 0.95
    requires_api: false
    query_method: "browser"

  abuseipdb:
    enabled: true
    name: "AbuseIPDB"
    url_template: "https://www.abuseipdb.com/check/{ip}"
    weight: 0.25
    reliability: 0.90
    requires_api: false
    query_method: "browser"

  alienvault:
    enabled: true
    name: "AlienVault OTX"
    url_template: "https://otx.alienvault.com/indicator/ip/{ip}"
    weight: 0.20
    reliability: 0.85
    requires_api: false
    query_method: "browser"

  shodan:
    enabled: true
    name: "Shodan"
    url_template: "https://www.shodan.io/host/{ip}"
    weight: 0.15
    reliability: 0.80
    requires_api: false
    query_method: "browser"

  urlhaus:
    enabled: true
    name: "URLhaus"
    url_template: "https://urlhaus.abuse.ch/browse.php?search={ip}"
    weight: 0.10
    reliability: 0.75
    requires_api: false
    query_method: "browser"
```

**权重配置说明：**
- 权重总和应该等于 1.0
- 根据情报源的可靠性和重要性分配权重
- 可靠性 (reliability) 范围 0-1，表示该情报源的历史准确度

### scoring.yaml

定义评分规则：

```yaml
scoring:
  # 基础分数计算规则
  rules:
    detection_rate:
      # 检测率转换为分数的公式
      formula: "detection_rate * 100"

    report_count:
      # 报告数量转换为分数
      low:
        max_reports: 5
        score: 20
      medium:
        max_reports: 20
        score: 50
      high:
        max_reports: 100
        score: 80
      critical:
        score: 100

  # 风险等级阈值
  thresholds:
    low: 20
    medium: 40
    high: 60
    critical: 80

  # 威胁类型权重
  threat_weights:
    malware: 1.0
    phishing: 0.9
    botnet: 1.0
    c2_server: 1.0
    spam: 0.5
    scan: 0.3
    dos_attack: 0.8
```

## 错误处理

- 如果某个情报源查询失败，记录错误但继续处理其他来源
- 最终评分基于成功查询的来源，按比例调整权重
- 如果所有来源都失败，返回错误信息和建议

## 批量查询

对于多个IP地址：
1. 对每个IP执行独立查询
2. 生成汇总报告，包含所有IP的评分
3. 可选择生成CSV格式的批量结果

```markdown
# 批量IP信誉报告

查询时间: {timestamp}
IP数量: {count}

## 汇总统计
- 高风险IP: {critical_count}
- 中风险IP: {high_count}
- 低风险IP: {low_count}
- 平均风险分: {average_score}

## 详细结果
{table_of_all_ips_with_scores}
```

## 注意事项

- 某些情报源可能有访问限制或需要登录
- 网页结构变化可能导致解析失败，需要定期维护
- 建议将查询结果缓存，避免重复查询
- 尊重各情报源的使用条款和速率限制

## 示例对话

**用户**: 检查IP 8.8.8.8 的信誉

**输出**:
使用此skill，查询多个情报源，计算综合评分，生成完整的信誉报告。

**用户**: 批量检查这些IP是否恶意: 192.168.1.1, 10.0.0.1, 8.8.8.8

**输出**:
对每个IP进行查询，生成汇总报告和CSV结果文件。
