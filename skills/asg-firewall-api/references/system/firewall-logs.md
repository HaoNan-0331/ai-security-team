# 防火墙日志

## 概述

防火墙日志模块提供防火墙日志的查询和导出功能。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **防火墙日志** | 查询防火墙日志(时间轴) | GET | `/api/audit-timeline` |
| **防火墙日志** | 查询防火墙日志 | GET | `/api/audit-log` |
| **防火墙日志** | 防火墙日志导出 | GET | `/api/audit-log` |

---

# 防火墙日志查询

## 查询防火墙日志(时间轴)

**端点**: `GET /api/audit-timeline`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 是 | 页数 |
| pageSize | Number | 是 | 每页展示条数 |
| module | String | 是 | 日志类型，防火墙日志为filter |
| sid | Number | 是 | 自定义查询id |
| Time_type | String | 否 | 查询时间类型（cur_day：当天；cur_week：本周；cur_month：本月；one_day：最近24小时；one_week：最近7天；one_month：最近30天；three_month：最近90天；user_def：自定义） |
| start_time | String | 否 | 查询时间类型为自定义时的起始时间 |
| end_time | String | 否 | 查询时间类型为自定义时的结束时间 |
| srcip | String | 否 | 源IP |
| dstip | String | 否 | 目的IP |
| srcport | String | 否 | 源端口 |
| dstport | String | 否 | 目的端口 |
| fwpolicyid | String | 否 | 一体化策略id |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| total_count | Number | 总计数 |
| availa_cout | Number | 有效计数 |
| is_finalized | String | 是否是最后一条记录 |
| duration | Number | 查询时间差 |
| earliest_strftime | String | 起始时间 |
| earliest_time | Number | 起始时间戳 |
| earliest_time_offset | Number | 起始时间时区位移 |
| latest_time_offset | Number | 结束时间时区位移 |
| cross_day | Number | 是否跨天查询（0：不跨天，1：跨天） |
| cursor_time | Number | 出接口 |
| event_count | Number | 日志事件计数 |
| is_time_cursored | Boolean | 分隔节点状态值 |

**响应示例**:

```json
{
    "buckets": [
        {
            "available_count": 136,
            "duration": 1800,
            "earliest_strftime": "2023-04-11T00:00:00+08:00",
            "earliest_time": 1681142400,
            "earliest_time_offset": 28800,
            "is_finalized": true,
            "latest_time_offset": 28800,
            "total_count": 136
        }
    ],
    "cross_day": 0,
    "cursor_time": 1681142400,
    "event_count": 4515,
    "is_time_cursored": true
}
```

---

## 查询防火墙日志

**端点**: `GET /api/audit-log`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 是 | 页数 |
| pageSize | Number | 是 | 每页展示条数 |
| module | String | 是 | 日志类型，防火墙日志为filter |
| sid | Number | 是 | 自定义查询id |
| Time_type | String | 否 | 查询时间类型 |
| start_time | String | 否 | 查询时间类型为自定义时的起始时间 |
| end_time | String | 否 | 查询时间类型为自定义时的结束时间 |
| srcip | String | 否 | 源IP |
| dstip | String | 否 | 目的IP |
| srcport | String | 否 | 源端口 |
| dstport | String | 否 | 目的端口 |
| fwpolicyid | String | 否 | 一体化策略id |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | String | 日志id |
| action | String | 动作 |
| content | String | 日志内容 |
| create_at | String | 时间 |
| dstip | String | 目的IP |
| dstport | String | 目的端口 |
| fwpolicyid | String | 一体化策略ID |
| ininterface | String | 入接口 |
| level | String | 日志级别 |
| outinterface | String | 出接口 |
| protocol | String | 协议 |
| srcip | String | 源IP |
| srcport | String | 源端口 |

**响应示例**:

```json
{
    "data": [
        {
            "id": "4379",
            "srcip": "12.12.12.12",
            "dstip": "47.115.157.107",
            "protocol": "UDP",
            "srcport": "63345",
            "dstport": "8700",
            "ininterface": "ge0/2",
            "outinterface": "ge0/0",
            "fwpolicyid": "1",
            "action": "PERMIT",
            "content": "POLICY*: The packet was through because the firewall policy is permit",
            "level": "6",
            "create_at": "2023-04-11 15:08:24"
        }
    ],
    "total": 4379
}
```

不存在返回空：

```json
{
    "data": [],
    "total": 0
}
```

---

## 防火墙日志导出

**端点**: `GET /api/audit-log`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Lang | String | 否 | 导出语言 |
| download | Number | 否 | 下载（必填1） |
| num | Number | 否 | 导出数量（1：当前页；5000：前5000条） |
| type | String | 否 | 导出文件类型（CSV；TXT；XML） |
| page | Number | 否 | 页数 |
| pageSize | Number | 否 | 每页展示条数 |
| module | String | 否 | 日志类型，防火墙日志为filter |
| start_time | String | 否 | 查询时间类型为自定义时的起始时间，若无，该值填空 |
| end_time | String | 否 | 查询时间类型为自定义时的结束时间，若无，该值填空 |
| srcip | String | 否 | 源IP |
| dstip | String | 否 | 目的IP |
| srcport | String | 否 | 源端口 |
| dstport | String | 否 | 目的端口 |
| fwpolicyid | String | 否 | 一体化策略id |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| str | String | 处理结果 |
| code | Number | 处理结果 |

**响应示例**: 下发正确返回文件内容

---

## 参数说明

### Time_type 参数说明

| 值 | 说明 |
|----|------|
| cur_day | 当天 |
| cur_week | 本周 |
| cur_month | 本月 |
| one_day | 最近24小时 |
| one_week | 最近7天 |
| one_month | 最近30天 |
| three_month | 最近90天 |
| user_def | 自定义 |

### type 参数说明

| 值 | 说明 |
|----|------|
| CSV | CSV格式 |
| TXT | TXT格式 |
| XML | XML格式 |

### num 参数说明

| 值 | 说明 |
|----|------|
| 1 | 当前页 |
| 5000 | 前5000条 |
