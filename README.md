# AI Security Team

> AI安全运维团队 - 10个专业AI Agent实现7×24小时安全运维自动化

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com)
[![Claude](https://img.shields.io/badge/Claude_Code-Teams-green.svg)](https://claude.ai/claude-code)

---

## 项目概述

基于 **Claude Code Teams** 功能构建的全AI安全运维团队，通过10个专业AI Agent的协作，实现安全运维的全面自动化。

### 核心理念

- **🤖 全AI运营**：所有岗位由AI Agent承担
- **🔄 智能协作**：orchestrator协调器自动分配任务
- **🎯 专业分工**：每个Agent专注特定领域
- **🛡️ 人类在环**：关键决策保留人工确认机制
- **⚡ 实时响应**：秒级响应安全事件

---

## 目录结构

```
ai-security-team/
├── agents/                    # Agent定义
    ├── supervisor/            # 监管员（独立监控层）
    ├── orchestrator/          # AI协调器 (Team Lead)
    ├── monitoring/            # 监控分析组 (3个Agent)
    ├── defense/               # 防御响应组 (3个Agent)
    ├── assessment/            # 评估优化组 (2个Agent)
    ├── operations/            # 运维管理组 (2个Agent)
    └── .template/             # Agent定义模板
│
└── README.md                  # 本文件
```

---

## Agent列表

### 👑 Team Lead

| Agent | 职责 | 文档 |
|-------|------|------|
| **orchestrator** | 任务调度、Agent协调、结果汇总、应急响应协调 | `agents/orchestrator/orchestrator.md` |

### 🔍 监控分析组 (3个)

| Agent | 职责 | 可用技能 | 文档 |
|-------|------|----------|------|
| **log-analyst** | 日志采集、解析、异常检测 | 无 | `agents/monitoring/log-analysis/` |
| **alert-triage** | 告警分类、优先级排序、误报过滤、威胁情报查询 | ip-reputation | `agents/monitoring/alert-judgment/` |
| **asset-manager** | 资产扫描、台账维护、状态监控 | network-device-automation<br>network-device-cli | `agents/monitoring/asset-mgmt/` |

### 🛡️ 防御响应组 (3个)

| Agent | 职责 | 可用技能 | 文档 |
|-------|------|----------|------|
| **threat-handler** | 威胁快速响应、情报收集、攻击遏制 | asg-firewall-api<br>nsf-firewall-api<br>network-device-cli<br>kali-pentest | `agents/defense/threat-response/` |
| **forensic-analyst** | 数字取证、证据保全、溯源分析 | 无 | `agents/defense/forensic/` |
| **policy-enforcer** | 安全策略配置、变更 | asg-firewall-api<br>nsf-firewall-api<br>network-device-automation | `agents/defense/policy-exec/` |

### 📊 评估优化组 (2个)

| Agent | 职责 | 可用技能 | 文档 |
|-------|------|----------|------|
| **vuln-assessment** | 漏洞扫描、验证、渗透测试 | kali-pentest | `agents/assessment/vuln-assessment/` |
| **risk-compliance** | 风险评估、合规检查、差距分析 | pptx | `agents/assessment/risk-compliance/` |

### ⚙️ 运维管理组 (2个)

| Agent | 职责 | 可用技能 | 文档 |
|-------|------|----------|------|
| **network-ops** | 网络设备配置、路由管理、故障排查 | network-device-cli<br>asg-firewall-api<br>nsf-firewall-api | `agents/operations/network-ops/` |
| **server-ops** | 服务器/终端管理、补丁管理、服务部署 | distributed-executor-api | `agents/operations/server-ops/` |

---

## 使用方式

### 与orchestrator对话

在Claude Code中，直接与**orchestrator**交流：

```
用户: orchestrator，发现Web服务器遭受SQL注入攻击，请处理！

orchestrator: 收到！正在启动安全事件响应流程...
├── 分配任务给 log-analyst：分析日志
├── 分配任务给 alert-triage：评估等级
├── 分配任务给 threat-handler：执行阻断
└── 协调响应流程

[各Agent执行任务...]

orchestrator: ✅ 事件已处理完毕！
```

### 查看Agent文档

每个Agent的文档包含：
- 职责定位和核心职责
- 与其他Agent的边界划分
- 输入输出关系
- 可用技能列表
- 决策权限
- 协作关系

```bash
# 查看orchestrator文档
cat agents/orchestrator/orchestrator.md

# 查看具体Agent文档
cat agents/monitoring/log-analysis/log-analysis.md
cat agents/defense/threat-response/threat-response.md
```

---

## 工作流程示例

### 安全事件响应

```
用户报告 → orchestrator
    ↓
log-analyst 分析日志
    ↓
alert-triage 评估等级
    ↓
orchestrator 事件定级（PDCERF流程）
    ↓
threat-handler 执行阻断
    ↓
forensic-analyst 收集证据
    ↓
orchestrator 汇总结果
```

### 漏洞管理

```
漏洞发现 → orchestrator
    ↓
vuln-assessment 扫描漏洞
    ↓
risk-compliance 评估风险
    ↓
server-ops 部署补丁
    ↓
orchestrator 汇总结果
```

---

## 决策权限

| 风险等级 | 决策权限 | 示例 |
|----------|----------|------|
| 低 | AI自主 | 阻断已知恶意IP、封禁账户 |
| 中 | AI+通知 | 执行处置并同步通知人类 |
| 高 | 人工确认 | 关闭关键业务系统、修改核心配置 |

---

## 职责边界明确

根据团队职责划分决策，各Agent的职责边界如下：

### 1. 安全设备配置边界

| Agent | 负责设备 | 不涉及 |
|--------|-----------|--------|
| **policy-exec** | 防火墙、IPS、WAF等安全设备 | 交换机、路由器等基础网络设备 |
| **network-ops** | 交换机、路由器等基础网络设备 | 防火墙、IPS、WAF等安全设备 |

**划分方式**: 按设备类型划分

---

### 2. 风险评估分工

| Agent | 职责 | 输出 |
|--------|------|------|
| **vuln-assessment** | 漏洞扫描、验证、渗透测试、技术评估、修复建议 | 漏洞清单、技术漏洞信息 |
| **risk-compliance** | 综合风险评估、风险量化、合规检查、整改建议 | 风险矩阵、风险等级、合规报告 |

**数据流向**: vuln-assessment → risk-compliance（作为风险评估中心）

---

### 3. 日志分析边界

| 维度 | log-analysis | forensic |
|------|-------------|----------|
| 工作模式 | 主动式，7×24持续监控 | 被动式，事件触发后启动 |
| 目标 | 实时发现异常 | 事件发生后收集证据 |
| 输出 | 原始异常事件 | 完整取证报告 |

---

### 4. 告警处理流程

| Agent | 职责 |
|--------|------|
| **log-analysis** | 只负责**发现异常**并上报**原始异常事件**（不分类、不排优先级） |
| **alert-judgment** | 负责告警**分类、排序、过滤误报** |

**数据流向**: log-analysis → alert-judgment（原始异常 → 分类告警）

---

### 5. 威胁情报归属

| Agent | 负责 | 能力来源 |
|--------|------|----------|
| **alert-judgment** | 威胁情报查询（IP信誉、IOC匹配） | ip-reputation skill |

**变更说明**: v2.1版本将原threat-intel Agent的威胁情报查询能力整合为ip-reputation skill，由alert-judgment Agent调用

---

### 6. 资产更新权限

| Agent | 权限 | 责任 |
|--------|------|------|
| **asset-mgmt** | **统一负责**资产库更新、台账维护 | 资产数据权威 |
| **运维agents**<br>(network-ops/server-ops) | 执行变更操作、变更后通知asset-mgmt | 不直接修改数据库 |

**变更流程**:
```
运维agent执行变更 → 通知asset-mgmt → asset-mgmt更新数据库
```

---

### 7. 响应职责

| Agent | 角色 | 工作重点 |
|--------|------|----------|
| **orchestrator** | 应急响应的**指挥官** | 响应流程协调、事件定级、资源调度、进度跟踪 |
| **threat-handler** | 安全事件的**快速响应员** | 威胁遏制、威胁清除、系统修复、恢复验证、情报收集 |

**协作方式**: orchestrator指挥协调，threat-handler执行处置

---

## 可用技能

Agent直接调用的技能：
- `network-device-automation` - 网络设备运维自动化（华为/H3C/思科/锐捷）
- `network-device-cli` - 网络设备命令行交互
- `asg-firewall-api` - 上元信安ASG防火墙REST API
- `nsf-firewall-api` - 绿盟NF防火墙REST API
- `kali-pentest` - Kali Linux渗透测试自动化
- `pptx` - PowerPoint演示文稿生成
- `distributed-executor-api` - 分布式命令执行系统

---

## 资产数据库


所有Agent通过SDK访问资产数据库：

```bash

# SDK方式
from asset_sdk import AssetClient
client = AssetClient()
assets = client.list_assets(asset_type="Server")
```

**各Agent常用命令**：

| Agent | 常用操作 |
|-------|----------|
| server-ops | `get --include-password` - 获取设备登录信息<br>`list --type Server` - 获取服务器列表<br>`list --type Endpoint` - 获取终端列表 |
| network-ops | `list --type NetworkDevice` - 获取网络设备列表 |
| threat-response | `search`, `update --status compromised` - 搜索/标记受影响资产 |
| asset-manager | `batch create`, `export` - 导入导出资产 |
| forensic | `history` - 查看变更历史 |

**详细文档**：
- [资产库README](asset-database/README.md)
- [Agent使用指南](docs/asset-database-AGENT-GUIDE.md)

---

## 添加新Agent

1. 复制模板：`cp agents/.template/AGENT_TEMPLATE.md agents/<group>/<agent-name>/AGENT.md`
2. 填写Agent定义（职责、边界、协作关系）
3. 创建prompt.md提示词文件
4. 更新本README

---

**项目版本**: v2.1
**创建日期**: 2026年2月8日
**更新日期**: 2026年3月19日
**维护者**: AI Security Team
