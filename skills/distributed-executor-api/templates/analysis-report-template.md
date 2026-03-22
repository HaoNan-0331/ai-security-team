# 系统健康巡检分析报告

**巡检批次**: {batch_id}
**巡检时间**: {inspection_time}
**设备数量**: {device_count}
**成功率**: {success_rate}

---

## 一、批次执行概要

| 项目 | 值 |
|------|------|
| 批次ID | {batch_id} |
| 巡检时间 | {start_time} ~ {end_time} |
| 设备数量 | {device_count} |
| 成功数量 | {success_count} |
| 失败数量 | {fail_count} |
| 总任务数 | {total_tasks} |
| 总耗时 | 约 {duration} 秒 |

---

## 二、设备健康概览

| 序号 | 主机名 | 操作系统 | 健康评分 | 状态 |
|------|--------|----------|----------|------|
{device_overview_rows}

---

{device_analysis_sections}

---

## 三、批次问题汇总

### 🔴 严重问题

| 设备 | 问题 | 影响 | 建议 |
|------|------|------|------|
{critical_issues_rows}

### ⚠️ 警告事项

| 设备 | 问题 | 影响 | 建议 |
|------|------|------|------|
{warning_issues_rows}

### ✅ 正常状态设备

{normal_devices_list}

---

## 四、批次健康评分

| 维度 | 平均评分 | 说明 |
|------|----------|------|
| CPU | {avg_cpu_score}/100 | {cpu_score_desc} |
| 内存 | {avg_memory_score}/100 | {memory_score_desc} |
| 磁盘 | {avg_disk_score}/100 | {disk_score_desc} |
| 网络 | {avg_network_score}/100 | {network_score_desc} |
| 日志 | {avg_log_score}/100 | {log_score_desc} |
| **总平均分** | **{avg_total_score}/100** | **{overall_health}** |

---

**报告生成时间**: {report_time}
**报告文件**: 批次巡检分析报告
