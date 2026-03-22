# knowledge/ - AI安全团队知识库

> 本地知识库，为所有Agent提供专业知识查询支持

---

## 使用指南

### 查询方式

当Agent遇到不熟悉的领域时，应优先查询本知识库：

```
1. 使用 Read 工具读取 knowledge/ 目录下的相关文档
2. 使用 Grep 工具搜索关键词
3. 使用 Glob 工具查找特定类型的文档
```

### 查询示例

```bash
# 查找防火墙相关知识
Grep pattern="防火墙" path="knowledge/"

# 读取特定产品文档
Read "knowledge/products/security equipment/ASG防火墙/策略配置/策略配置.md"

# 查找所有配置模板
Glob pattern="knowledge/templates/**/*.md"
```

---

## 目录结构

```
knowledge/
├── products/              # 产品知识（安全设备、网络设备）
│   ├── security equipment/         # 防火墙产品
│   │   ├── ASG防火墙/     # 上元信安ASG
│   │   ├── RSAS漏洞扫描器  #绿盟远程安全评估系统RSAS
│   │   └── NF防火墙/      # 绿盟NF防火墙
│   └── network/           # 网络设备
│       ├── 华为/          # 华为交换机/路由器
│       ├── H3C/           # H3C设备
│       └── Cisco/         # 思科设备
│
├── technologies/          # 技术知识
│   ├── networking/        # 网络技术
│   │   ├── 路由技术/
│   │   ├── 交换技术/
│   │   └── VPN技术/
│   ├── security/          # 安全技术
│   │   ├── 渗透测试/
│   │   ├── 漏洞评估/
│   │   └── 应急响应/
│   └── protocols/         # 协议知识
│       ├── TCP_IP/
│       ├── HTTP_HTTPS/
│       └── DNS_DHCP/
│
├── compliance/            # 合规知识
│   ├── 等保2.0/           # 等保合规
│   │   ├── 三级要求/
│   │   └── 控制点清单/
│   └── ISO27001/          # ISO合规
│       └── Annex_A/
│
├── playbooks/             # 应急响应预案
│   ├── malware/           # 恶意软件响应
│   ├── intrusion/         # 入侵响应
│   └── ddos/              # DDoS响应
│
├── procedures/            # 标准操作流程
│   ├── daily/             # 日常运维流程
│   ├── emergency/         # 应急处理流程
│   └── change/            # 变更管理流程
│
└── templates/             # 配置模板
    ├── firewall/          # 防火墙配置模板
    ├── network/           # 网络配置模板
    └── report/            # 报告模板
```

---

## 知识库内容规范

### 文档格式

```markdown
# 标题

## 概述
（简要说明用途和场景）

## 详细内容
（核心知识点）

## 配置示例（可选）
（代码或命令示例）

## 注意事项（可选）
（重要提示和陷阱）

## 参考资料（可选）
（来源链接）
```

### 命名规范

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 产品文档 | `产品名称/功能模块/功能模块.md` | `ASG防火墙/策略配置/策略配置.md` |
| 技术文档 | `技术领域/子领域/主题.md` | `networking/路由技术/OSPF.md` |
| 预案文档 | `类型-场景.yaml` | `malware-ransomware.yaml` |
| 流程文档 | `序号_流程名称.md` | `01_防火墙策略变更流程.md` |
| 模板文档 | `模板名称_模板.md` | `防火墙基础配置_模板.md` |

---

## 各Agent推荐查询路径

| Agent | 推荐查询目录 | 典型场景 |
|-------|-------------|----------|
| orchestrator | `playbooks/`, `procedures/` | 协调响应、流程执行 |
| log-analysis | `technologies/security/` | 日志分析、异常检测 |
| alert-judgment | `technologies/security/` | 告警分类、威胁识别 |
| alert-judgment | `technologies/security/` | 告警分类、威胁情报查询 |
| threat-response | `playbooks/`, `products/firewalls/` | 威胁处置、设备操作 |
| forensic | `technologies/security/应急响应/` | 取证分析、溯源 |
| policy-exec | `products/firewalls/` | 策略配置、设备管理 |
| vuln-assessment | `technologies/security/渗透测试/` | 漏洞扫描、渗透测试 |
| risk-compliance | `compliance/` | 合规检查、风险评估 |
| network-ops | `products/network/`, `technologies/networking/` | 网络配置、故障排查 |
| server-ops | `templates/` | 系统配置、补丁管理 |

---

## 知识库维护

### 添加新知识

1. 确定知识类型（产品/技术/合规/预案/流程/模板）
2. 创建到对应目录
3. 按规范编写文档
4. 更新本README（如有新目录）

### 知识更新

- 产品版本更新时同步更新文档
- 发现错误或遗漏时及时修正
- 定期清理过时内容

---

*最后更新: 2026-03-17*
