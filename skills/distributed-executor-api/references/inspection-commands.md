# 常用巡检命令参考

## Windows 系统巡检命令

### 标准巡检命令集（7项）

| 序号 | 检查项 | 命令 | 超时 |
|------|--------|------|------|
| 1 | 系统信息 | `systeminfo` | 60s |
| 2 | 磁盘空间 | `wmic logicaldisk get DeviceID,Size,FreeSpace,FileSystem` | 30s |
| 3 | 内存使用 | `wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value` | 30s |
| 4 | 网络连接 | `netstat -ano | findstr ESTABLISHED` | 30s |
| 5 | 系统日志 | `wevtutil qe System /c:20 /rd:true /f:text` | 60s |
| 6 | 安全日志 | `wevtutil qe Security /c:10 /rd:true /f:text` | 60s |
| 7 | 应用程序日志 | `wevtutil qe Application /c:10 /rd:true /f:text` | 60s |

### 系统信息

| 命令 | 说明 |
|------|------|
| `systeminfo` | 完整系统信息 |
| `hostname` | 主机名 |
| `wmic os get Caption,Version,BuildNumber` | 操作系统版本 |
| `wmic computersystem get Model,Manufacturer` | 计算机型号和制造商 |
| `wmic cpu get Name,NumberOfCores,MaxClockSpeed` | CPU 信息 |
| `wmic memorychip get Capacity,Speed` | 内存信息 |
| `wmic bios get SerialNumber` | 主机序列号 |

### 网络相关

| 命令 | 说明 |
|------|------|
| `ipconfig` | IP 配置 |
| `ipconfig /all` | 详细 IP 配置 |
| `ipconfig /displaydns` | DNS 缓存 |
| `netstat -ano` | 所有网络连接 |
| `netstat -ano \| findstr ESTABLISHED` | 活动连接 |
| `route print` | 路由表 |
| `arp -a` | ARP 缓存 |
| `ping 8.8.8.8` | 网络连通性测试 |
| `tracert www.baidu.com` | 路由追踪 |
| `nslookup www.baidu.com` | DNS 查询 |

### 进程和服务

| 命令 | 说明 |
|------|------|
| `tasklist` | 运行进程列表 |
| `tasklist /v` | 详细进程信息 |
| `tasklist /fo csv` | CSV 格式输出 |
| `tasklist \| findstr chrome.exe` | 查找特定进程 |
| `wmic process where "name='chrome.exe'" get ProcessId,CommandLine` | 进程详细信息 |
| `sc query type= service state= all` | 所有服务状态 |
| `sc query Spooler` | 特定服务状态 |
| `powershell "Get-Process \| Select-Object Name,CPU,WorkingSet -First 10"` | PowerShell 获取进程 |

### 文件和磁盘

| 命令 | 说明 |
|------|------|
| `dir C:\` | 列出目录内容 |
| `dir C:\ /s` | 递归列出所有文件 |
| `wmic logicaldisk get DeviceID,Size,FreeSpace` | 磁盘空间 |
| `fsutil volume diskfree C:` | 磁盘可用空间 |
| `type C:\file.txt` | 查看文件内容 |
| `findstr "keyword" C:\file.txt` | 搜索文件内容 |

### 软件和配置

| 命令 | 说明 |
|------|------|
| `wmic product get Name,Version,Vendor` | 已安装软件列表 |
| `wmic qfe get HotFixID,InstalledOn` | 已安装补丁 |
| `reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"` | 启动项 |
| `type C:\Windows\System32\drivers\etc\hosts` | hosts 文件 |
| `net user` | 用户列表 |
| `net localgroup administrators` | 管理员组成员 |

### 性能监控

| 命令 | 说明 |
|------|------|
| `powershell "Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 3"` | CPU 使用率 |
| `powershell "Get-Counter '\\Memory\\Available MBytes'"` | 可用内存 |
| `powershell "Get-Counter '\\Network Interface(*)\\Bytes Total/sec'"` | 网络流量 |
| `wevtutil qe System /c:10 /rd:true /f:text` | 最近 10 条系统日志 |

### 其他实用命令

| 命令 | 说明 |
|------|------|
| `whoami` | 当前用户 |
| `echo %DATE% %TIME%` | 日期和时间 |
| `schtasks /query /fo LIST` | 任务计划 |
| `driverquery` | 已安装驱动 |
| `powershell "Get-WmiObject Win32_PnPSignedDriver \| Select-Object DeviceName,DriverVersion"` | 驱动版本 |

---

## Linux 系统巡检命令

### 系统信息

| 命令 | 说明 |
|------|------|
| `uname -a` | 系统信息 |
| `hostname` | 主机名 |
| `cat /etc/os-release` | 操作系统版本 |
| `uptime` | 系统运行时间 |
| `cat /proc/cpuinfo` | CPU 信息 |
| `free -h` | 内存使用 |
| `df -h` | 磁盘使用 |

### 网络相关

| 命令 | 说明 |
|------|------|
| `ip addr` | IP 地址 |
| `ip route` | 路由表 |
| `netstat -tuln` | 监听端口 |
| `ss -tuln` | 套接字统计 |
| `ping -c 4 8.8.8.8` | 网络测试 |
| `traceroute www.baidu.com` | 路由追踪 |

### 进程和服务

| 命令 | 说明 |
|------|------|
| `ps aux` | 进程列表 |
| `ps aux \| grep nginx` | 查找进程 |
| `top -b -n 1` | 系统资源快照 |
| `systemctl status nginx` | 服务状态 |
| `systemctl list-units --type=service` | 所有服务 |

### 文件和磁盘

| 命令 | 说明 |
|------|------|
| `ls -la /` | 列出根目录 |
| `du -sh /*` | 各目录大小 |
| `df -h` | 磁盘使用 |
| `fdisk -l` | 磁盘分区 |

### 日志查看

| 命令 | 说明 |
|------|------|
| `journalctl -u nginx -n 50` | 查看服务日志 |
| `tail -100 /var/log/messages` | 系统日志 |
| `dmesg \| tail` | 内核日志 |

---

## 网络设备巡检命令

### 华为设备

| 命令 | 说明 |
|------|------|
| `display version` | 查看版本信息 |
| `display device` | 查看设备信息 |
| `display cpu-usage` | CPU使用率 |
| `display memory-usage` | 内存使用率 |
| `display interface brief` | 接口简要信息 |
| `display ip interface brief` | IP接口信息 |
| `display arp` | ARP表 |
| `display mac-address` | MAC地址表 |
| `display logbuffer` | 日志缓冲区 |
| `display alarm all` | 告警信息 |
| `display environment` | 环境信息（温度、电源等） |
| `display fans` | 风扇状态 |
| `display power` | 电源状态 |

### H3C设备

| 命令 | 说明 |
|------|------|
| `display version` | 查看版本信息 |
| `display device` | 查看设备信息 |
| `display cpu-usage` | CPU使用率 |
| `display memory` | 内存使用率 |
| `display interface brief` | 接口简要信息 |
| `display ip interface brief` | IP接口信息 |
| `display arp` | ARP表 |
| `display mac-address` | MAC地址表 |
| `display diagnostic-information` | 诊断信息 |
| `display environment` | 环境信息 |

### Cisco设备

| 命令 | 说明 |
|------|------|
| `show version` | 查看版本信息 |
| `show inventory` | 硬件清单 |
| `show processes cpu` | CPU使用率 |
| `show memory statistics` | 内存统计 |
| `show ip interface brief` | IP接口简要信息 |
| `show interface status` | 接口状态 |
| `show arp` | ARP表 |
| `show mac address-table` | MAC地址表 |
| `show logging` | 日志信息 |
| `show environment` | 环境信息 |
| `show diagnostic result` | 诊断结果 |

### 锐捷设备

| 命令 | 说明 |
|------|------|
| `show version` | 查看版本信息 |
| `show cpu` | CPU使用率 |
| `show memory` | 内存使用率 |
| `show interface status` | 接口状态 |
| `show ip interface brief` | IP接口信息 |
| `show arp` | ARP表 |
| `show mac-address-table` | MAC地址表 |
| `show logging` | 日志信息 |

---

## 预定义巡检模板

### Windows 服务器健康巡检模板（完整版，含日志）

```json
{
  "template_name": "windows_health_check_full",
  "commands": [
    {"name": "系统信息", "command": "systeminfo", "timeout": 60, "encoding": "gbk"},
    {"name": "磁盘空间", "command": "wmic logicaldisk get DeviceID,Size,FreeSpace,FileSystem", "timeout": 30, "encoding": "gbk"},
    {"name": "内存使用", "command": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value", "timeout": 30, "encoding": "gbk"},
    {"name": "网络连接", "command": "netstat -ano | findstr ESTABLISHED", "timeout": 30, "encoding": "gbk"},
    {"name": "系统日志", "command": "wevtutil qe System /c:20 /rd:true /f:text", "timeout": 60, "encoding": "utf-8"},
    {"name": "安全日志", "command": "wevtutil qe Security /c:10 /rd:true /f:text", "timeout": 60, "encoding": "utf-8"},
    {"name": "应用程序日志", "command": "wevtutil qe Application /c:10 /rd:true /f:text", "timeout": 60, "encoding": "utf-8"}
  ]
}
```

### Linux 服务器健康巡检模板（完整版，含日志）

```json
{
  "template_name": "linux_health_check_full",
  "commands": [
    {"name": "系统信息", "command": "uname -a && cat /etc/os-release", "timeout": 30, "encoding": "utf-8"},
    {"name": "运行时间", "command": "uptime", "timeout": 30, "encoding": "utf-8"},
    {"name": "磁盘使用", "command": "df -h", "timeout": 30, "encoding": "utf-8"},
    {"name": "内存使用", "command": "free -h", "timeout": 30, "encoding": "utf-8"},
    {"name": "网络连接", "command": "ss -tuln", "timeout": 30, "encoding": "utf-8"},
    {"name": "系统日志", "command": "journalctl -p err -n 20 --no-pager", "timeout": 60, "encoding": "utf-8"},
    {"name": "安全日志", "command": "tail -50 /var/log/secure 2>/dev/null | tail -20", "timeout": 30, "encoding": "utf-8"},
    {"name": "系统消息日志", "command": "tail -20 /var/log/messages", "timeout": 30, "encoding": "utf-8"}
  ]
}
```

### 网络设备基础巡检模板

```json
{
  "template_name": "network_device_basic",
  "commands": [
    {"name": "版本信息", "command": "display version"},
    {"name": "CPU使用率", "command": "display cpu-usage"},
    {"name": "内存使用", "command": "display memory-usage"},
    {"name": "接口状态", "command": "display interface brief"},
    {"name": "告警信息", "command": "display alarm all"}
  ]
}
```

---

## 命令执行超时建议

| 命令类型 | 建议超时时间 | 说明 |
|----------|--------------|------|
| 简单查询 | 10-30秒 | hostname, ipconfig, uname 等 |
| 系统信息 | 30-60秒 | systeminfo, ps aux 等 |
| 网络测试 | 30-60秒 | ping, traceroute 等 |
| 日志查询 | 60-120秒 | wevtutil, journalctl 等 |
| 软件列表 | 60-120秒 | wmic product 等（较慢） |
| 批量操作 | 根据数量调整 | 每个客户端增加30秒余量 |

---

## 日志巡检命令详解

### Windows 日志巡检

#### 基本日志查询命令

| 命令 | 说明 | 用途 |
|------|------|------|
| `wevtutil qe System /c:20 /rd:true /f:text` | 系统日志最近20条 | 系统级事件 |
| `wevtutil qe Security /c:10 /rd:true /f:text` | 安全日志最近10条 | 登录、权限变更 |
| `wevtutil qe Application /c:10 /rd:true /f:text` | 应用程序日志最近10条 | 应用错误 |
| `wevtutil qe "Windows PowerShell" /c:10 /rd:true /f:text` | PowerShell日志 | 脚本执行记录 |

#### 按级别筛选日志

```bash
# 错误级别日志 (Level=2)
wevtutil qe System /q:"*[System[(Level=2)]]" /c:10 /rd:true /f:text

# 警告级别日志 (Level=3)
wevtutil qe System /q:"*[System[(Level=3)]]" /c:10 /rd:true /f:text

# 错误和警告 (Level=2或3)
wevtutil qe System /q:"*[System[(Level=2 or Level=3)]]" /c:20 /rd:true /f:text

# 严重错误 (Level=1)
wevtutil qe System /q:"*[System[(Level=1)]]" /c:10 /rd:true /f:text
```

#### 按时间范围筛选

```bash
# 最近1小时
wevtutil qe System /q:"*[System[TimeCreated[timediff(@SystemTime) <= 3600000]]]" /c:50 /rd:true /f:text

# 最近24小时
wevtutil qe System /q:"*[System[TimeCreated[timediff(@SystemTime) <= 86400000]]]" /c:100 /rd:true /f:text

# 最近7天
wevtutil qe System /q:"*[System[TimeCreated[timediff(@SystemTime) <= 604800000]]]" /c:200 /rd:true /f:text
```

#### 按事件ID筛选

```bash
# 登录失败事件 (ID 4625)
wevtutil qe Security /q:"*[System[(EventID=4625)]]" /c:20 /rd:true /f:text

# 服务启动失败 (ID 7000)
wevtutil qe System /q:"*[System[(EventID=7000)]]" /c:20 /rd:true /f:text

# 系统意外关机 (ID 41)
wevtutil qe System /q:"*[System[(EventID=41)]]" /c:10 /rd:true /f:text

# 账户锁定 (ID 4740)
wevtutil qe Security /q:"*[System[(EventID=4740)]]" /c:10 /rd:true /f:text
```

#### PowerShell 方式获取日志

```bash
# 获取系统日志
powershell "Get-EventLog -LogName System -Newest 20 | Format-List TimeGenerated,Source,EventID,EntryType,Message"

# 获取错误日志
powershell "Get-EventLog -LogName System -EntryType Error -Newest 10 | Format-List"

# 使用Get-WinEvent（更高效）
powershell "Get-WinEvent -FilterHashtable @{LogName='System';Level=2,3} -MaxEvents 20 | Format-List TimeCreated,ProviderName,Id,LevelDisplayName,Message"

# 统计日志数量
powershell "Get-EventLog -LogName System -After (Get-Date).AddDays(-1) | Group-Object EntryType | Select-Object Name,Count"
```

### Linux 日志巡检

#### systemd 日志 (journalctl)

| 命令 | 说明 |
|------|------|
| `journalctl -n 20 --no-pager` | 最近20条日志 |
| `journalctl -p err -n 20 --no-pager` | 错误级别日志 |
| `journalctl -p warning -n 20 --no-pager` | 警告级别日志 |
| `journalctl --since today --no-pager` | 今日日志 |
| `journalctl --since "1 hour ago" --no-pager` | 最近1小时 |
| `journalctl --since "2026-02-12" --no-pager` | 指定日期 |
| `journalctl -u nginx -n 20 --no-pager` | nginx服务日志 |
| `journalctl -u sshd -n 20 --no-pager` | SSH服务日志 |
| `journalctl -u docker -n 20 --no-pager` | Docker服务日志 |
| `journalctl -f` | 实时日志（不用于巡检） |

#### 日志级别说明

| 级别 | 值 | 说明 |
|------|------|------|
| emerg | 0 | 紧急：系统不可用 |
| alert | 1 | 警报：必须立即处理 |
| crit | 2 | 严重：严重错误 |
| err | 3 | 错误：错误信息 |
| warning | 4 | 警告：警告信息 |
| notice | 5 | 通知：正常但重要 |
| info | 6 | 信息：一般信息 |
| debug | 7 | 调试：调试信息 |

#### 传统日志文件

| 日志文件 | 说明 | 命令 |
|----------|------|------|
| `/var/log/messages` | 系统消息日志 | `tail -50 /var/log/messages` |
| `/var/log/secure` | 安全日志（RedHat系） | `tail -50 /var/log/secure` |
| `/var/log/auth.log` | 认证日志（Debian系） | `tail -50 /var/log/auth.log` |
| `/var/log/syslog` | 系统日志（Debian系） | `tail -50 /var/log/syslog` |
| `/var/log/cron` | 定时任务日志 | `tail -50 /var/log/cron` |
| `/var/log/boot.log` | 启动日志 | `tail -50 /var/log/boot.log` |
| `/var/log/dmesg` | 内核启动日志 | `dmesg | tail -50` |
| `/var/log/kern.log` | 内核日志 | `tail -50 /var/log/kern.log` |

#### 日志分析命令

```bash
# 查找错误关键词
grep -i "error\|fail\|critical" /var/log/messages | tail -20

# 统计错误数量
grep -c "error" /var/log/messages

# 查找SSH登录失败
grep "Failed password" /var/log/secure | tail -20
grep "Failed password" /var/log/auth.log | tail -20

# 查找sudo使用记录
grep "sudo:" /var/log/secure | tail -20
grep "sudo:" /var/log/auth.log | tail -20

# 查找用户登录记录
last -n 20
lastlog

# 内核错误
dmesg | grep -i "error\|warn\|fail" | tail -20
```

### 网络设备日志巡检

#### 华为/H3C 设备

```
# 查看日志缓冲区
display logbuffer

# 查看告警缓冲区
display alarm-buffer

# 查看最新日志
display logbuffer reverse

# 按模块筛选
display logbuffer module SHELL
display logbuffer module DEV

# 清除日志
reset logbuffer
```

#### Cisco 设备

```
# 查看日志
show logging

# 查看最新日志
show logging | include recent

# 查看特定级别的日志
show logging | include severity

# 查看日志统计
show logging statistics
```

---

## 日志分析要点

### 需要关注的日志事件

#### Windows 关键事件ID

| 事件ID | 说明 | 级别 |
|--------|------|------|
| 4624 | 登录成功 | 信息 |
| 4625 | 登录失败 | 警告 |
| 4634 | 注销成功 | 信息 |
| 4648 | 使用显式凭据登录 | 信息 |
| 4672 | 特殊登录（管理员） | 信息 |
| 4720 | 账户创建 | 警告 |
| 4726 | 账户删除 | 警告 |
| 4732/4733 | 添加/移除本地组成员 | 警告 |
| 4740 | 账户锁定 | 错误 |
| 7000 | 服务启动失败 | 错误 |
| 7001 | 服务启动依赖失败 | 错误 |
| 7031 | 服务意外终止 | 错误 |
| 7045 | 系统中安装了服务 | 警告 |
| 41 | 系统意外关机 | 错误 |
| 1074 | 系统正常关机 | 信息 |

#### Linux 关键日志模式

| 模式 | 说明 | 级别 |
|------|------|------|
| `Failed password` | SSH登录失败 | 警告 |
| `Accepted password` | SSH登录成功 | 信息 |
| `Invalid user` | 无效用户尝试 | 警告 |
| `Connection closed` | 连接关闭 | 信息 |
| `Out of memory` | 内存不足 | 错误 |
| `segfault` | 程序崩溃 | 错误 |
| `I/O error` | 磁盘错误 | 错误 |
| `kernel: BUG` | 内核错误 | 严重 |

### 日志健康评估标准

| 指标 | 健康 | 警告 | 严重 |
|------|------|------|------|
| 错误日志数/天 | <10 | 10-50 | >50 |
| 登录失败数/小时 | <5 | 5-20 | >20 |
| 服务崩溃数/天 | 0 | 1-3 | >3 |
| 磁盘错误数 | 0 | 1-5 | >5 |
