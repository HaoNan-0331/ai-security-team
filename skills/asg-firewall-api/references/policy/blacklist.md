# 黑名单

## 概述

黑名单模块提供 IP 黑名单和域名黑名单的配置管理功能，支持添加、修改、删除和查询操作。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 新建IP黑名单 | POST | `/api/blacklist` |
| 查询IP黑名单 | GET | `/api/blacklist` |
| 修改IP黑名单 | PUT | `/api/blacklist` |
| 删除IP黑名单 | DELETE | `/api/blacklist` |
| 获取域名黑名单 | GET | `/api/blacklist-domain` |
| 新建域名黑名单 | POST | `/api/blacklist-domain` |
| 修改域名黑名单 | PUT | `/api/blacklist-domain` |
| 删除域名黑名单 | DELETE | `/api/blacklist-domain` |

---

# IP 黑名单

## 新建 IP 黑名单

**端点**: `POST /api/blacklist`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ip_type | Number | 否 | IP类型（1：IPv4，2：IPv6） |
| ip | String | 否 | 源IP |
| age | Number | 是 | 生命周期，值-1代表永久，参数为空代表永久，单位秒 |
| enable | Number | 否 | 是否启用（0：不启用，1：启用） |

**age 参数预设值**:

| 值 | 说明 |
|----|------|
| 300 | 5分钟 |
| 600 | 10分钟 |
| 900 | 15分钟 |
| 1800 | 30分钟 |
| 3600 | 1小时 |
| 7200 | 2小时 |
| 14400 | 4小时 |
| 28800 | 8小时 |
| 86400 | 1天 |
| -1 | 永久 |

**请求示例**:

```json
{
    "ip_type": "1",
    "ip": "1.1.2.2",
    "age": "300",
    "enable": "0"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "-22",
    "str": "非法的IP地址"
}
```

---

## 查询 IP 黑名单

**端点**: `GET /api/blacklist`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ip_type | Number | 否 | IP类型（1：IPv4，2：IPv6） |
| ip | String | 否 | 源IP |
| reason | Number | 否 | 添加原因（-1：所有，0：手工添加，1：端口扫描，2：地址扫描，3：IPS，4：业务自动添加，5：联动功能添加，6：DOS攻击添加，7：防暴力破解） |
| state | Number | 否 | 状态（0：不启用，1：启用，2：所有） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ip | String | IP地址 |
| age | Number | 生命周期 |
| leftTime | String | 剩余生效时间 |
| effectTime | String | 生效时间 |
| reason | Number | 添加原因 |
| state | Number | 状态（0：失效，1：生效） |
| ip_type | Number | IP类型（1：IPv4，2：IPv6） |
| enable | Number | 启用状态（0：不启用，1：启用） |

**响应示例**:

```json
{
    "data": [
        {
            "ip": "1.1.1.1",
            "age": "300",
            "leftTime": "61",
            "effectTime": "2022-08-17 14:05:14",
            "reason": "0",
            "state": "1",
            "enable": "1",
            "ip_type": "1"
        }
    ],
    "total": 1
}
```

---

## 修改 IP 黑名单

**端点**: `PUT /api/blacklist`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| old_ip | String | 修改前IP |  |
| ip | String | 修改后IP |  |
| age | Number | 生命周期 |  |
| enable | Number | 状态（0：不启用，1：启用） |  |
| reason | Number | 添加原因（范围：0-7，下发只允许0，代表手动） |  |
| ip_type | Number | IP类型（1：IPv4，2：IPv6） |  |

**请求示例**:

```json
{
    "old_ip": "1.1.1.100",
    "ip": "1.1.1.110",
    "age": "3600",
    "enable": "1",
    "reason": "0",
    "ip_type": "1"
}
```

---

## 删除 IP 黑名单

**端点**: `DELETE /api/blacklist`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| ip | String | 源IP |  |
| ip_type | Number | IP类型（1：IPv4，2：IPv6） |  |

**请求示例**:

```json
{
    "ip": "1.1.1.1",
    "ip_type": "1"
}
```

---

# 域名黑名单

## 获取域名黑名单

**端点**: `GET /api/blacklist-domain`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| age | Number | 生命周期 |
| bingo | Number | 命中次数 |
| domain | String | 域名 |
| effectTime | String | 生效截止时间 |
| fuzzy_match | Number | 模块开关（1：开启，0：关闭） |
| leftTime | String | 剩余生效时间 |
| state | Number | 状态 |

**响应示例**:

```json
{
    "data": [
        {
            "doamin": "www.xxx.com",
            "age": "300",
            "leftTime": "61",
            "effectTime": "2000-05-11 11:27:02",
            "reason": "0",
            "state": "1"
        },
        {
            "doamin": "www.yyy.com",
            "age": "600",
            "leftTime": "61",
            "effectTime": "2000-05-11 11:27:02",
            "reason": "0",
            "state": "1"
        }
    ]
}
```

---

## 新建域名黑名单

**端点**: `POST /api/blacklist-domain`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| enable | Number | 否 | 配置开关（1：开启，0：关闭） |
| domain | String | 否 | 域名，范围（1-255） |
| fuzzy_match | Number | 否 | 模块开关（1：开启，0：关闭） |
| age | Number | 否 | 生命周期（5min、10min、15min、30min、1h、2h、4h、8h、1day、永久） |

**请求示例**:

```json
{
    "enable": "0",
    "age": "300",
    "domain": "www.tianya.com",
    "fuzzy_match": "0"
}
```

---

## 修改域名黑名单

**端点**: `PUT /api/blacklist-domain`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| age | Number | 否 | 生命周期 |
| enable | Number | 否 | 启用状态（0：不启用，1：启用） |
| domain | String | 否 | 域名，范围（1-255） |
| fuzzy_match | Number | 否 | 模糊匹配开关（1：开启，0：关闭） |
| lefttime | String | 是 | 剩余生效时间 |
| effecttime | String | 是 | 生效截止时间 |
| old_domain | String | 是 | 修改前域名 |
| reason | String | 是 | 添加原因（范围：0-7，0表示手动，其他自动） |
| state | Number | 是 | 状态 |

**请求示例**:

```json
{
    "domain": "www.tianya.com",
    "age": "300",
    "enable": "0",
    "effectTime": "2022-11-02 17:04:09",
    "leftTime": "0",
    "fuzzy_match": "0",
    "state": "0",
    "old_domain": "www.tianya.cn"
}
```

---

## 删除域名黑名单

**端点**: `DELETE /api/blacklist-domain`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| domain | String | 否 | 域名，范围（1-255） |

**请求示例**:

```json
{
    "domain": "www.jd.com"
}
```

---

## 参数说明

### ip_type 参数说明

| 值 | 说明 |
|----|------|
| 1 | IPv4地址 |
| 2 | IPv6地址 |

### reason 参数说明

| 值 | 说明 |
|----|------|
| -1 | 所有 |
| 0 | 手工添加 |
| 1 | 端口扫描 |
| 2 | 地址扫描 |
| 3 | IPS |
| 4 | 业务自动添加 |
| 5 | 由联动功能添加 |
| 6 | DOS攻击添加 |
| 7 | 防暴力破解 |

### state 参数说明

| 值 | 说明 |
|----|------|
| 0 | 失效/不启用 |
| 1 | 生效/启用 |
| 2 | 所有 |
