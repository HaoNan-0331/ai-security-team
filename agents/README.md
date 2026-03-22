# AI安全运维团队 Agent列表

## 团队结构（11个Agent）

### 中央调度
- **orchestrator** - AI协调器（含应急响应协调）

### 监控分析组
- **log-analysis** - 日志分析
- **alert-judgment** - 告警研判（含威胁情报查询）
- **asset-mgmt** - 资产管理

### 防御响应组
- **threat-response** - 威胁处置
- **forensic** - 取证分析
- **policy-exec** - 策略执行

### 评估优化组
- **vuln-assessment** - 漏洞评估（含渗透测试）
- **risk-compliance** - 风险与合规

### 运维管理组
- **network-ops** - 网络运维
- **server-ops** - 系统运维（含补丁管理）

---

## 目录结构

```
agents/
├── orchestrator/              # AI协调器(Team Lead)
│   └── prompt.md
│
├── supervisor/                # 监管员（独立监控层）
│   └── supervisor.md
│
├── monitoring/                # 监控分析组 (3)
│   ├── log-analysis/          # 日志分析Agent
│   ├── alert-judgment/        # 告警研判Agent（含威胁情报查询）
│   └── asset-mgmt/            # 资产管理Agent
│
├── defense/                   # 防御响应组 (3)
│   ├── threat-response/       # 威胁处置Agent
│   ├── forensic/              # 取证分析Agent
│   └── policy-exec/           # 策略执行Agent
│
├── assessment/                # 评估优化组 (2)
│   ├── vuln-assessment/       # 漏洞评估Agent（含渗透测试）
│   └── risk-compliance/       # 风险与合规Agent
│
└── operations/                # 运维管理组 (2)
    ├── network-ops/           # 网络运维Agent
    └── server-ops/            # 系统运维Agent（含补丁管理）
```

---

## Agent总览

### 1. AI协调器 (Orchestrator)

**目录**: `orchestrator/`
**角色**: 团队大脑，负责整体协调、调度和应急响应

| 属性 | 说明 |
|------|------|
| 定位 | AI团队的大脑 |
| 核心职责 | 任务调度、代理协调、结果汇总、质量控制、应急响应协调 |
| 决策权限 | 分配任务、代理调用、常规异常处理 |
| 人类介入 | 重大策略变更、高风险操作 |

---

### 2. 监管员 (Supervisor) - 独立监控层

**目录**: `supervisor/`
**角色**: 独立审计监察员，单向监控所有Agent

| 属性 | 说明 |
|------|------|
| 定位 | 独立的审计监察员，不与其他Agent通信 |
| 核心职责 | 监控所有Agent通信和行为、评分评估、违规检测、主动告警 |
| 监控方式 | 被动读取 `~/.claude/teams/{team}/inboxes/` 下的所有Inbox文件 |
| 告警方式 | 发送邮件到 1466160825@qq.com，**不经过任何Agent** |
| 隔离性 | 完全隔离，其他Agent不知道监管员存在 |
| 决策权限 | 只监控和告警，不干预Agent行为 |
| 人类介入 | 接收告警邮件，审批规则修改建议 |

---

### 3. 监控分析组 (Monitoring Group)

#### 3.1 日志分析Agent
**目录**: `monitoring/log-analysis/`
**专业领域**: 日志数据采集、解析、分析、异常检测

| 属性 | 说明 |
|------|------|
| 核心职责 | 日志采集、解析、异常检测、行为分析、趋势分析 |
| 使用Skills | distributed-executor-api |
| 输入 | 原始日志数据、分析参数 |
| 输出 | 异常事件、行为分析报告、威胁情报建议 |
| 协作 | 上报告警研判Agent、接收资产发现Agent数据 |

#### 3.2 告警研判Agent
**目录**: `monitoring/alert-judgment/`
**专业领域**: 安全告警分类、优先级排序、误报过滤、事件关联、威胁情报查询

| 属性 | 说明 |
|------|------|
| 核心职责 | 告警接收、分类、优先级排序、误报过滤、事件关联、威胁情报查询 |
| 使用Skills | asset-database-sdk, ip-reputation |
| 输入 | 安全告警数据、历史事件 |
| 输出 | 高危告警→威胁处置、中危→工单、低危→归档、误报→记录 |
| 决策权 | 自主：分类/优先级/误报过滤；确认：高危告警处置 |

> **v2.1更新**: 整合原threat-intel的威胁情报查询能力，使用ip-reputation skill进行IP信誉查询

#### 3.3 资产管理Agent
**目录**: `monitoring/asset-mgmt/`
**专业领域**: 网络资产发现、资产分类、资产变更监控、资产风险管理

| 属性 | 说明 |
|------|------|
| 核心职责 | 资产扫描、识别、分类、变更监控、影响分析、资产报告 |
| 输入 | 网络扫描范围、资产管理数据库、变更通知 |
| 输出 | 资产清单、资产变更通知、资产风险报告 |
| 协作 | 向日志分析Agent提供资产清单 |

> **资产库更新 v3.0** (2026-02-17): 详见 [资产库README](../asset-database/README.md) 和 [Agent使用指南](../docs/asset-database-AGENT-GUIDE.md)

---

### 4. 防御响应组 (Defense Group)

#### 4.1 威胁处置Agent
**目录**: `defense/threat-response/`
**专业领域**: 安全事件处置、威胁遏制、情报收集、系统修复、恢复验证

| 属性 | 说明 |
|------|------|
| 核心职责 | 事件接收、威胁遏制、清除、修复、验证、处置报告、情报收集 |
| 使用Skills | asg-firewall-api, nsf-firewall-api, network-device-cli, kali-pentest |
| 决策分级 | 低：AI自主；中：AI+通知；高：人工确认 |
| 预授权操作 | 阻断IP、禁用账户、隔离终端、关闭端口 |

#### 4.2 取证分析Agent
**目录**: `defense/forensic/`
**专业领域**: 数字取证、证据保全、溯源分析、攻击链还原

| 属性 | 说明 |
|------|------|
| 核心职责 | 证据收集、保全、内存分析、磁盘分析、网络分析、溯源分析、攻击链还原、取证报告 |
| 输入 | 受影响系统、事件时间范围、取证授权 |
| 输出 | 取证证据包、溯源分析报告、攻击链图、取证报告 |

#### 4.3 策略执行Agent
**目录**: `defense/policy-exec/`
**专业领域**: 安全策略配置、策略变更、策略合规检查

| 属性 | 说明 |
|------|------|
| 核心职责 | 策略解析、设备配置、策略下发、配置验证、合规检查、策略备份 |
| 使用Skills | asg-firewall-api, nsf-firewall-api |
| 决策分级 | 标准策略：AI自主；重要策略：AI+通知；核心策略：人工确认 |

---

### 5. 评估优化组 (Assessment Group)

#### 5.1 漏洞评估Agent
**目录**: `assessment/vuln-assessment/`
**专业领域**: 漏洞扫描、漏洞验证、渗透测试、安全评估

| 属性 | 说明 |
|------|------|
| 核心职责 | 漏洞扫描、验证、渗透测试、风险评估、修复建议、测试报告 |
| 使用Skills | kali-pentest, asset-database-sdk |
| 扫描策略 | 核心：每月/业务低峰；一般：每季度；测试：每周 |
| 重要限制 | 渗透测试需书面授权、时间窗口内、测试范围内、不影响业务 |

#### 5.2 风险与合规Agent
**目录**: `assessment/risk-compliance/`
**专业领域**: 风险评估、合规检查、差距分析、整改建议

| 属性 | 说明 |
|------|------|
| 核心职责 | 风险识别、分析、量化、合规检查、差距分析、整改建议 |
| 检查标准 | 等保2.0三级、ISO 27001:2022 |
| 检查周期 | 内部自查：每季度；外部审计：每年；专项：按需 |
| 输入 | 漏洞信息、威胁情报、资产价值 |

---

### 6. 运维管理组 (Operations Group)

#### 6.1 网络运维Agent
**目录**: `operations/network-ops/`
**专业领域**: 网络设备配置、路由管理、网络故障排查、网络性能监控

| 属性 | 说明 |
|------|------|
| 核心职责 | 网络设备配置、路由策略、VPN配置、故障排查、性能监控、拓扑管理 |
| 使用Skills | network-device-cli, distributed-executor-api |
| 支持设备 | 华为、H3C、思科、锐捷等 |

#### 6.2 系统运维Agent
**目录**: `operations/server-ops/`
**专业领域**: 统一管理服务器和终端设备的配置、部署、故障处理、补丁管理

| 属性 | 说明 |
|------|------|
| 核心职责 | 设备配置管理、服务部署维护、补丁管理、性能监控、故障处理、容量规划、备份恢复 |
| 管理对象 | 服务器（物理机、虚拟机、容器、云主机）+ 终端（PC、笔记本、工作站） |
| 使用Skills | distributed-executor-api |
| 特点 | 根据资产类型（Server/Endpoint）自动适配运维策略 |

---

## Agent协作关系

### 协作矩阵

| 协作场景 | 主要Agent | 协作Agent | 目的 |
|---------|----------|----------|------|
| 安全事件处理 | 日志分析 → 告警研判 → 威胁处置 | 取证分析 | 事件响应 |
| 漏洞管理 | 漏洞评估 → 系统运维 | 资产管理 | 修复闭环 |
| 安全评估 | 漏洞评估 → 风险与合规 | 威胁情报 | 综合评估 |
| 运维变更 | AI协调器 → 运维Agent | 资产管理 | 变更执行 |

### 消息流向

```
[人类管理员]
      ↓ 指令
[AI协调器]
      ↓ 分配
  ┌───┴───┬─────────┬─────────┐
  │       │         │         │
[监控组][防御组][评估组][运维组]
  │       │         │         │
  └───┬───┴─────────┴─────────┘
      ↓ 汇总
[AI协调器]
      ↓ 报告
[人类管理员]
```

---

## Agent状态管理

### 状态定义

| 状态 | 说明 |
|------|------|
| idle | 空闲，等待任务 |
| busy | 忙碌，执行任务中 |
| error | 错误，需要人工介入 |
| maintenance | 维护中，暂停服务 |

### 心跳机制

每个Agent定期向AI协调器发送心跳：
- 频率：每30秒
- 内容：状态、当前任务、资源使用

---

## 创建新Agent

1. 复制模板：`cp .template/AGENT_TEMPLATE.md <group>/<agent-name>/AGENT.md`
2. 填写Agent定义
3. 创建提示词文件：`<agent-name>_prompt.md`
4. 更新本README
5. 测试验证

---

**团队版本**: v2.1
**Agent数量**: 10 (1协调器 + 1监管员 + 8专业Agent)
**最后更新**: 2026年3月19日

---

## v2.1 版本更新说明 (2026-03-19)

### 变更内容
- **删除威胁情报Agent (threat-intel)**：职责整合到告警研判Agent，使用ip-reputation skill实现威胁情报查询
- **告警研判Agent扩展能力**：新增ip-reputation skill，支持IP信誉情报查询

### 优化效果
- Agent数量：11 → 10（减少9%）
- 情报查询能力：从独立Agent变为Skill调用，响应更快

---

## v2.0 版本更新说明 (2026-03-17)

### 变更内容
- **删除事件响应Agent (incident-response)**：职责整合到AI协调器
- **删除渗透测试Agent (pentest)**：职责整合到漏洞评估Agent
- **删除风险评估Agent (risk-assessment)**：与合规检查Agent合并为风险与合规Agent
- **删除合规检查Agent (compliance)**：与风险评估Agent合并为风险与合规Agent
- **删除补丁管理Agent (patch-mgmt)**：职责整合到系统运维Agent
- **新增风险与合规Agent (risk-compliance)**：综合风险评估和合规检查
- **AI协调器新增应急响应协调职责**：PDCERF流程协调
- **漏洞评估Agent扩展渗透测试能力**
- **系统运维Agent新增补丁管理职责**

### 优化效果
- Agent数量：15 → 11（减少27%）
- 职责边界：清晰明确
- 启动开销：降低
- 协调链路：缩短
