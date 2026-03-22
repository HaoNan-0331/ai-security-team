---
name: distributed-executor-api
description: 分布式命令执行系统API管理技能。此技能应在需要通过分布式命令执行系统对服务器和终端进行巡检、远程命令执行或其它系统支持的功能时使用。支持利用远程客户端执行SSH命令执行、HTTP请求执行、Telnet命令执行、本地命令执行、客户端管理等功能。支持单次和批量操作，巡检任务自动生成两个独立文件：分析报告（仅数据分析）和原始执行数据（命令、时间、返回结果），保存到用户桌面。需要用户提供服务端URL、用户名和密码进行认证。
---

# 分布式命令执行系统 API 管理技能

## 概述

本技能用于通过分布式命令执行系统的REST API对已部署的客户端进行远程管理和巡检操作。系统采用客户端-服务端架构，服务端提供REST API接口，客户端通过WebSocket连接到服务端并执行下发的任务。

## 系统架构

```
[用户] --> [Claude + 本技能] --> [服务端 REST API] --> [WebSocket] --> [客户端] --> [执行命令]
                                                              |
                                                              v
                                                    [SSH/HTTP/Telnet/本地命令]
```

## 触发条件

当用户请求以下操作时，触发此技能：
- 对服务器或终端进行健康巡检
- 通过SSH/Telnet执行远程命令
- 发送HTTP请求测试
- 在客户端本地执行系统命令
- 管理或查看客户端状态
- 批量对多个客户端执行操作

## 认证流程

### 步骤1：获取服务端连接信息

首次使用时，通过 `AskUserQuestion` 工具交互式获取以下信息：

| 参数 | 说明 | 示例 |
|------|------|------|
| server_url | 服务端API地址 | `https://192.168.10.248:8080` |
| username | 登录用户名 | `admin` |
| password | 登录密码 | `SecurePass123` |

### 步骤2：登录获取访问令牌

调用登录接口获取Bearer Token：

```bash
curl -k -X POST {server_url}/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"{username}","password":"{password}"}'
```

响应示例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**重要**：
- Token有效期为24小时
- 所有后续API调用需要在Header中携带：`Authorization: Bearer {access_token}`
- 使用 `-k` 参数跳过自签名证书验证

## API 接口参考

### 1. 客户端管理

#### 获取所有客户端
```
GET /api/clients
```

#### 获取在线客户端
```
GET /api/clients/online
```

#### 获取客户端详情
```
GET /api/clients/{client_id}
```

### 2. 命令执行

#### 执行SSH命令
```
POST /api/ssh/execute
```

请求体：
```json
{
  "client_id": "A1B2C3D4",
  "host": "192.168.1.1",
  "port": 22,
  "username": "admin",
  "password": "password123",
  "command": "show version",
  "timeout": 30
}
```

#### 执行Telnet命令
```
POST /api/telnet/execute
```

请求体：
```json
{
  "client_id": "A1B2C3D4",
  "host": "192.168.1.1",
  "port": 23,
  "username": "admin",
  "password": "password123",
  "command": "show version",
  "timeout": 30,
  "login_prompt": "login:",
  "password_prompt": "Password:"
}
```

#### 执行HTTP请求
```
POST /api/http/execute
```

请求体：
```json
{
  "client_id": "A1B2C3D4",
  "url": "https://api.example.com/users",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"name\":\"test\"}",
  "timeout": 30
}
```

#### 执行本地命令
```
POST /api/local/execute
```

请求体：
```json
{
  "client_id": "A1B2C3D4",
  "command": "systeminfo",
  "timeout": 30,
  "encoding": "gbk"
}
```

**注意**：Windows命令建议使用 `encoding: "gbk"`，Linux使用 `encoding: "utf-8"`

### 3. 结果查询

#### 查询任务结果
```
GET /api/sessions/{session_id}
```

响应示例：
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_id": "A1B2C3D4",
  "task_type": "ssh",
  "request_data": {
    "host": "192.168.1.1",
    "command": "show version"
  },
  "response_data": {
    "stdout": "Device Model: XYZ-1000\nSoftware Version: 1.0.0",
    "stderr": "",
    "exit_code": 0
  },
  "success": true,
  "error_message": null,
  "created_at": "2026-01-23T08:59:01.744250"
}
```

#### 查询客户端历史
```
GET /api/sessions/client/{client_id}?limit=100
```

## 执行流程

### 单客户端巡检流程

```
1. [认证] 获取访问令牌
2. [准备] 获取客户端列表，确认目标客户端在线
3. [执行] 并发执行所有巡检命令，获取session_id列表
4. [等待] 轮询查询所有结果（间隔2秒，超时60秒）
5. [分析] 分析执行结果
6. [生成] 生成两个独立文件
7. [保存] 将两个文件保存到用户桌面
```

### 批量操作流程

```
1. [认证] 获取访问令牌
2. [准备] 获取所有目标客户端，确认在线状态
3. [并发] 同时向多个客户端发送任务
4. [收集] 轮询收集所有session的结果
5. [汇总] 汇总所有结果
6. [生成] 生成两个独立文件
7. [保存] 将两个文件保存到用户桌面
```

## 轮询结果实现

由于任务执行是异步的，需要轮询查询结果：

```python
def wait_for_result(session_id, timeout=60, interval=2):
    """
    轮询等待任务结果
    """
    start = time.time()
    while time.time() - start < timeout:
        result = get_session(session_id)
        if result.get('response_data') is not None:
            return result
        time.sleep(interval)
    raise TimeoutError(f"任务执行超时: {session_id}")
```

## 巡检内容

巡检任务包含以下检查项（根据操作系统类型自动选择）：

### Windows 系统巡检

| 检查项 | 命令 | 说明 |
|--------|------|------|
| 系统信息 | `systeminfo` | 主机名、OS版本、硬件配置、运行时间 |
| 磁盘空间 | `wmic logicaldisk get DeviceID,Size,FreeSpace,FileSystem` | 各分区容量和使用率 |
| 内存使用 | `wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value` | 内存总量和可用量 |
| 网络连接 | `netstat -ano \| findstr ESTABLISHED` | 活跃网络连接 |
| **系统日志** | `wevtutil qe System /c:20 /rd:true /f:text` | 最近20条系统日志 |
| **安全日志** | `wevtutil qe Security /c:10 /rd:true /f:text` | 最近10条安全日志（需管理员权限） |
| **应用程序日志** | `wevtutil qe Application /c:10 /rd:true /f:text` | 最近10条应用程序日志 |

### Linux 系统巡检

| 检查项 | 命令 | 说明 |
|--------|------|------|
| 系统信息 | `uname -a && cat /etc/os-release` | 内核版本、发行版信息 |
| 运行时间 | `uptime` | 系统运行时间和负载 |
| 磁盘使用 | `df -h` | 各挂载点容量和使用率 |
| 内存使用 | `free -h` | 内存和交换分区使用情况 |
| 网络连接 | `ss -tuln` | 监听端口 |
| **系统日志** | `journalctl -p err -n 20 --no-pager` | 最近20条错误级别日志 |
| **安全日志** | `tail -50 /var/log/secure 2>/dev/null \| tail -20` | 最近20条安全日志 |
| **系统消息日志** | `tail -20 /var/log/messages` | 最近20条系统消息 |

### 网络设备巡检

| 检查项 | 命令 | 说明 |
|--------|------|------|
| 版本信息 | `display version` / `show version` | 设备型号、软件版本 |
| CPU使用 | `display cpu-usage` / `show processes cpu` | CPU使用率 |
| 内存使用 | `display memory-usage` / `show memory statistics` | 内存使用率 |
| 接口状态 | `display interface brief` / `show ip interface brief` | 接口状态 |
| 日志信息 | `display logbuffer` / `show logging` | 设备日志 |

## 输出规范

### 文件生成规则

巡检完成后，**按批次**生成两个独立的Markdown文件并保存到用户桌面：

1. **分析报告**：`巡检分析报告_{批次ID}_{日期时间}.md`
2. **原始数据**：`巡检原始数据_{批次ID}_{日期时间}.md`

**重要**：一个批次（可能包含多台设备）只生成两个文件，所有设备的数据汇总在这两个文件中。

### 获取桌面路径

使用以下方式获取用户桌面路径：
```bash
# Windows
powershell -Command "[Environment]::GetFolderPath('Desktop')"

# Linux
echo ~/Desktop
```

### 文件命名格式

```
巡检分析报告_20260212_110502.md
巡检原始数据_20260212_110502.md
```

---

## 报告模板文件

巡检完成后，使用以下模板文件生成报告。模板文件位于 `templates/` 目录：

| 模板文件 | 用途 | 说明 |
|----------|------|------|
| `templates/analysis-report-template.md` | 批次分析报告模板 | 包含批次概要和多设备汇总 |
| `templates/device-analysis-template.md` | 单设备分析模板 | 用于循环填充每台设备的分析 |
| `templates/raw-data-template.md` | 批次原始数据模板 | 包含批次任务汇总 |
| `templates/device-raw-data-template.md` | 单设备原始数据模板 | 用于循环填充每台设备的原始数据 |
| `templates/task-detail-template.md` | 任务详情模板 | 单个任务的原始数据格式 |

### 模板使用流程

1. **读取主模板**：读取 `analysis-report-template.md` 或 `raw-data-template.md`
2. **循环填充设备数据**：
   - 读取 `device-analysis-template.md` 或 `device-raw-data-template.md`
   - 为每台设备填充数据，拼接成完整内容
   - 替换主模板中的 `{device_analysis_sections}` 或 `{device_raw_data_sections}`
3. **循环填充任务详情**：使用 `task-detail-template.md` 填充每个任务
4. **保存到桌面**：使用 Write 工具将填充后的内容保存到用户桌面

### 批次分析报告占位符

**主模板 (analysis-report-template.md)**：
- `{batch_id}` - 批次ID（使用时间戳或UUID）
- `{inspection_time}` - 巡检时间
- `{device_count}` - 设备数量
- `{start_time}` - 开始时间
- `{end_time}` - 结束时间
- `{success_count}` - 成功设备数
- `{fail_count}` - 失败设备数
- `{total_tasks}` - 总任务数
- `{duration}` - 总耗时
- `{device_overview_rows}` - 设备健康概览表格行
- `{device_analysis_sections}` - 各设备详细分析（循环填充device-analysis-template）
- `{critical_issues_rows}` - 严重问题表格行（跨设备汇总）
- `{warning_issues_rows}` - 警告事项表格行（跨设备汇总）
- `{normal_devices_list}` - 正常状态设备列表
- `{avg_cpu_score}` - CPU平均评分
- `{avg_memory_score}` - 内存平均评分
- `{avg_disk_score}` - 磁盘平均评分
- `{avg_network_score}` - 网络平均评分
- `{avg_log_score}` - 日志平均评分
- `{avg_total_score}` - 总平均分
- `{overall_health}` - 整体健康状态

**单设备分析模板 (device-analysis-template.md)**：
- `{device_index}` - 设备序号
- `{hostname}` - 主机名
- `{client_id}` - 客户端ID
- `{os_info}` - 操作系统信息
- `{ip_address}` - IP地址
- `{total_memory}` - 总内存
- `{free_memory}` - 可用内存
- `{memory_percent}` - 内存使用率
- `{memory_status}` - 内存状态
- `{disk_summary}` - 磁盘摘要
- `{disk_status}` - 磁盘状态
- `{connection_count}` - 网络连接数
- `{network_status}` - 网络状态
- `{device_log_rows}` - 日志分析表格行
- `{device_score}` - 设备健康评分
- `{device_health_level}` - 健康等级
- `{device_issues}` - 设备问题列表

### 批次原始数据占位符

**主模板 (raw-data-template.md)**：
- `{batch_id}` - 批次ID
- `{inspection_time}` - 巡检时间
- `{device_count}` - 设备数量
- `{batch_summary_rows}` - 批次任务汇总表格行
- `{device_raw_data_sections}` - 各设备原始数据（循环填充device-raw-data-template）

**单设备原始数据模板 (device-raw-data-template.md)**：
- `{device_index}` - 设备序号
- `{hostname}` - 主机名
- `{client_id}` - 客户端ID
- `{os_info}` - 操作系统信息
- `{ip_address}` - IP地址
- `{device_task_summary_rows}` - 设备任务汇总表格行
- `{device_task_details}` - 任务详情（循环填充task-detail-template）

**任务详情模板 (task-detail-template.md)**：
- `{task_number}` - 任务序号
- `{task_name}` - 任务名称
- `{session_id}` - Session ID
- `{client_id}` - 客户端ID
- `{task_type}` - 任务类型
- `{command}` - 执行命令
- `{timeout}` - 超时时间
- `{encoding}` - 编码方式
- `{start_time}` - 开始时间
- `{end_time}` - 完成时间
- `{status}` - 执行状态
- `{exit_code}` - 退出码
- `{request_params}` - 请求参数JSON
- `{stdout}` - 标准输出
- `{stderr}` - 标准错误

---

## 日志巡检命令详解

### Windows 日志命令

```bash
# 系统日志（最近20条）
wevtutil qe System /c:20 /rd:true /f:text

# 安全日志（最近10条，需管理员权限）
wevtutil qe Security /c:10 /rd:true /f:text

# 应用程序日志（最近10条）
wevtutil qe Application /c:10 /rd:true /f:text

# 按级别筛选错误日志
wevtutil qe System /q:"*[System[(Level=2)]]" /c:10 /rd:true /f:text

# 按时间范围筛选（最近24小时）
wevtutil qe System /q:"*[System[TimeCreated[timediff(@SystemTime) <= 86400000]]]" /c:50 /rd:true /f:text

# PowerShell方式获取日志
powershell "Get-EventLog -LogName System -Newest 20 | Format-List"
powershell "Get-WinEvent -FilterHashtable @{LogName='System';Level=2,3} -MaxEvents 20"
```

### Linux 日志命令

```bash
# systemd日志（错误级别）
journalctl -p err -n 20 --no-pager

# systemd日志（最近1小时）
journalctl --since "1 hour ago" --no-pager

# 安全日志
tail -50 /var/log/secure 2>/dev/null | tail -20

# 系统消息日志
tail -20 /var/log/messages

# 认证日志
tail -20 /var/log/auth.log

# 内核日志
dmesg | tail -20

# 按服务筛选日志
journalctl -u nginx -n 20 --no-pager
journalctl -u sshd -n 20 --no-pager
```

---

## 错误处理

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 401 | 令牌无效或过期 | 重新登录获取新令牌 |
| 403 | 无权使用该客户端 | 提示用户联系管理员 |
| 404 | 客户端不存在 | 检查client_id是否正确 |
| 500 | 服务器内部错误 | 查看服务端日志 |

## 最佳实践

1. **执行前检查**: 先确认客户端在线状态
2. **超时设置**: 日志命令建议设置60秒超时
3. **编码处理**: Windows使用gbk，Linux使用utf-8
4. **批量控制**: 批量操作时控制并发数量，避免过载
5. **结果验证**: 检查success字段和exit_code确认执行成功
6. **文件保存**: 巡检完成后立即保存两个报告文件到桌面
7. **日志分析**: 重点关注错误(Error)和警告(Warning)级别日志

## 使用示例

### 示例1：Windows系统完整巡检

用户请求：
> 对客户端FC3C8E7A进行系统巡检

执行步骤：
1. 登录获取Token
2. 确认客户端在线
3. 并发执行7个巡检命令（系统信息、磁盘、内存、网络、系统日志、安全日志、应用日志）
4. 收集所有执行结果
5. 生成分析报告和原始数据两个文件
6. 保存到用户桌面

输出文件：
- `DESKTOP-VP07H4I_分析报告_20260212_110502.md`
- `DESKTOP-VP07H4I_原始数据_20260212_110502.md`

### 示例2：Linux系统巡检

用户请求：
> 对Linux服务器进行健康巡检

执行步骤：
1. 登录获取Token
2. 确认客户端在线
3. 并发执行8个巡检命令（系统信息、运行时间、磁盘、内存、网络、系统日志、安全日志、内核日志）
4. 收集所有执行结果
5. 生成分析报告和原始数据两个文件
6. 保存到用户桌面

### 示例3：批量网络设备巡检

用户请求：
> 对所有在线网络设备进行巡检

执行步骤：
1. 登录获取Token
2. 获取所有在线客户端
3. 筛选网络设备类型客户端
4. 并发向所有设备发送巡检命令
5. 收集所有执行结果
6. 汇总分析，生成批量报告
7. 保存两个文件到桌面
