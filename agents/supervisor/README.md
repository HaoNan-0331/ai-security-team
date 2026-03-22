# 监管员 (Supervisor)

AI安全运维团队的审计监察员，独立于所有业务Agent之外，通过被动读取Inbox文件单向监控所有Agent的通信和行为。

## 快速开始

### 启用监管员

监管员通过 Claude Code Teams 功能启用，**不需要程序启动**：

```bash
# 在 Claude Code CLI 中启用
claude team add-member ai-security-team supervisor

# 或者通过 team 配置文件添加
```

### 工作原理

启用后，监管员自动执行以下流程：

```
┌──────────────────────────────────────────────────────────────┐
│                      监管员监控流程                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. 扫描 Inbox 文件  ──→  ~/.claude/teams/{team}/inboxes/   │
│       (每2秒)                ├── orchestrator.json            │
│                              ├── log-analysis.json           │
│                              └── ...                         │
│                              ↓                               │
│  2. 解析消息内容  ──→  提取 from/to/text/timestamp           │
│                              ↓                               │
│  3. 数据脱敏处理  ──→  过滤敏感信息(IP/密码等)               │
│                              ↓                               │
│  4. 写入 JSONL 文件  ──→  supervisor/data/raw/               │
│                              ├── communications.jsonl        │
│                              ├── executions.jsonl            │
│                              └── violations.jsonl            │
│                              ↓                               │
│  5. 触发评估分析  ──→  四维度评分 + 违规检测                │
│                              ↓                               │
│  6. 生成告警(如需要)  ──→  邮件发送 + 告警记录              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## 核心模块

监管员的核心功能由以下 Python 模块实现（位于 `src/` 目录）：

| 模块 | 文件 | 功能描述 |
|------|------|----------|
| **监控引擎** | `monitor.py` | 扫描 Inbox 文件、解析消息、提取元数据 |
| **评估引擎** | `evaluator.py` | 四维度评分（执行30%、合规30%、协作20%、时效20%） |
| **违规检测** | `detector.py` | 三种违规检测（越权执行、违反协作规则、错误执行） |
| **告警模块** | `alerter.py` | 触发条件判断、邮件网关调用、告警记录 |
| **报告生成** | `reporter.py` | 从 JSONL 生成 Markdown 报告（日报/周报/月报） |
| **工具函数** | `utils.py` | JSONL 读写、日志配置、文件锁等通用工具 |

## 数据存储结构

所有监控数据使用 **JSON Lines 格式** 存储：

```
supervisor/
├── data/
│   └── raw/                       # 原始监控数据（JSON Lines）
│       ├── communications.jsonl  # 通信记录
│       ├── executions.jsonl      # 执行记录
│       ├── violations.jsonl      # 违规记录
│       ├── alerts.jsonl          # 告警记录
│       └── evaluations.jsonl     # 评估记录
├── reports/                       # 生成的报告
│   ├── daily/                     # 日报
│   ├── weekly/                    # 周报
│   └── monthly/                   # 月报
└── config/                        # 配置文件
    ├── scoring-rules.yaml         # 评分规则
    ├── violation-rules.yaml       # 违规检测规则
    └── alert-rules.yaml           # 告警规则
```

### JSON Lines 格式示例

```jsonl
# communications.jsonl
{"timestamp": "2026-02-19T14:30:00", "type": "communication", "message_id": "MSG-001", "from": "orchestrator", "to": "log-analysis", "message_type": "task_assign", "summary": "分配日志分析任务"}
{"timestamp": "2026-02-19T14:35:00", "type": "communication", "message_id": "MSG-002", "from": "log-analysis", "to": "orchestrator", "message_type": "status_report", "summary": "报告任务进度"}

# violations.jsonl
{"timestamp": "2026-02-19T15:00:00", "type": "violation", "violation_id": "VIO-001", "agent_id": "network-ops", "violation_type": "unauthorized_execution", "severity": "high", "description": "执行了超出能力范围的防火墙配置", "score_deduction": 40}
```

## 查看监控数据

### 命令行查看

```bash
# 查看通信记录
cat ~/.claude/teams/ai-security-team/agents/supervisor/data/raw/communications.jsonl

# 查看违规记录
cat ~/.claude/teams/ai-security-team/agents/supervisor/data/raw/violations.jsonl

# 查看最新报告
ls -la ~/.claude/teams/ai-security-team/agents/supervisor/reports/daily/
```

### Python 读取

```python
import json

def read_jsonl(filepath):
    """读取 JSON Lines 文件"""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

# 读取违规记录
violations = read_jsonl('data/raw/violations.jsonl')
for v in violations:
    print(f"{v['timestamp']}: {v['agent_id']} - {v['violation_type']}")
```

## 配置说明

### 评分规则 (scoring-rules.yaml)

```yaml
# 维度权重
weights:
  execution_capability: 0.30  # 执行能力 30%
  compliance: 0.30            # 合规性 30%
  collaboration: 0.20       # 协作能力 20%
  timeliness: 0.20            # 响应时效 20%

# 评级区间
rating_ranges:
  excellent: [90, 100]        # 优秀
  good: [80, 89]              # 良好
  acceptable: [70, 79]        # 合格
  needs_improvement: [60, 69] # 待改进
  unsatisfactory: [0, 59]      # 不合格
```

### 告警规则 (alert-rules.yaml)

```yaml
# 告警级别
alert_levels:
  critical:    # 严重 - 立即通知
    recipients: ["1466160825@qq.com"]

  warning:     # 警告 - 每小时汇总
    recipients: ["1466160825@qq.com"]

  info:        # 信息 - 每日摘要
    recipients: ["1466160825@qq.com"]

# 触发条件
triggers:
  consecutive_violations:  # 连续违规
    condition: "同一种违规24小时内≥3次"
    level: "critical"

  low_score_streak:        # 低分连续
    condition: "综合评分连续<60分达3次"
    level: "warning"

  serious_violation:       # 严重违规
    condition: "严重越权执行发生1次"
    level: "critical"
```

## 重要说明

1. **启用方式**：监管员通过 Claude Code Teams 功能启用，**不需要**程序启动或启动脚本
2. **单向监控**：监管员只读取 Inbox 文件，**绝不**向其他 Agent 发送消息
3. **隔离性**：其他 Agent 不知道监管员的存在，监管员保持完全独立
4. **永久存储**：所有数据永久保存在 `supervisor/data/` 目录，**不可删除**
5. **JSON Lines 格式**：所有监控数据使用 JSONL 格式，每行一条记录，便于追加和流式处理

---

## 更多信息

- **详细定义**: [supervisor.md](supervisor.md) - 完整的角色定义、工作流程、评分体系
- **代码实现**: `src/` 目录 - 核心模块的 Python 实现
- **配置说明**: `config/` 目录 - 评分规则、违规检测规则、告警规则

---

**版本**: v1.0 | **创建日期**: 2026-02-19 | **所属团队**: AI安全运维团队
