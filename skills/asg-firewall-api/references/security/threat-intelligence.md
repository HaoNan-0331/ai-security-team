# 威胁情报

## 概述

威胁情报模块提供情报策略管理、云端情报联动和自定义威胁情报的配置功能。

## API 端点汇总

| 功能 | 方法 | 端点 |
|------|------|------|
| **情报策略** | 获取情报策略使能状态 | GET | `/api/ecd-item` |
| **情报策略** | 修改情报策略使能状态 | PUT | `/api/ecd-item` |
| **情报策略** | 获取威胁情报信誉值 | GET | `/api/reliable-config` |
| **情报策略** | 修改威胁情报信誉值 | PUT | `/api/reliable-config` |
| **情报策略** | 获取威胁情报风险级别的日志级别配置 | GET | `/api/intelligence-level` |
| **情报策略** | 修改威胁情报风险级别的日志级别配置 | PUT | `/api/intelligence-level` |
| **云端联动** | 获取云端情报联动配置 | GET | `/api/coo-def-cloud` |
| **云端联动** | 获取与云端威胁情报中心连接状态 | GET | `/api/check-online` |
| **云端联动** | 获取云端威胁情报情报库升级历史 | GET | `/api/intelligence-database` |
| **云端联动** | 获取云端威胁情报情报库情况 | GET | `/api/check-update` |
| **云端联动** | 获取云端威胁情报最近一次升级时间 | GET | `/api/ioc-lasttime` |
| **自定义情报** | 获取自定义威胁情报列表 | GET | `/api/defense` |
| **自定义情报** | 新建自定义威胁情报策略 | POST | `/api/defense` |
| **自定义情报** | 修改自定义威胁情报策略 | PUT | `/api/defense` |
| **自定义情报** | 删除自定义威胁情报策略 | DELETE | `/api/defense` |

---

# 情报策略

## 获取情报策略使能状态

**端点**: `GET /api/ecd-item`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ecd_sw_coo_def_ip | Number | IP信誉库开关（0：关，1：开） |
| ecd_sw_coo_def_domain | Number | 域名开关（0：关，1：开） |
| ecd_sw_coo_def_uri | Number | URL开关（0：关，1：开） |
| ecd_sw_coo_def_malware_url | Number | 本地情报库（已屏蔽） |
| ecd_sw_coo_def_sha256 | Number | 文件hash开关（0：关，1：开） |

**响应示例**:

```json
{
    "data": [
        {
            "ecd_sw_coo_def_ip": "0",
            "ecd_sw_coo_def_domain": "0",
            "ecd_sw_coo_def_uri": "0",
            "ecd_sw_coo_def_malware_url": "1",
            "ecd_sw_coo_def_sha256": "0"
        }
    ]
}
```

---

## 修改情报策略使能状态

**端点**: `PUT /api/ecd-item`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ecd_sw_coo_def_ip | Number | 否 | IP信誉库开关（0：关，1：开） |
| ecd_sw_coo_def_domain | Number | 否 | 域名开关（0：关，1：开） |
| ecd_sw_coo_def_uri | Number | 否 | URL开关（0：关，1：开） |
| ecd_sw_coo_def_sha256 | Number | 否 | 文件hash开关（0：关，1：开） |

**请求示例**:

```json
{
    "ecd_sw_coo_def_ip": "0",
    "ecd_sw_coo_def_domain": "1",
    "ecd_sw_coo_def_uri": "1",
    "ecd_sw_coo_def_sha256": "1"
}
```

---

## 获取威胁情报信誉值

**端点**: `GET /api/reliable-config`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| logenable | Number | 记录日志开关（0：关，1：开） |
| logreliable | Number | 记录日志信誉值（1-100） |
| log_risklevel | Number | 记录日志对应风险级别（-1：未知，0：安全，1：可疑，2：低，3：中，4：高，5：严重） |
| denyenable | Number | 拒绝并记录日志开关（0：关，1：开） |
| denyreliable | Number | 拒绝并记录日志信誉值（1-100） |
| deny_risklevel | Number | 拒绝并记录日志对应风险级别 |

**响应示例**:

```json
{
    "data": [
        {
            "logenable": "0",
            "logreliable": "35",
            "log_risklevel": "1",
            "denyenable": "0",
            "denyreliable": "80",
            "deny_risklevel": "4"
        }
    ],
    "total": 1
}
```

---

## 修改威胁情报信誉值

**端点**: `PUT /api/reliable-config`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| logenable | Number | 是 | 记录日志开关（0：关，1：开，默认为0） |
| logreliable | Number | 否 | 记录日志信誉值（1-100） |
| log_risklevel | Number | 是 | 记录日志对应风险级别（-1：未知，0：安全，1：可疑，2：低，3：中，4：高，5：严重，默认为-1） |
| denyenable | Number | 是 | 拒绝并记录日志开关（0：关，1：开，默认为0） |
| denyreliable | Number | 否 | 拒绝并记录日志信誉值（1-100），必须大于记录日志信誉值 |
| deny_risklevel | Number | 是 | 拒绝并记录日志对应风险级别（-1：未知，0：安全，1：可疑，2：低，3：中，4：高，5：严重，默认为-1） |

**请求示例**:

```json
{
    "logenable": "1",
    "logreliable": "30",
    "log_risklevel": "1",
    "denyenable": "1",
    "denyreliable": "88",
    "deny_risklevel": "4"
}
```

---

## 获取威胁情报风险级别的日志级别配置

**端点**: `GET /api/intelligence-level`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| levelserious | Number | 日志级别严重（0紧急，1告警，2严重，3错误，4警示，5通知，6信息） |
| levelhigh | Number | 日志级别高 |
| levelmid | Number | 日志级别中 |
| levellow | Number | 日志级别低 |
| leveldoubt | Number | 日志级别可疑 |
| levelsafe | Number | 日志级别安全 |
| levelunknown | Number | 日志级别未知 |

**响应示例**:

```json
{
    "data": [
        {
            "levelserious": "0",
            "levelhigh": "1",
            "levelmid": "2",
            "levellow": "3",
            "leveldoubt": "4",
            "levelsafe": "5",
            "levelunknown": "6"
        }
    ],
    "total": 1
}
```

---

## 修改威胁情报对应风险等级的日志级别配置

**端点**: `PUT /api/intelligence-level`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| levelserious | Number | 否 | 日志级别严重（0紧急，1告警，2严重，3错误，4警示，5通知，6信息） |
| levelhigh | Number | 否 | 日志级别高 |
| levelmid | Number | 否 | 日志级别中 |
| levellow | Number | 否 | 日志级别低 |
| leveldoubt | Number | 否 | 日志级别可疑 |
| levelsafe | Number | 否 | 日志级别安全 |
| levelunknown | Number | 否 | 日志级别未知 |

**请求示例**:

```json
{
    "levelserious": "0",
    "levelhigh": "0",
    "levelmid": "2",
    "levellow": "3",
    "leveldoubt": "4",
    "levelsafe": "5",
    "levelunknown": "6"
}
```

---

# 云端情报联动

## 获取云端情报联动配置

**端点**: `GET /api/coo-def-cloud`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| server | String | 服务器URL（字符数1-256） |
| enable | Number | 是否开启云端联动（0：关闭，1：开启） |
| auto_update | Number | 定期升级（0：关闭，10-1440：开启且定时为XX分钟） |
| update_license_day | Number | 威胁情报许可（0：无许可，1：有许可） |
| ioc_lib_version | String | 情报版本（回显内容） |
| ioc_agent_lib_version | String | 代理agent情报版本（回显内容） |

**响应示例**:

```json
{
    "data": [
        {
            "server": "https://tip.sec-inside.com",
            "enable": "1",
            "auto_update": "60",
            "update_license_day": "1",
            "ioc_lib_version": "20220420.1002",
            "ioc_agent_lib_version": "20220420.1002"
        }
    ],
    "total": 1
}
```

---

## 获取与云端威胁情报中心连接状态

**端点**: `GET /api/check-online`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | Number | 错误码 |
| last_updatetime | String | 上次升级时间 |
| message | String | 状态信息 |

**响应示例**:

```json
{
    "code": 0,
    "last_updatetime": "2022-04-20 10:02:24",
    "message": "Online"
}
```

---

## 获取云端威胁情报情报库升级历史

**端点**: `GET /api/intelligence-database`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| Id | Number | 历史索引 |
| Verrname | String | 拉取版本 |
| Time | String | 拉取时间 |
| Type | String | 拉取类型 |
| Mode | String | 情报拉取方式（自动/手动） |
| Result | String | 拉取结果（成功/失败） |

**响应示例**:

```json
{
    "data": [
        {
            "Id": 0,
            "Vername": "20220420.1002",
            "Time": "2022-04-20 11:07:45",
            "Type": "ioc",
            "Mode": "Auto",
            "Result": "Success"
        }
    ]
}
```

---

## 获取云端威胁情报情报库情况

**端点**: `GET /api/check-update`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | Number | 错误码 |
| cur_version | String | 当前情报库版本 |
| ioc_total | Number | 设备生效情报数 |
| message | String | 信息 |
| new_version | String | 云端新版本 |

**响应示例**:

```json
{
    "code": "0",
    "cur_version": "20220420.1002",
    "ioc_total": 400000,
    "message": "",
    "new_version": "20220420.1002"
}
```

---

## 获取云端威胁情报最近一次升级时间

**端点**: `GET /api/ioc-lasttime`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | Number | 错误码 |
| lasttime | String | 最近一次升级时间 |

**响应示例**:

```json
{
    "code": 0,
    "lastuptime": "2022-04-20 10:02:24"
}
```

---

# 自定义威胁情报

## 获取自定义威胁情报列表

**端点**: `GET /api/defense`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 否 | 语言（cn：中文，en：英文） |
| source | String | 否 | 数据源，必填，填写local_coo_def |
| page | Number | 是 | 当前页数，缺省为1 |
| pageSize | Number | 是 | 页码，缺省为10000000 |
| type | Number | 是 | 类型（0：所有，1：出站IP，2：入站IP，3：DNS域名，4：HTTP URL，5：文件sha256） |
| object | String | 是 | 内容，具体类型格式根据type字段控制 |
| level | Number | 是 | 风险等级（-2：所有，-1：未知，0：安全，1：可疑，2：低，3：中，4：高，5：严重） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| type | Number | 类型（1：出站IP，2：入站IP，3：DNS域名，4：HTTP URL，5：文件sha256） |
| time | Number | 剩余时间，以秒为基础单位 |
| reliable | Number | 信誉值 |
| object | String | 内容 |
| level | Number | 风险级别 |
| buildtime | String | 生效时间，格式为时间戳格式 |
| des | String | 详情 |

**响应示例**:

```json
{
    "data": [{
        "type": "5",
        "level": "1",
        "reliable": "100",
        "time": "52568",
        "buildtime": "1682236271",
        "object": "be2139d41fb3e49530cca7722a07f0112830c4968f728fb2cdfb6f92ceef0c73",
        "des": "desc",
        "source": "local_coo_def"
    }],
    "total": 1
}
```

---

## 新建自定义威胁情报策略

**端点**: `POST /api/defense`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | Number | 否 | 类型（1：出站IP，2：入站IP，3：DNS域名，4：HTTP URL，5：文件sha256） |
| object | String | 否 | 内容，具体类型格式根据type字段控制 |
| reliable | Number | 否 | 信誉值，可配范围为1-100 |
| time | Number | 是 | 生效时间，单位为秒，可配范围为0-59940，0代表永久，缺省为0 |
| level | Number | 是 | 风险级别（-1：未知，0：安全，1：可疑，2：低，3：中，4：高，5：严重，缺省为-1） |
| des | Number | 是 | 描述 |
| source | String | 否 | 数据来源，必填，自定义威胁情报填写local_coo_def |

**请求示例**:

```json
{
    "type": 1,
    "object": "5.5.5.5",
    "reliable": 80,
    "time": 59940,
    "level": 5,
    "des": "",
    "source": "local_coo_def"
}
```

---

## 修改自定义威胁情报策略

**端点**: `PUT /api/defense`

**请求参数**: 同新建自定义威胁情报策略

---

## 删除自定义威胁情报策略

**端点**: `DELETE /api/defense`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | Number | 否 | 类型 |
| object | String | 否 | 内容 |
| source | String | 否 | 数据来源，必填，填写local_coo_def |

**请求示例**:

```json
{
    "type": 1,
    "object": "5.5.5.5",
    "source": "local_coo_def"
}
```

---

## 参数说明

### type 参数说明

| 值 | 说明 |
|----|------|
| 0 | 所有 |
| 1 | 出站IP |
| 2 | 入站IP |
| 3 | DNS域名 |
| 4 | HTTP URL |
| 5 | 文件sha256 |

### level 参数说明

| 值 | 说明 |
|----|------|
| -2 | 所有 |
| -1 | 未知 |
| 0 | 安全 |
| 1 | 可疑 |
| 2 | 低 |
| 3 | 中 |
| 4 | 高 |
| 5 | 严重 |

### log_risklevel 参数说明

| 值 | 说明 |
|----|------|
| -1 | 未知 |
| 0 | 安全 |
| 1 | 可疑 |
| 2 | 低 |
| 3 | 中 |
| 4 | 高 |
| 5 | 严重 |
