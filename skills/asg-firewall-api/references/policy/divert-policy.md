# 引流策略

## 概述

引流策略模块提供流量引流功能的配置管理，包括新建、修改、查询、删除、清除命中数和移动引流策略。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **引流策略** | 新建引流策略 | POST | `/api/divert-policy` |
| **引流策略** | 修改引流策略 | PUT | `/api/divert-policy` |
| **引流策略** | 查询引流策略 | GET | `/api/divert-policy` |
| **引流策略** | 删除引流策略 | DELETE | `/api/divert-policy` |
| **引流策略** | 清除引流策略命中数 | PUT | `/api/divert-policy` |
| **引流策略** | 移动引流策略 | PUT | `/api/divert-policy` |

---

# 引流策略

## 新建引流策略

**端点**: `POST /api/divert-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | 策略ID |
| enable | Number | 否 | 是否启用（0：不启用，1：启用） |
| if_in | String | 否 | 入接口，默认为any |
| sip | String | 否 | 源地址对象，默认为any |
| dip | String | 否 | 目的地址对象，默认为any |
| sev | String | 否 | 服务对象，默认为any |
| tr | String | 否 | 时间对象，默认为any |
| divert_tunnel | String | 否 | 引流隧道 |
| linkage_tunnel | String | 是 | 关联隧道 |
| syslog | Number | 否 | 日志开关（0：关闭，1：开启） |
| Refer_id | Number | 是 | 目标位置策略Id |
| Protection_enable | Number | 是 | 安全防护功能是否启用（0：不启用，1：启用） |
| Vrf_name | String | 是 | vrf名称 |
| count | Number | 是 | 数量，默认值是-1 |
| app | String | 是 | 应用 |

**请求示例**:

```json
{
    "if_in": "ge0/0",
    "enable": "1",
    "id": "0",
    "linkage_tunnel": "tunl2",
    "syslog": "1",
    "divert_tunnel": "tunl0",
    "sip": "src-addr",
    "dip": "dst",
    "sev": "ah",
    "tr": "always"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "250",
    "str": "参数错误"
}
```

---

## 修改引流策略

**端点**: `PUT /api/divert-policy`

**请求参数**: 同新建引流策略，增加以下参数：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| bingo | Number | 是 | 命中数 |

**请求示例**:

```json
{
    "id": "1",
    "enable": "1",
    "if_in": "ge0/0",
    "sip": "src-addr",
    "dip": "dst",
    "sev": "ah",
    "tr": "always",
    "divert_tunnel": "tunl0",
    "linkage_tunnel": "tunl1",
    "bingo": "0",
    "syslog": "0"
}
```

**响应示例**: 同新建引流策略

---

## 查询引流策略

**端点**: `GET /api/divert-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 是 | 当前页数 |
| pageSize | Number | 是 | 页码 |
| lang | String | 是 | 语言（cn：中文，en：英文） |
| api_key | String | 是 | 接口的api |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | Number | 策略ID |
| enable | Number | 是否启用（0：不启用，1：启用） |
| if_in | String | 入接口，默认为any |
| sip | String | 源地址对象，默认为any |
| dip | String | 目的地址对象，默认为any |
| sev | String | 服务对象，默认为any |
| tr | String | 时间对象，默认为any |
| divert_tunnel | String | 引流隧道 |
| linkage_tunnel | String | 关联隧道 |
| syslog | Number | 日志开关（0：关闭，1：开启） |
| bingo | Number | 命中数 |

**响应示例**:

```json
{
    "data": [
        {
            "id": "1",
            "enable": "1",
            "if_in": "ge0/0",
            "sip": "src-addr",
            "dip": "dst",
            "sev": "ah",
            "tr": "always",
            "divert_tunnel": "tunl0",
            "linkage_tunnel": "tunl2",
            "bingo": "0",
            "syslog": "0"
        }
    ],
    "total": 1
}
```

---

## 删除引流策略

**端点**: `DELETE /api/divert-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID |

**请求示例**:

```json
{
    "id": "1"
}
```

**响应示例**: 同新建引流策略

---

## 清除引流策略命中数

**端点**: `PUT /api/divert-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID |

**请求示例**:

```json
{
    "id": "1"
}
```

**响应示例**: 同新建引流策略

---

## 移动引流策略

**端点**: `PUT /api/divert-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID |
| mv_opt | Number | 是 | 目标位置（1：策略ID之前，2：策略ID之后） |
| refer_id | Number | 是 | 目标位置策略ID |

**请求示例**:

```json
{
    "id": "2",
    "mv_opt": "1",
    "refer_id": "1"
}
```

**响应示例**: 同新建引流策略

---

## 参数说明

### enable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 不启用 |
| 1 | 启用 |

### syslog 参数说明

| 值 | 说明 |
|----|------|
| 0 | 关闭 |
| 1 | 开启 |

### mv_opt 参数说明

| 值 | 说明 |
|----|------|
| 1 | 策略ID之前 |
| 2 | 策略ID之后 |

### Protection_enable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 不启用 |
| 1 | 启用 |
