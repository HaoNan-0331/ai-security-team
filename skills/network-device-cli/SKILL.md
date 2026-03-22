---
name: network-device-cli
description: 网络设备命令行交互技能。此技能应在需要对网络设备（华为、H3C、思科、锐捷等）进行命令行运维操作时使用，包括SSH/Telnet/串口连接、配置管理、故障诊断、健康巡检等场景。使用显式连接参数，适用于单设备操作、故障应急处理和自动化巡检任务。
---

# 网络设备命令行交互技能

本技能提供网络设备命令行级别的自动化运维能力，支持主流网络设备厂商的统一管理。

## 技能用途

本技能用于网络设备的自动化运维操作，包括但不限于：
- 设备连接管理（SSH/Telnet/串口）
- 命令执行（逐条执行，遇错中断）
- 配置查询、备份和恢复
- 设备健康检查和巡检
- 故障诊断和应急处理
- 批量设备操作（交互式输入）

## 支持的设备厂商

- 华为 (Huawei)
- 华三 (H3C)
- 思科 (Cisco IOS/NX-OS)
- 锐捷 (Ruijie)
- 其他支持标准CLI的设备

## 核心架构

```
scripts/
├── 【核心层】基础组件
│   ├── base_executor.py       # 执行器基类（命令帮助查询）
│   └── experience_manager.py  # 经验库管理器
│
├── 【执行层】厂商专属执行器
│   ├── h3c_executor.py        # H3C设备执行器
│   ├── huawei_executor.py     # 华为设备执行器
│   ├── cisco_executor.py      # 思科设备执行器
│   └── ruijie_executor.py     # 锐捷设备执行器
│
└── 【应用层】业务功能
    ├── config_backup.py       # 配置备份/恢复
    ├── health_check.py        # 健康检查/巡检
    └── batch_manager.py       # 批量操作
```

## 厂商专属执行器

每个厂商都有专属的执行器，负责连接设备并执行命令。执行器自动集成经验库，处理已知问题。

### 统一接口格式

所有执行器使用显式连接参数：

```bash
python scripts/<vendor>_executor.py --host <IP> --username <用户> --password <密码> --commands "<命令1>" "<命令2>"
```

### 通用参数

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `--host` | 是 | 设备IP地址或主机名 | `192.168.1.1` |
| `--username` | 是 | 登录用户名 | `admin` |
| `--password` | 是 | 登录密码 | `password123` |
| `--port` | 否 | SSH端口，默认22 | `22` |
| `--commands` | 是 | 要执行的命令列表 | `"display version"` |
| `--commands-json` | 否 | 从JSON读取命令（使用`-`表示stdin） | `-` |
| `--output` | 否 | 结果输出文件路径 | `result.json` |
| `--query-help` | 否 | 查询命令帮助语法 | `"undo nat"` |
| `--auto-help` | 否 | 命令失败时自动查询帮助 | 无 |

### H3C执行器

```bash
# 基本命令执行
python scripts/h3c_executor.py --host 192.168.56.3 --username admin --password xxx --commands "display version" "display vlan"

# 从JSON文件读取命令
echo '["display version", "display vlan"]' | python scripts/h3c_executor.py --host 192.168.56.3 --username admin --password xxx --commands-json -

# 保存结果到文件
python scripts/h3c_executor.py --host 192.168.56.3 --username admin --password xxx --commands "display version" --output result.json

# 查询命令帮助
python scripts/h3c_executor.py --host 10.0.254.2 --username admin --password xxx --query-help "undo nat server protocol tcp global current-interface"

# 命令失败时自动查询帮助
python scripts/h3c_executor.py --host 10.0.254.2 --username admin --password xxx --commands "display version" --auto-help
```

**H3C执行器特点：**
- 使用 `invoke_shell` 模式（更稳定）
- 自动处理分页（`---- More ----`）
- 自动修复 `save` 命令（添加 `force` 参数）
- **支持命令帮助查询**（`--query-help` 查询语法，`--auto-help` 失败时自动查询）

### 华为执行器

```bash
# 执行命令
python scripts/huawei_executor.py --host 192.168.1.1 --username admin --password xxx --commands "display version" "display vlan"

# 查询命令帮助
python scripts/huawei_executor.py --host 192.168.1.1 --username admin --password xxx --query-help "undo nat"

# 命令失败时自动查询帮助
python scripts/huawei_executor.py --host 192.168.1.1 --username admin --password xxx --commands "display version" --auto-help
```

**华为执行器特点：**
- 使用 `invoke_shell` 模式
- 自动处理分页（`---- More ----`）
- 与H3C类似的CLI风格
- **支持命令帮助查询**（`--query-help` / `--auto-help`）

### 思科执行器

```bash
# 执行命令
python scripts/cisco_executor.py --host 192.168.1.1 --username admin --password xxx --commands "show version" "show vlan brief"

# 查询命令帮助
python scripts/cisco_executor.py --host 192.168.1.1 --username admin --password xxx --query-help "no ip nat"

# 命令失败时自动查询帮助
python scripts/cisco_executor.py --host 192.168.1.1 --username admin --password xxx --commands "show version" --auto-help
```

**思科执行器特点：**
- 使用 `invoke_shell` 模式
- 自动处理分页（`--More--`）
- 支持 `enable` 密码
- 与华为/H3C不同的命令语法（`show` vs `display`）
- **支持命令帮助查询**（`--query-help` / `--auto-help`）

### 锐捷执行器

```bash
# 执行命令
python scripts/ruijie_executor.py --host 192.168.1.1 --username admin --password xxx --commands "show version" "show vlan"

# 查询命令帮助
python scripts/ruijie_executor.py --host 192.168.1.1 --username admin --password xxx --query-help "no ip nat"

# 命令失败时自动查询帮助
python scripts/ruijie_executor.py --host 192.168.1.1 --username admin --password xxx --commands "show version" --auto-help
```

**锐捷执行器特点：**
- 使用 `invoke_shell` 模式
- 自动处理分页（`--More--` / `---- More ----`）
- 与思科类似的CLI风格
- **支持命令帮助查询**（`--query-help` / `--auto-help`）

### 执行器返回格式

所有执行器统一返回JSON格式：

```json
{
  "success": true,
  "executed": 2,
  "total": 3,
  "failed_at": null,
  "results": [
    {
      "command": "display version",
      "success": true,
      "output": "H3C Comware Software...",
      "error": null,
      "help": null
    },
    {
      "command": "display vlan",
      "success": false,
      "output": "% Error: Unrecognized command",
      "error": "命令执行错误: Unrecognized command",
      "help": "display vlan ?\r\n  vpn-instance  Specify a VPN instance\r\n..."
    }
  ]
}
```

**字段说明：**
- `command`: 执行的命令
- `success`: 是否成功
- `output`: 命令输出
- `error`: 错误信息（如有）
- `help`: 帮助信息（使用 `--auto-help` 时自动获取）

## 核心工作流程

### 1. 命令执行流程

```
用户需求
    │
    ▼
大模型生成命令列表
    │
    ▼
根据设备类型选择对应厂商执行器
    │
    ▼
执行器逐条执行命令
    │
    ├─ 成功 → 继续下一条
    │
    └─ 失败 → 中断，返回错误
            │
            ▼
         是否启用 auto-help？
            │
      ┌─────┴─────┐
      ▼           ▼
     是          否
      │           │
      ▼           ▼
  自动查询帮助   直接返回错误
      │           │
      └─────┬─────┘
            ▼
         大模型接收错误/帮助
            │
            ▼
      查询经验库处理方法
            │
      ┌─────┴─────┐
      ▼           ▼
   有经验       无经验
      │           │
      ▼           ▼
   应用方案    尝试解决
      │           │
      └─────┬─────┘
            ▼
      修改命令后重试
            │
            ▼
      如果是脚本问题
            │
            ▼
      修改执行器代码
```

### 2. 配置管理

备份、恢复或对比设备配置：

```bash
python scripts/config_backup.py --host <IP> --username <用户> --password <密码> [选项]
```

**可用操作：**

| 操作 | 参数 | 说明 |
|------|------|------|
| 备份 | `--backup` | 将当前配置保存到本地文件 |
| 恢复 | `--restore <文件>` | 从备份文件恢复配置 |
| 对比 | `--compare <文件>` | 比较当前配置与备份文件的差异 |

**示例：**
```bash
# 备份配置
python scripts/config_backup.py --host 192.168.1.1 --username admin --password xxx --backup

# 恢复配置
python scripts/config_backup.py --host 192.168.1.1 --username admin --password xxx --restore backup_20250101.json

# 对比配置
python scripts/config_backup.py --host 192.168.1.1 --username admin --password xxx --compare backup_20250101.json
```

### 3. 健康检查与巡检

执行设备健康检查和自动巡检：

```bash
python scripts/health_check.py --host <IP> --username <用户> --password <密码> --vendor <厂商> [选项]
```

**检查项目包括：**
- CPU和内存使用率
- 接口状态和流量统计
- 路由表完整性
- ARP/MACTable状态
- 日志中的错误和告警
- 端口错误和丢包统计
- 冗余协议状态（VRRP/HSRP/Standalone）

**示例：**
```bash
# H3C设备健康检查
python scripts/health_check.py --host 192.168.1.1 --username admin --password xxx --vendor h3c

# 生成Markdown报告
python scripts/health_check.py --host 192.168.1.1 --username admin --password xxx --vendor huawei --format markdown --output report.md
```

### 4. 批量设备操作

对多台设备执行相同操作（交互式输入设备信息）：

```bash
python scripts/batch_manager.py <操作类型>
```

**操作类型：**
- `commands`: 批量执行命令
- `backup`: 批量配置备份
- `health`: 批量健康检查

**执行流程：**
1. 选择操作类型
2. 交互式输入每台设备的连接信息
3. 输入完成后开始执行
4. 显示每台设备的执行结果

**示例：**
```bash
# 批量执行命令
python scripts/batch_manager.py commands
# 按提示输入设备信息，输入空行结束
```

## 经验库系统

经验库记录实际遇到的问题和解决方案，执行器会自动应用相关经验。

### 经验库位置

```
experiences/
├── index.json              # 经验索引
├── 001_command_execution.json  # H3C使用exec_command超时
├── 002_pagination.json         # 分页处理
├── 003_encoding.json           # Windows编码问题
└── 004_script_error.json       # save命令force参数
```

### 经验库管理

```bash
# 查看所有经验
python scripts/experience_manager.py

# 搜索经验
python scripts/experience_manager.py --search "timeout"

# 添加新经验（交互式）
python scripts/experience_manager.py --add

# 导出为Markdown
python scripts/experience_manager.py --export experiences.md
```

### 已有经验

| ID | 问题 | 解决方案 |
|----|------|----------|
| 001 | H3C使用exec_command超时 | 使用invoke_shell() |
| 002 | 配置显示不完整 | 自动处理分页 |
| 003 | Windows编码错误 | 使用errors='ignore' |
| 004 | save命令执行失败 | 自动添加force参数 |

## 参考文档

### 厂商命令对照表
查看 `references/vendor_commands.md` 获取：
- 各厂商基础命令对照
- 配置模式差异
- 常用查询命令
- 厂商特定功能命令

### 故障排查指南
查看 `references/troubleshooting_guide.md` 获取：
- 常见网络故障诊断流程
- 逐层排查方法（物理层→数据链路层→网络层）
- 日志分析技巧
- 性能瓶颈定位

### 巡检检查清单
查看 `references/inspection_checklist.md` 获取：
- 各厂商标准巡检项目
- 检查项的优先级分类
- 异常阈值定义
- 巡检周期建议

## 使用示例

### 场景1: 单设备配置查询
```
用户: 查询交换机192.168.1.1的所有接口状态
操作: python scripts/huawei_executor.py --host 192.168.1.1 --username admin --password xxx --commands "display interface brief"
     执行命令并返回结果
```

### 场景2: 设备健康巡检
```
用户: 对核心交换机进行健康检查
操作: python scripts/health_check.py --host 192.168.1.1 --username admin --password xxx --vendor h3c
     连接设备后执行全面检查，生成巡检报告
```

### 场景3: 配置备份
```
用户: 备份交换机192.168.1.1的配置
操作: python scripts/config_backup.py --host 192.168.1.1 --username admin --password xxx --backup
     按日期归档备份文件
```

### 场景4: 故障应急处理
```
用户: 核心链路中断，快速诊断问题
操作: python scripts/h3c_executor.py --host 192.168.1.1 --username admin --password xxx --commands "display interface brief" "display ip routing-table"
     使用troubleshooting_guide.md指导排查流程
     逐层检查物理链路→接口状态→路由→邻居关系
```

### 场景5: 批量配置备份
```
用户: 备份多台核心交换机配置
操作: python scripts/batch_manager.py backup
     交互式输入每台设备的连接信息
     批量执行配置备份
```

### 场景6: 查询命令帮助（命令语法不确定时）
```
用户: 不确定如何正确删除NAT映射
操作: python scripts/h3c_executor.py --host 10.0.254.2 --username admin --password xxx --query-help "undo nat server protocol tcp global current-interface"
     返回命令语法和可选参数，帮助生成正确的命令
```

### 场景7: 自动帮助模式（命令失败时自动查询）
```
用户: 执行可能出错的命令，需要自动获取帮助信息
操作: python scripts/h3c_executor.py --host 10.0.254.2 --username admin --password xxx --commands "display nat xxxx" --auto-help
     命令失败时自动查询帮助，在返回结果的 help 字段中包含语法提示
```

## 技术依赖

所有脚本依赖以下Python库：
- **Paramiko**: 底层SSH协议实现
- **PyYAML**: 配置文件解析
- **Rich**: 终端输出美化（可选）

安装依赖：
```bash
pip install paramiko pyyaml rich
```

## 最佳实践

1. **安全性**
   - 不要在脚本中硬编码密码
   - 使用交互式输入或环境变量传递密码
   - 敏感操作前先备份配置

2. **可靠性**
   - 执行变更前使用 `show run/display current-configuration` 备份
   - 批量操作前先在单台设备测试
   - 配置变更后保存配置（write/save）

3. **可追溯性**
   - 所有操作记录日志（时间、设备、命令、结果）
   - 配置备份按版本管理
   - 巡检报告归档保存

4. **错误处理**
   - 网络连接失败自动重试（最多3次）
   - 命令执行失败记录详细错误信息
   - 批量操作失败不影响其他设备

## 限制说明

- 需要显式提供每台设备的连接参数
- Telnet和串口连接安全性较低，建议仅在管理网络内使用
- 不同厂商、不同版本的命令语法可能有差异，执行器会尽量适配
- 某些厂商特定功能可能需要手动操作
- 生产环境变更操作前务必在测试环境验证
