### {device_index}. {hostname} ({client_id})

**基本信息**: {os_info} | IP: {ip_address}

#### 资源使用分析

| 指标 | 值 | 使用率 | 状态 |
|------|------|--------|------|
| 内存 | {total_memory} / {free_memory} | {memory_percent}% | {memory_status} |
| 磁盘 | {disk_summary} | - | {disk_status} |
| 网络 | {connection_count} 连接 | - | {network_status} |

#### 日志分析

| 日志类型 | 错误数 | 警告数 | 状态 |
|----------|--------|--------|------|
{device_log_rows}

#### 健康评分

**评分**: {device_score}/100 - {device_health_level}

#### 问题与建议

{device_issues}
