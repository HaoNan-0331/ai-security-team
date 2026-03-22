# IP信誉情报源参考

本文档详细说明各个IP信誉情报源的数据格式和解析方法。

## VirusTotal (VT)

**URL**: `https://www.virustotal.com/gui/ip-address/{ip}`

### 数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| data.attributes.last_analysis_stats | object | 最新扫描统计 |
| data.attributes.last_analysis_stats.malicious | int | 检出恶意的引擎数 |
| data.attributes.last_analysis_stats.harmless | int | 未检出恶意的引擎数 |
| data.attributes.last_analysis_stats.suspicious | int | 检出可疑的引擎数 |
| data.attributes.last_analysis_results | object | 各引擎详细结果 |
| data.attributes.country | string | 国家代码 |
| data.attributes.continent | string | 大洲代码 |
| data.attributes.network | string | 网络段 |

### 评分逻辑

```python
detection_rate = malicious / (malicious + harmless + suspicious + timeout)
score = detection_rate * 100
```

### 解析提示

- 网页版本需要JavaScript渲染，使用browser获取
- API版本需要API key（免费版有速率限制）
- 数据更新频率：每小时

## AbuseIPDB

**URL**: `https://www.abuseipdb.com/check/{ip}`

### 数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| data.abuseConfidenceScore | int | 滥用置信度 (0-100) |
| data.totalReports | int | 总报告数 |
| data.numDistinctUsers | int | 报告用户数 |
| data.lastReportedAt | string | 最后报告时间 |
| data.isPublic | boolean | 是否为公网IP |
| data.ipVersion | int | IP版本 (4/6) |
| data.isWhitelisted | boolean | 是否在白名单中 |

### 评分逻辑

```python
# 基于报告数量和置信度
base_score = min(100, log2(total_reports + 1) * 15)
confidence_factor = abuse_confidence_score / 100
score = base_score * (0.5 + 0.5 * confidence_factor)
```

### 滥用类别

- 3 - Fraud Order
- 4 - DDoS Attack
- 5 - FTP Brute-Force
- 6 - Ping of Death
- 7 - Phishing
- 8 - Fraud VoIP
- 9 - Open Proxy
- 10 - Web Spam
- 11 - Email Spam
- 12 - Blog Spam
- 13 - VPN IP
- 14 - Port Scan
- 15 - Hacking
- 16 - SQL Injection
- 17 - Spoofing
- 18 - Brute Force
- 19 - Bad Web Bot
- 20 - Exploited Host
- 21 - Web App Attack
- 22 - SSH
- 23 - IoT Targeted

## AlienVault OTX

**URL**: `https://otx.alienvault.com/indicator/ip/{ip}`

### 数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| reputation | int | 声誉值 (0-5) |
| pulse_info.count | int | 脉冲数量 |
| pulse_info.pulses | array | 脉冲详情 |
| whois | string | WHOIS信息 |
| geo | object | 地理位置信息 |

### 评分逻辑

```python
# 基于声誉值和脉冲数量
if reputation == 0:
    reputation_score = 100
elif reputation == 1:
    reputation_score = 80
elif reputation == 2:
    reputation_score = 60
elif reputation == 3:
    reputation_score = 40
elif reputation == 4:
    reputation_score = 20
else:
    reputation_score = 0

pulse_bonus = min(20, pulse_count * 2)
score = reputation_score + pulse_bonus
```

## Shodan

**URL**: `https://www.shodan.io/host/{ip}`

### 数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| ports | array | 开放端口列表 |
| vulns | array | CVE漏洞列表 |
| tags | array | 标签 |
| hostnames | array | 主机名 |
| country_name | string | 国家名称 |
| city | string | 城市 |
| isp | string | ISP |
| asn | string | ASN编号 |
| org | string | 组织 |
| info | string | 一般信息 |

### 评分逻辑

```python
# 基于开放端口数量和漏洞
port_score = min(50, len(ports) * 5)
vuln_score = min(50, len(vulns) * 10)
score = port_score + vuln_score
```

## URLhaus

**URL**: `https://urlhaus.abuse.ch/browse.php?search={ip}`

### 数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| malware_count | int | 恶意软件样本数量 |
| tags | array | 标签 |
| firstseen | string | 首次发现时间 |
| lastseen | string | 最后发现时间 |
| urlhaus_reference | string | URLhaus参考链接 |

### 评分逻辑

```python
# 基于恶意软件样本数量
score = min(100, malware_count * 10)
```

### 标签

- botnet
- ddos
- downloader
- loader
- ransomware
- trojan
- backdoor
- banking_malware
- dropper
- exploit_kit
- phishing

## 解析注意事项

1. **网页结构变化**: 网页结构可能随时变化，需要定期维护解析逻辑
2. **速率限制**: 大部分服务有速率限制，批量查询时需要控制频率
3. **认证要求**: 某些服务可能需要登录或API密钥才能查看完整信息
4. **数据延迟**: 不同服务的更新频率不同，注意数据时效性
5. **误报率**: 每个来源都有误报率，通过多源交叉验证可以提高准确性

## 测试IP

以下IP可用于测试各个情报源的响应：

- `8.8.8.8` - Google DNS（可信IP，应得低分）
- `1.1.1.1` - Cloudflare DNS（可信IP）
- `192.168.1.1` - 内网IP（通常不应出现在公网情报源）
- `185.220.101.1` - Tor节点（中等风险）
- `45.142.212.14` - 已知恶意IP（应得高分）

## 数据标准化

所有来源的数据应标准化为以下格式：

```python
{
    "source": "source_name",
    "ip": "query_ip",
    "score": 0-100,
    "confidence": 0-1,
    "timestamp": "ISO 8601",
    "details": {
        "detections": {},
        "threat_types": [],
        "geo": {},
        "first_seen": "ISO 8601",
        "last_seen": "ISO 8601"
    }
}
```
