---
description: 上元信安ASG防火墙REST API管理技能。此技能应在需要对ASG防火墙进行自动化运维操作时使用，包括接口管理、路由配置、策略管理、地址/服务对象、应用层控制、入侵防护、病毒防护、EDR联动、威胁情报、引流策略、镜像策略、用户认证、防火墙日志、Syslog、SNMP、SD-WAN、升级重启、授权和地址对象等场景。支持单次和批量操作，自动记录操作日志。需要用户提供从Web界面生成的Token进行认证。
---

# 上元信安ASG防火墙REST API管理技能

## 技能概述

本技能提供与上元信安ASG防火墙REST API交互的完整能力，支持通过Python脚本进行单次和批量运维操作。所有操作会自动记录日志，便于审计和故障排查。

## 功能范围与能力边界

**重要提示**：本技能仅支持对ASG防火墙执行**已定义的API操作**。如果用户提出的需求不在以下功能范围内，请直接告知用户该需求不在本技能的支持范围内。

### 支持的功能范围

本技能支持以下功能模块的操作：

| 模块 | 支持的操作 |
|------|-----------|
| **网络接口** | VLAN接口、GRE隧道、环回接口、旁路部署、端口镜像的增删改查 |
| **路由配置** | 静态路由（IPv4/IPv6）、策略路由（IPv4/IPv6）、ISP路由的增删改查 |
| **SSL VPN** | SSL VPN配置、监控、用户绑定、接口配置的查询和修改 |
| **策略管理** | 一体化策略的增删改查、启用禁用、移动；IP/域名黑名单的增删改查 |
| **威胁情报** | 威胁情报开关、信誉值配置、云端联动、自定义情报的配置和查询 |
| **入侵防护** | IPS模板和事件集的增删改查 |
| **病毒防护** | 病毒防护模板和扫描文件类型的增删改查 |
| **EDR联动** | EDR中心配置、安装路径、联动策略、资产列表的查询和配置 |
| **引流/镜像策略** | 引流策略和镜像策略的增删改查 |
| **用户认证** | 用户管理、SNMP同步、微信认证配置的增删改查 |
| **日志监控** | 防火墙日志查询导出、Syslog配置 |
| **系统管理** | SD-WAN配置、固件版本查询、升级历史、备份恢复、授权激活 |
| **地址对象** | 地址对象和地址组对象的增删改查 |

### 不支持的功能范围

以下需求**不在本技能支持范围内**，如遇此类需求请直接告知用户：

| 功能类别 | 示例需求 | 应对方式 |
|----------|----------|----------|
| **非ASG防火墙设备** | 操作其他品牌防火墙、路由器、交换机 | 告知用户本技能仅支持上元信安ASG防火墙 |
| **非API功能** | 通过Web界面自动化操作、截图、UI交互 | 建议用户使用Web界面或相关RPA工具 |
| **网络层操作** | Ping、Telnet、SSH连接、端口扫描等 | 建议用户使用网络诊断工具 |
| **数据分析** | 流量分析、日志分析、报表生成 | 建议用户导出数据后使用分析工具 |
| **自定义开发** | 开发新功能、修改防火墙固件 | 建议联系设备厂商 |
| **硬件操作** | 设备重启、电源管理、硬件更换 | 建议用户通过物理控制台或Web界面操作 |
| **超出API能力** | 批量导入导出复杂配置、第三方系统集成 | 建议查看设备Web界面或联系技术支持 |
| **安全审计** | 渗透测试、漏洞扫描、安全评估 | 建议使用专业安全工具 |

### 判断方法

当用户提出需求时，可通过以下方式判断：

1. **查看功能模块列表**：确认需求是否属于上述15个功能模块之一
2. **检查API方法**：确认 `ASGApiClient` 类中是否有对应的方法
3. **参考文档**：查看 `references/` 目录下的API文档

**示例对话**：
- 用户："帮我分析上个月的防火墙日志，生成流量报表"
- 回答："抱歉，日志分析和报表生成不在本技能的支持范围内。本技能仅支持通过API查询和导出日志数据。您可以使用本技能导出日志后，使用数据分析工具进行进一步处理。"

## 执行方式说明

**重要：执行方式约束**

1. **必须使用Python脚本执行**：本技能的所有操作**必须**通过 `scripts/asg_api_client.py` 脚本执行，**严禁直接使用curl命令或http.request调用API**。

2. **执行模式**：
   - 优先使用Python代码导入 `ASGApiClient` 类进行操作
   - 或通过命令行调用 `python scripts/asg_api_client.py <host> <token> <operation> [params]`

3. **错误示例**（不要这样做）：
   ```bash
   # 错误：不要直接使用curl
   curl -X POST "https://192.168.1.1/api/policy?api_key=xxx" -d "{...}"
   ```

4. **正确示例**（应该这样做）：
   ```python
   from scripts.asg_api_client import ASGApiClient

   client = ASGApiClient(host="https://192.168.1.1", token="xxx", verify_ssl=False)
   result = client.add_policy({...})
   ```

### 适用场景
- 日常运维：策略配置、路由管理、接口配置
- 批量管理：批量添加策略、批量配置地址对象
- 故障应急：快速添加黑名单、调整策略、查看日志
- 自动化巡检：定期收集配置信息、检查系统状态

## 认证方式

**重要**：ASG防火墙使用Token认证，用户需要从Web界面生成认证Token。

### 获取Token步骤
1. 登录ASG防火墙Web管理界面
2. 进入"系统管理" > "管理员" > "API管理"
3. 点击"生成Token"按钮
4. 复制生成的Token（示例：`56els9k7vt3ov6h7gaiuu04la5`）

## 连接信息

在使用本技能时，需要提供以下连接信息：

| 参数 | 说明 | 示例 |
|------|------|------|
| host | 防火墙IP地址 | `https://172.17.108.86` 或 `http://192.168.1.1` |
| token | 认证Token | `56els9k7vt3ov6h7gaiuu04la5` |
| lang | 语言（可选） | `cn`（中文）或 `en`（英文） |

## 脚本位置

本技能的所有脚本位于：`scripts/`

- `asg_api_client.py` - 核心API客户端
- `asg_batch_operations.py` - 批量操作脚本
- `experience_manager.py` - 经验管理器（查询错误、搜索解决方案）
- `query_logs.py` - 日志查询工具
- `add_policy_with_address.py` - 策略添加工具（含地址对象创建）

## 使用方式

### 方式一：直接执行Python脚本

```bash
# 查看一体化策略（使用默认参数：protocol=1, vrf=vrf0, page=1, pageSize=10）
python scripts/asg_api_client.py https://192.168.163.10 YOUR_TOKEN get_policies

# 添加一体化策略（简化方法，推荐）
python scripts/asg_api_client.py https://192.168.163.10 YOUR_TOKEN add_policy_simple '{"source":"192.168.1.10","destination":"8.8.8.8","action":"deny","desc":"禁止访问"}'

# 添加一体化策略（完整方法）
python scripts/asg_api_client.py https://192.168.163.10 YOUR_TOKEN add_policy '{"protocol":"1","if_in":"any","if_out":"any","sip":"any","dip":"any","sev":"any","user":"any","app":"any","tr":"always","mode":"1","enable":"1","id":"1"}'

# 批量操作
python scripts/asg_batch_operations.py https://192.168.163.10 YOUR_TOKEN batch_config.json
```

### 方式二：在Python代码中调用

```python
from scripts.asg_api_client import ASGApiClient

# 创建客户端
client = ASGApiClient(
    host="https://192.168.163.10",
    token="YOUR_TOKEN",
    verify_ssl=False
)

# 获取一体化策略（使用默认参数）
policies = client.get_policies()
print(policies)

# 获取一体化策略（指定参数）
policies = client.get_policies(protocol="1", vrf="vrf0", page=1, page_size=10)
print(policies)

# 添加策略
result = client.add_policy({
    "id": "1",
    "protocol": "1",
    "if_in": "any",
    "if_out": "any",
    "sip": "any",
    "dip": "any",
    "sev": "any",
    "user": "any",
    "app": "any",
    "tr": "always",
    "mode": "1",
    "enable": "1"
})
```

## 功能模块

### 1. 网络接口
- VLAN接口配置
- GRE隧道配置
- 环回接口配置
- 旁路部署配置
- 端口镜像配置

### 2. 路由配置
- 静态路由（IPv4/IPv6）
- 策略路由（IPv4/IPv6）
- ISP路由

### 3. VPN配置
- SSL VPN配置

### 4. 策略管理
- 一体化策略（添加/修改/删除/查询/启用禁用/移动）
- 黑名单（IP/域名）
- 引流策略
- 镜像策略

### 5. 安全防护
- 威胁情报（情报策略/信誉值/云端联动/自定义情报）
- 入侵防护（模板/事件集）
- 病毒防护（模板/文件类型）
- EDR联动（中心配置/安装路径/联动策略/资产列表）

### 6. 用户认证
- 跨三层用户 + MAC绑定
- 用户管理（新建/编辑/删除/查询）
- SNMP用户同步
- 微信认证

### 7. 日志与监控
- 防火墙日志查询与导出
- Syslog日志加密传输
- SNMP配置

### 8. 系统管理
- SD-WAN配置
- 升级与重启（固件升级/特征库升级/系统备份恢复）
- 授权激活
- 重启操作

### 9. 地址对象
- 地址对象（添加/修改/删除）
- 地址组对象（添加/删除）

## API参数说明

### 通用参数
- `api_key`: 认证Token（必填）
- `lang`: 语言，`cn`中文或`en`英文（可选，默认cn）
- `vrf`: VRF实例名称（必填，默认vrf0）
- `page`: 页数（用于分页查询）
- `pageSize`: 每页条数（用于分页查询）

### 协议类型
- `protocol`: `1`表示IPv4，`2`表示IPv6

### 动作类型
- `mode`: `1`表示PERMIT（允许），`2`表示DENY（拒绝）

### 启用状态
- `enable`: `0`表示不启用，`1`表示启用

### 日志级别
- `log_level`: `0`紧急，`1`告警，`2`严重，`3`错误，`4`警示，`5`通知，`6`信息

## 批量操作模板

批量操作支持JSON和YAML格式，模板文件位于：`assets/templates/`

### JSON模板示例
```json
[
  {
    "method": "POST",
    "endpoint": "/api/policy",
    "params": {"api_key": "YOUR_TOKEN", "lang": "cn"},
    "data": {
      "id": "1",
      "protocol": "1",
      "if_in": "any",
      "if_out": "any",
      "sip": "any",
      "dip": "any",
      "sev": "any",
      "user": "any",
      "app": "any",
      "tr": "always",
      "mode": "1",
      "enable": "1"
    }
  },
  {
    "method": "GET",
    "endpoint": "/api/policy",
    "params": {"api_key": "YOUR_TOKEN", "lang": "cn", "protocol": "1", "vrf": "vrf0", "page": 1, "pageSize": 10}
  }
]
```

### YAML模板示例
```yaml
- method: POST
  endpoint: /api/blacklist
  params:
    api_key: YOUR_TOKEN
    lang: cn
  data:
    ip_type: "1"
    ip: "1.1.1.1"
    age: "300"
    enable: "1"

- method: GET
  endpoint: /api/blacklist
  params:
    api_key: YOUR_TOKEN
    lang: cn
    ip_type: "1"
```

## 日志记录

**自动经验记录功能（默认启用）**

本技能支持**自动记录每次操作到经验库**，便于后续分析和知识积累：

### 双重日志记录机制

1. **API日志** (`logs/api_log_YYYYMMDD.json`)
   - 记录原始API调用详情
   - 包含完整的请求和响应数据
   - 用于技术调试和审计

2. **经验库日志** (`experiences/auto_log.json`)
   - 记录操作摘要和执行结果
   - 自动分析成功/失败状态
   - 用于经验积累和问题排查

### 配置选项

```python
# 默认启用自动经验记录
client = ASGApiClient(
    host="https://192.168.1.1",
    token="YOUR_TOKEN",
    verify_ssl=False
    # enable_experience_logging=True  # 默认启用
)

# 如需禁用自动经验记录
client = ASGApiClient(
    host="https://192.168.1.1",
    token="YOUR_TOKEN",
    verify_ssl=False,
    enable_experience_logging=False  # 禁用
)
```

### 查看经验记录

```bash
# 查看经验库统计
python scripts/experience_manager.py stats

# 查看最近的操作记录
cat experiences/auto_log.json | tail -20
```

## 响应格式

### 成功响应
```json
{
  "data": [...],
  "total": 10
}
```

### 错误响应
```json
{
  "code": "错误码",
  "str": "错误描述"
}
```

常见错误码：
- `250`: 参数错误
- `87`: 目标策略/对象不存在
- `90`: 出接口或入接口不存在
- `106`: 名称冲突
- `107`: 对象名称不存在
- `-22`: 非法的IP地址

## 常见操作示例

### 添加一体化策略（简化方法 - 推荐）

`add_policy_simple` 是一个简化方法，会自动创建源/目标地址对象（如果不存在）：

```python
# 使用IP地址直接添加策略，自动处理地址对象
client.add_policy_simple(
    source_ip="192.168.1.10",
    dest_ip="8.8.8.8",
    action="deny",  # 或 "permit"
    description="禁止访问Google DNS"
)
```

**参数说明**：
- `source_ip`: 源IP地址
- `dest_ip`: 目标IP地址
- `action`: `"permit"`(允许) 或 `"deny"`(拒绝)
- `description`: 策略描述
- `policy_id`: 策略ID（可选，自动获取下一个可用ID）
- 其他可选参数：`protocol`, `if_in`, `if_out`, `sev`, `user`, `app`, `tr` 等

**注意**：此方法会自动创建名为 `src_xxx_xxx_xxx_xxx` 和 `dst_xxx_xxx_xxx_xxx` 的地址对象

### 添加一体化策略（完整方法）
```python
client.add_policy({
    "id": "1",
    "protocol": "1",
    "if_in": "any",
    "if_out": "any",
    "sip": "any",
    "dip": "any",
    "sev": "any",
    "user": "any",
    "app": "any",
    "tr": "always",
    "mode": "1",
    "enable": "1",
    "syslog": "1",
    "log_level": "6"
})
```

### 添加IP黑名单
```python
client.add_ip_blacklist({
    "ip_type": "1",
    "ip": "1.1.1.1",
    "age": "300",
    "enable": "1"
})
```

### 添加地址对象
```python
client.add_address({
    "name": "test_addr",
    "desc": "测试地址对象",
    "type": 0,
    "item": [
        {"host": "1.1.1.1", "type": 0},
        {"net": "192.168.1.0/24", "type": 1}
    ]
})
```

### 查询防火墙日志
```python
client.get_firewall_logs(
    sid="custom_query_id",
    time_type="one_day",
    start_time="2023-04-10 00:00:00",
    end_time="2023-04-11 00:00:00"
)
```

### 获取入侵防护模板
```python
client.get_ips_templates()
```

### 添加病毒防护模板
```python
client.add_av_template({
    "name": "病毒防护模板1",
    "desc": "测试模板",  # 必填参数
    "enable": "0",
    "action": "0",
    "http": "0",
    "ftp": "1",
    "smtp": "1",
    "imap": "1",
    "pop3": "0",
    "apt_enable": "1"
})
```

**注意**：
- `desc` 是必填参数，必须提供描述
- 所有参数值必须是字符串类型（如 "1" 而不是 1）
- `action`: "0"=通过, "1"=阻断
- `enable`: "0"=关闭, "1"=启用

## 注意事项

1. **认证Token安全**：Token具有较高权限，请妥善保管，不要泄露
2. **操作幂等性**：添加操作如果ID或名称已存在会失败，请先查询后操作
3. **批量操作顺序**：批量操作按顺序执行，建议先查询后添加/修改
4. **日志级别**：日志级别（0-6）对应紧急到信息，请根据需要选择
5. **协议类型**：注意区分IPv4（protocol=1）和IPv6（protocol=2）
6. **策略ID范围**：策略ID范围为1-10000
7. **生命周期参数**：黑名单age参数-1表示永久，单位为秒

## 参考文档

详细的API文档位于：`references/` 目录

- `overview/` - 概述和认证
- `network/` - 网络接口和路由
- `policy/` - 策略管理
- `objects/` - 地址和服务对象
- `security/` - 安全防护（威胁情报、入侵防护、病毒防护）
- `collaboration/` - 联动配置（EDR）
- `application_config/` - 应用层控制
- `system/` - 系统管理（升级、重启、日志）
- `appendix/` - 附录（错误码、参数说明）

## 故障排查

### 连接失败
- 检查防火墙IP地址是否正确
- 确认使用正确的协议（http/https）
- 检查网络连接

### 认证失败
- 确认Token是否有效
- 检查Token是否已过期

### 操作失败
- 查看响应中的code和str字段
- 检查参数是否符合API文档要求
- 查看日志文件了解详细错误信息

## 经验库系统

本技能内置了经验库系统，用于记录和分享在使用ASG防火墙API过程中积累的经验和解决方案。

### 经验库结构

```
skills/asg-firewall-api/experiences/
├── errors.json       # 错误码手册（10+ 错误码）
├── solutions.json    # 解决方案库（10+ 解决方案）
├── pitfalls.md       # 常见陷阱文档（15+ 陷阱）
└── auto_log.json     # 自动操作日志
```

### 使用经验管理器

```bash
# 查看经验库统计
python scripts/experience_manager.py stats

# 查询错误码
python scripts/experience_manager.py lookup 88

# 搜索解决方案
python scripts/experience_manager.py search 策略

# 导出经验库（分享功能）
python scripts/experience_manager.py export my_experience.zip

# 导入经验库
python scripts/experience_manager.py import my_experience.zip
```

### Python代码中使用经验管理器

```python
from scripts.experience_manager import ExperienceManager

# 创建管理器
mgr = ExperienceManager()

# 查询错误码
error_info = mgr.lookup_error_code('88')
print(f"错误: {error_info['name']}")
print(f"描述: {error_info['description']}")
print(f"解决方案: {error_info['solutions']}")

# 搜索解决方案
solutions = mgr.search_solutions('策略添加失败')
for sol in solutions:
    print(f"[{sol['id']}] {sol['title']}")
    print(f"  症状: {sol['symptoms']}")
    print(f"  步骤: {sol['steps']}")

# 记录操作
mgr.log_operation(
    operation='add_policy',
    endpoint='/api/policy',
    params={'api_key': 'xxx'},
    data={'id': '3', ...},
    response={'success': True},
    notes='成功添加拒绝策略'
)

# 导出经验库
mgr.export_to_package('team_experience.zip')
```

### 经验分享功能

经验库支持导出为ZIP包，方便在团队间分享：

1. **导出经验库**：
   ```bash
   python scripts/experience_manager.py export team_exp_20260204.zip
   ```

2. **分享ZIP包**：将生成的ZIP包发送给团队成员

3. **导入经验库**：
   ```bash
   python scripts/experience_manager.py import team_exp_20260204.zip
   ```

4. **合并模式**：导入时使用 `--merge` 参数合并现有经验：
   ```python
   mgr.import_from_package('team_exp.zip', merge=True)
   ```

### 常见错误码速查

| 错误码 | 名称 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | 无需处理 |
| 87 | 目标策略/对象不存在 | 先查询确认对象存在 |
| 88 | 参考对象不存在 | 检查地址对象名称、refer_id参数 |
| 90 | 出接口或入接口不存在 | 检查接口名称或使用any |
| 106 | 名称冲突 | 使用不同名称或更新现有对象 |
| 107 | 对象名称不存在 | 检查对象名称拼写 |
| 250 | 参数错误 | 检查所有必填参数 |
| 926 | Web访问控制模板不存在 | 检查模板名称或设为空 |

### 常见陷阱速查

1. **地址对象命名**：
   - `add_policy_simple` 会自动创建地址对象
   - 命名格式为 `src_xxx_xxx_xxx_xxx` 和 `dst_xxx_xxx_xxx_xxx`（点号替换为下划线）
   - 例如：`192.168.1.1` → `src_192_168_1_1`

2. **策略参数完整性**：添加策略时需提供完整的必填参数列表

3. **参数类型**：所有参数应为字符串类型（如 `"1"` 而不是 `1`）

4. **refer_id设置**：添加新策略时设为 `"0"`

5. **空响应处理**：某些API成功时返回空响应，表示操作成功

6. **SSL验证**：设置 `verify_ssl=False`

7. **host格式**：需包含协议前缀（`https://` 或 `http://`）

8. **病毒防护模板**：`desc` 是必填参数，不能为空

9. **文件类型扫描**：文件类型必须以 `*.` 开头，如 `*.exe`

详细内容请查看 `experiences/pitfalls.md` 文件。
