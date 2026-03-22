# Email Gateway - AI安全团队邮件网关

> 为 AI Security Team 的 orchestrator 提供邮件收发能力

## 系统架构

```
┌─────────────────────┐     ┌─────────────────────┐
│  email_service.py   │     │    orchestrator     │
│  (独立运行的服务)    │     │   (Claude Code)     │
│                     │     │                     │
│  持续轮询邮箱        │────▶│  启动时读取队列     │
│  新邮件 → 存入队列   │     │  处理完毕 → 清除    │
└─────────────────────┘     └─────────────────────┘
           │
           ▼
    ┌──────────────────┐
    │ pending_emails   │  ← 待处理邮件队列
    │    .json         │
    └──────────────────┘
```

## 功能特性

- **独立服务**: 后台持续监听邮箱，7x24运行
- **邮件队列**: 新邮件自动存入队列，orchestrator随时读取
- **邮件发送**: 发送HTML/纯文本邮件，支持附件
- **白名单过滤**: 只处理白名单发件人的邮件
- **安全存储**: AES加密存储邮箱授权码
- **日志追加**: 可选将邮件记录追加到指定JSON文件

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行配置向导

```bash
python setup.py
```

按提示完成：
- 输入QQ邮箱地址和授权码
- 设置主密码（用于加密存储）
- 添加白名单发件人
- 设置轮询间隔

### 3. 获取QQ邮箱授权码

1. 登录 QQ邮箱网页版
2. 进入 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
4. 开启 **IMAP/SMTP服务**
5. 生成 **授权码**（不是QQ密码）

### 4. 启动邮件监听服务

**Windows (后台运行，无窗口):**
```cmd
set EMAIL_AUTH_CODE=你的授权码
pythonw email_service.py
```

**Windows (带窗口，调试用):**
```cmd
set EMAIL_AUTH_CODE=你的授权码
python email_service.py
```

**Linux (后台运行):**
```bash
export EMAIL_AUTH_CODE=你的授权码
nohup python email_service.py &
```

**启用日志文件追加（可选）:**
```cmd
python email_service.py --agent "E:\logs\email_log.json"
```

说明：
- `--agent` 参数指定日志文件路径（文件必须已存在）
- 每次轮询发现新邮件后，队列写完后会向该文件追加一条JSON记录
- 如果文件不存在或未指定参数，该功能自动禁用
- 写入失败不影响邮件正常入队

### 5. orchestrator 使用

orchestrator 启动时读取队列：

```python
from email_gateway import EmailGateway
import os

# 初始化
gateway = EmailGateway(master_password=os.getenv("EMAIL_MASTER_PASSWORD"))

# 读取待处理邮件
emails = gateway.get_queued_emails()
for email in emails:
    # 理解邮件内容，执行任务
    print(email.subject, email.body_text)

# 处理完毕，清除队列
gateway.mark_emails_processed([e.email_id for e in emails])
```

## 使用方法

### Python代码中使用

```python
from email_gateway import EmailGateway

# 初始化（需要主密码）
gateway = EmailGateway(master_password="your_master_password")

# ========== 读取邮件队列 ==========

# 获取待处理邮件
emails = gateway.get_queued_emails()
print(f"有 {len(emails)} 封待处理邮件")

# 处理完毕后清除
gateway.mark_emails_processed([email.email_id for email in emails])

# 查看队列数量
count = gateway.get_queue_count()

# ========== 发送邮件 ==========

# 发送普通邮件
gateway.send_email(
    to=["admin@example.com"],
    subject="安全报告",
    content="<h1>日报</h1><p>今日安全状况正常。</p>",
    content_type="html"
)

# 发送给所有管理员
gateway.send_to_admins(
    subject="紧急通知",
    content="发现安全事件！",
    priority="high"
)

# 发送安全事件告警
gateway.send_incident_alert(
    incident_type="DDoS攻击",
    severity="high",
    description="检测到来自多个IP的异常流量",
    details={"source_ips": ["1.2.3.4", "5.6.7.8"], "target": "Web服务器"}
)

# 发送日报
gateway.send_daily_report(
    report_date="2026-02-15",
    summary={"total_events": 5, "incidents": 1},
    events=[{"time": "10:00", "type": "登录失败", "severity": "中"}]
)
```

### 命令行使用

```bash
# 启动邮件监听服务
python email_service.py

# 启用日志文件追加
python email_service.py --agent "E:\logs\email_log.json"

# 只检查一次（不持续运行）
python email_service.py --check-once

# 查看待处理队列
python email_service.py --show-queue

# 清空队列
python email_service.py --clear-queue

# 检查未读邮件
python email_gateway.py --check --password "your_master_password"

# 测试发送
python email_gateway.py --test-send --password "your_master_password"
```

**命令行参数说明：**

| 参数 | 说明 |
|------|------|
| `--agent <path>` | 指定日志文件路径，队列写完后追加JSON记录（文件必须存在） |
| `--check-once` | 只检查一次，不持续运行 |
| `--show-queue` | 显示当前待处理队列 |
| `--clear-queue` | 清空待处理队列 |

## 文件结构

```
email-gateway/
├── email_gateway.py   # 主程序（orchestrator使用）
├── email_service.py   # 独立监听服务（后台运行）
├── config.py          # 配置管理（加密存储）
├── sender.py          # 邮件发送
├── receiver.py        # 邮件接收
├── parser.py          # 邮件信息传递
├── setup.py           # 配置向导
├── requirements.txt   # 依赖
├── README.md          # 本文档
├── config/            # 配置文件目录
│   ├── email_config.json    # 邮箱配置
│   ├── whitelist.json       # 白名单
│   └── pending_emails.json  # 待处理邮件队列
├── logs/              # 日志目录
└── attachments/       # 附件存储
```

## 与 Orchestrator 集成

orchestrator 在启动时：

```python
# orchestrator 启动流程
class Orchestrator:
    def __init__(self):
        self.email_gateway = EmailGateway(
            master_password=os.getenv("EMAIL_MASTER_PASSWORD")
        )

    def startup(self):
        # 1. 从队列读取待处理邮件
        emails = self.email_gateway.get_queued_emails()
        for email in emails:
            self.process_instruction(email.body_text)  # AI理解并执行

        # 2. 处理完毕，清除队列
        self.email_gateway.mark_emails_processed(
            [e.email_id for e in emails]
        )

    def report_to_human(self, title, content):
        # 向人类汇报
        self.email_gateway.send_to_admins(
            subject=title,
            content=content
        )
```

## 安全注意事项

1. **主密码**: 请使用强密码并妥善保管，丢失后无法恢复配置
2. **授权码**: 不是QQ密码，是邮箱设置中生成的专用码
3. **白名单**: 只添加可信的发件人
4. **配置文件**: `config/` 目录包含敏感信息，请勿分享

## 常见问题

**Q: 发送邮件失败?**
A: 检查授权码是否正确，确保开启了SMTP服务

**Q: 收不到邮件?**
A: 检查发件人是否在白名单中，检查IMAP服务是否开启，确认email_service.py是否在运行

**Q: 如何修改配置?**
A: 重新运行 `python setup.py` 或直接编辑 `config/` 目录下的JSON文件

**Q: 邮件服务如何开机自启?**
A: Windows可以使用任务计划程序，Linux可以使用systemd或crontab

**Q: --agent 文件不存在怎么办?**
A: 功能会自动禁用，不会影响邮件正常收发。启动时会输出提示信息："日志文件不存在，功能已禁用: <文件路径>"

**Q: --agent 写入失败会影响邮件吗?**
A: 不会。日志文件写入失败只记录错误日志，邮件仍会正常入队处理

**Q: 每收到一封邮件都会写一条日志吗?**
A: 不是。每次轮询发现新邮件后，队列写完后只写一条日志记录，不管同时收到多少封邮件
