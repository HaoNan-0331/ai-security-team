# 一体化策略

## 概述

一体化策略模块提供防火墙策略的完整管理功能，包括添加、修改、删除、查询、启用/禁用和移动策略。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 添加一体化策略 | POST | `/api/policy` |
| 修改一体化策略 | PUT | `/api/policy` |
| 获取一体化策略 | GET | `/api/policy` |
| 删除一体化策略 | DELETE | `/api/policy` |
| 修改一体化策略启用禁用状态 | PUT | `/api/policy-state` |
| 移动一体化策略 | PUT | `/api/policy` |

---

## 添加一体化策略

**端点**: `POST /api/policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID（范围：1-10000） |
| protocol | Number | 否 | 协议类型，1表示IPv4，2表示IPv6 |
| if_in | String | 否 | 入接口 |
| if_out | String | 否 | 出接口 |
| sip | String | 否 | 源地址 |
| dip | String | 否 | 目的地址 |
| sev | String | 否 | 服务名称 |
| user | String | 否 | 用户名称 |
| app | String | 否 | 应用名称 |
| tr | String | 否 | 时间表 |
| mode | Number | 否 | 动作（1：PERMIT，2：DENY） |
| enable | Number | 是 | 策略是否启用（0：不启用，1：启用） |
| bingo | Number | 是 | 策略被命中的次数 |
| syslog | Number | 是 | 是否开启日志（0：不启用，1：启用） |
| log_level | Number | 是 | 日志级别（0：紧急，1：告警，2：严重，3：错误，4：警示，5：通知，6：信息） |
| refer_id | Number | 否 | 相关策略ID（用于插入/移动策略） |
| mv_opt | Number | 是 | 移动选项（0：移动到指定策略之前，1：移动到指定策略之后） |
| desc | String | 是 | 描述 |
| mirror_dev | String | 是 | 流镜像接口名称（未使用） |
| flowstat | Number | 是 | 流量统计功能（0：不启用，1：启用） |
| protection_enable | Number | 是 | 安全防护功能（0：不启用，1：启用，暂时保留） |
| protection_module | String | 是 | 安全防护模块（暂时保留） |
| conn_slimit | Number | 是 | 源主机连接限制（范围：0-10000000，0为不限速） |
| conn_rate_slimit | Number | 是 | 源主机连接速率限制（范围：0-10000000，0为不限速） |
| conn_dlimit | Number | 是 | 目的主机连接限制（范围：0-10000000，0为不限速） |
| conn_rate_dlimit | Number | 是 | 目的主机连接速率限制（范围：0-10000000，0为不限速） |
| https_audit | Number | 是 | HTTPS解密（0：禁用，1：启用） |
| appac | String | 是 | 应用防护模板名称 |
| ips | String | 是 | IPS防护模板名称 |
| av | String | 是 | 病毒防护模板名称 |
| webac | String | 是 | Web控制模板名称 |

**请求示例**:

```json
{
    "id": "2",
    "protocol": "1",
    "if_in": "any",
    "if_out": "any",
    "sip": "test",
    "dip": "any",
    "sev": "any",
    "user": "any",
    "app": "any",
    "tr": "always",
    "mode": "1",
    "enable": "1",
    "bingo": "1",
    "syslog": "1",
    "log_level": "6",
    "refer_id": "1",
    "mv_opt": "1",
    "desc": "vvv",
    "mirror_dev": "null",
    "flowstat": "1",
    "protection_enable": "1",
    "protection_module": "",
    "conn_slimit": "10",
    "conn_rate_slimit": "10",
    "conn_dlimit": "10",
    "conn_rate_dlimit": "10",
    "https_audit": "1",
    "appac": "qq",
    "ips": "ips",
    "av": "av",
    "webac": "web访问审计"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "90",
    "str": "出接口或入接口不存在"
}
```

---

## 修改一体化策略

**端点**: `PUT /api/policy`

**请求参数**: 同添加一体化策略

**请求示例**:

```json
{
    "id": "2",
    "protocol": "1",
    "if_in": "any",
    "if_out": "ge0/3",
    "sip": "test",
    "dip": "test1",
    "sev": "ah",
    "user": "any",
    "app": "any",
    "tr": "always",
    "mode": "1",
    "enable": "1",
    "syslog": "1",
    "log_level": "3"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "926",
    "str": "web访问控制模板不存在"
}
```

---

## 修改一体化策略启用禁用状态

**端点**: `PUT /api/policy-state`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | 策略ID（默认为-1） |
| protocol | Number | 是 | 协议类型，1表示IPv4，2表示IPv6 |
| enable | Number | 否 | 是否启用策略（0：不启用，1：启用） |

**请求示例**:

```json
{
    "id": "1",
    "protocol": "1",
    "enable": "0"
}
```

**响应示例**:

```json
{
    "code": "87",
    "str": "目标策略不存在"
}
```

---

## 移动一体化策略

**端点**: `PUT /api/policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID |
| protocol | Number | 是 | 协议类型，1表示IPv4，2表示IPv6 |
| mode | Number | 否 | 动作（1：PERMIT，2：DENY） |
| enable | Number | 是 | 策略是否启用（0：不启用，1：启用） |
| syslog | Number | 是 | 是否开启日志（0：不启用，1：启用） |
| refer_id | Number | 否 | 相关策略ID |
| mv_opt | Number | 是 | 移动选项（0：移动到指定策略之前，1：移动到指定策略之后） |

**请求示例**:

```json
{
    "id": "1",
    "protocol": "2",
    "mode": "1",
    "enable": "1",
    "syslog": "1",
    "refer_id": "2",
    "mv_opt": "1"
}
```

**响应示例**:

```json
{
    "code": "88",
    "str": "参考策略不存在"
}
```

---

## 获取一体化策略

**端点**: `GET /api/policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| protocol | Number | 是 | 协议类型，1表示IPv4，2表示IPv6 |
| vrf | String | 是 | VRF实例名称（如：vrf0） |
| page | Number | 是 | 页码 |
| pageSize | Number | 是 | 每页条数 |
| api_key | String | 是 | 认证Token |
| lang | String | 否 | 语言，cn中文或en英文 |

**请求示例**:

```
GET /api/policy?protocol=1&vrf=vrf0&page=1&pageSize=10&api_key=zsv2krok3bgdwu9jgauo28bqklnfyswh
```

**响应参数**: 同添加一体化策略请求参数

**响应示例**:

```json
{
    "data": [
        {
            "id": "2",
            "protocol": "1",
            "if_in": "any",
            "if_out": "ge0/3",
            "sip": "any",
            "dip": "test1",
            "sev": "aol",
            "user": "test",
            "user_show": "test",
            "app": "msn",
            "app_show": "msn",
            "tr": "time",
            "appac": "qq",
            "webac": "web访问审计",
            "ips": "ips",
            "av": "av",
            "https_audit": "1",
            "mode": "1",
            "flowstat": "1",
            "enable": "0",
            "bingo": "0",
            "syslog": "1",
            "log_level": "6",
            "refer_id": "0",
            "mv_opt": "0",
            "desc": ""
        }
    ],
    "total": 1
}
```

---

## 删除一体化策略

**端点**: `DELETE /api/policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | 策略ID |
| protocol | Number | 是 | 协议类型，1表示IPv4，2表示IPv6 |

**请求示例**:

```json
{
    "id": "2",
    "protocol": "1"
}
```

**响应示例**:

```json
{
    "code": "87",
    "str": "Taget policy doesn't exist"
}
```

---

## 参数说明

### protocol 参数说明

| 值 | 说明 |
|----|------|
| 1 | IPv4协议 |
| 2 | IPv6协议 |

### mode 参数说明

| 值 | 说明 |
|----|------|
| 1 | PERMIT（允许） |
| 2 | DENY（拒绝） |

### enable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 禁用策略 |
| 1 | 启用策略 |

### mv_opt 参数说明

| 值 | 说明 |
|----|------|
| 0 | 移动到指定策略之前 |
| 1 | 移动到指定策略之后 |

### log_level 参数说明

| 值 | 说明 |
|----|------|
| 0 | 紧急 |
| 1 | 告警 |
| 2 | 严重 |
| 3 | 错误 |
| 4 | 警示 |
| 5 | 通知 |
| 6 | 信息 |
