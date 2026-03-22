# 静态路由配置

## 概述

静态路由模块提供 IPv4 和 IPv6 静态路由的配置管理功能。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 新建IPv4静态路由 | POST | `/api/route-static` |
| 修改IPv4静态路由 | PUT | `/api/route-static` |
| 查询IPv4静态路由 | GET | `/api/route-static` |
| 删除IPv4静态路由 | DELETE | `/api/route-static` |
| 新建IPv6静态路由 | POST | `/api/route6-static` |
| 查询IPv6静态路由 | GET | `/api/route6-static` |
| 删除IPv6静态路由 | DELETE | `/api/route6-static` |

---

## 新建 IPv4 静态路由

**端点**: `POST /api/route-static`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dst_ip | String | 是 | 目的IP |
| nh_type | Number | 是 | 出接口/下一跳，0：下一跳，1：出接口 |
| nh_ip | String | 否* | 下一跳（nh_type=0时必填） |
| oif | String | 否* | 出接口，可选隧道接口、GRE接口（nh_type=1时必填） |
| monitor_name | String | 否 | 健康检查对象 |
| distance | Number | 是 | 距离，范围：1-255 |
| weigh | Number | 是 | 权重，范围：1-100 |
| flag | Number | 否 | 启用/禁用，1：启用，0：禁用，默认启用 |

**请求示例**:

```json
{
    "dst_ip": "2.2.7.2/24",
    "nh_type": "0",
    "nh_ip": "172.24.0.1",
    "oif": "",
    "monitor_name": "",
    "distance": "25",
    "weigh": "100",
    "flag": "0"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "250",
    "str": "参数错误"
}
```

---

## 修改 IPv4 静态路由

**端点**: `PUT /api/route-static`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dst_ip | String | 是 | 目的IP |
| nh_type | Number | 是 | 出接口/下一跳，0：下一跳，1：出接口 |
| nh_ip | String | 否* | 下一跳（nh_type=0时必填） |
| oif | String | 否* | 出接口，可选隧道接口、GRE接口（nh_type=1时必填） |
| monitor_name | String | 否 | 健康检查对象 |
| distance | Number | 是 | 距离，范围：1-255 |
| weigh | Number | 是 | 权重，范围：1-100 |
| flag | Number | 否 | 启用/禁用，1：启用，0：禁用，默认启用 |

**请求示例**:

```json
{
    "dst_ip": "2.2.7.2/24",
    "nh_type": "0",
    "nh_ip": "172.24.0.1",
    "oif": "",
    "monitor_name": "",
    "distance": "25",
    "weigh": "10",
    "flag": "0"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "250",
    "str": "参数错误"
}
```

---

## 查询 IPv4 静态路由

**端点**: `GET /api/route-static`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dst_ip | String | 目的IP |
| nh_type | Number | 出接口/下一跳，0：下一跳，1：出接口 |
| nh_ip | String | 下一跳 |
| distance | Number | 距离 |
| weigh | Number | 权重 |
| flag | Number | 启用/禁用 |
| monitor_name | String | 健康检查对象 |

**响应示例**:

```json
{
    "data": [
        {
            "dst_ip": "0.0.0.0/0",
            "nh_type": "0",
            "nh_ip": "172.24.0.1",
            "distance": "1",
            "weigh": "1",
            "flag": "1",
            "monitor_name": ""
        }
    ],
    "total": 1
}
```

---

## 删除 IPv4 静态路由

**端点**: `DELETE /api/route-static`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dst_ip | String | 是 | 目的IP |
| nh_type | Number | 是 | 出接口/下一跳，0：下一跳，1：出接口 |
| nh_ip | String | 否* | 下一跳（nh_type=0时必填） |
| oif | String | 否* | 出接口，可选隧道接口、GRE接口（nh_type=1时必填） |

**请求示例**:

```json
{
    "dst_ip": "2.2.7.2/24",
    "nh_type": "0",
    "nh_ip": "172.24.0.1",
    "oif": ""
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "36",
    "str": "找不到静态路由"
}
```

---

## 新建 IPv6 静态路由

**端点**: `POST /api/route6-static`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dst_ip | String | 是 | 目的IPv6地址 |
| nh_type | Number | 是 | 出接口/下一跳地址/下一跳地址和出接口，0：下一跳地址，1：出接口，2：下一跳地址和出接口 |
| nh_ip | String | 否* | 下一跳IPv6地址（nh_type=0或2时必填） |
| oif | String | 否* | 出接口，可选隧道接口、GRE接口（nh_type=1或2时必填） |
| distance | Number | 是 | 距离，范围：1-255 |
| weigh | Number | 是 | 权重，范围：1-100 |

**请求示例**:

```json
{
    "dst_ip": "2022::20/64",
    "nh_type": "0",
    "nh_ip": "2021::21",
    "oif": "",
    "distance": "25",
    "weigh": "100"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "11",
    "str": "地址格式错误"
}
```

---

## 查询 IPv6 静态路由

**端点**: `GET /api/route6-static`

**请求参数（可选）**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dst_ip | String | 否 | 目的IPv6地址 |
| nh_type | Number | 否 | 出接口/下一跳地址/下一跳地址和出接口 |
| nh_ip | String | 否 | 下一跳IPv6地址 |
| oif | String | 否 | 出接口 |
| distance | Number | 否 | 距离 |
| weigh | Number | 否 | 权重 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dst_ip | String | 目的IPv6地址 |
| nh_type | Number | 出接口/下一跳类型 |
| nh_ip | String | 下一跳IPv6地址 |
| distance | Number | 距离 |
| weigh | Number | 权重 |
| monitor_name | String | 健康检查对象 |

**响应示例**:

查询成功返回所有查询内容：

```json
{
    "data": [
        {
            "dst_ip": "2022::/64",
            "nh_type": "0",
            "nh_ip": "2021::21",
            "distance": "25",
            "weigh": "100",
            "monitor_name": ""
        }
    ],
    "total": 1
}
```

查询不存在返回空：

```json
{
    "data": [],
    "total": 0
}
```

---

## 删除 IPv6 静态路由

**端点**: `DELETE /api/route6-static`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dst_ip | String | 是 | 目的IPv6地址 |
| nh_type | Number | 是 | 出接口/下一跳地址/下一跳地址和出接口 |
| nh_ip | String | 否* | 下一跳IPv6地址 |
| oif | String | 否* | 出接口 |
| distance | Number | 是 | 距离，范围：1-255 |
| weigh | Number | 是 | 权重，范围：1-100 |

**请求示例**:

```json
{
    "dst_ip": "2022::/64",
    "nh_type": "2",
    "nh_ip": "2020::20",
    "oif": "ge0/1",
    "distance": "1",
    "weigh": "1"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "36",
    "str": "找不到静态路由"
}
```

---

## 参数说明

### nh_type 参数值说明

| 值 | 说明 |
|----|------|
| 0 | 使用下一跳IP地址 |
| 1 | 使用出接口 |
| 2 | 同时使用下一跳IP地址和出接口（仅IPv6） |

### flag 参数说明

| 值 | 说明 |
|----|------|
| 0 | 禁用该路由 |
| 1 | 启用该路由（默认） |
