# 策略路由配置

## 概述

策略路由模块提供 IPv4 和 IPv6 策略路由的配置管理功能，支持基于源地址、目的地址、用户、应用、服务等条件的路由策略。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 新建IPv4策略路由 | POST | `/api/route-policy` |
| 修改IPv4策略路由 | PUT | `/api/route-policy` |
| 查询IPv4策略路由 | GET | `/api/route-policy` |
| 删除IPv4策略路由 | DELETE | `/api/route-policy` |
| 新建IPv6策略路由 | POST | `/api/route6-policy` |
| 修改IPv6策略路由 | PUT | `/api/route6-policy` |
| 查询IPv6策略路由 | GET | `/api/route6-policy` |
| 删除IPv6策略路由 | DELETE | `/api/route6-policy` |

---

## 新建 IPv4 策略路由

**端点**: `POST /api/route-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| mp_alg | String | 是 | 多路径选择，per-source-address（按源地址）或 per-ip-connection（按连接） |
| nexthop_items | Array | 是 | 下一跳信息列表 |
| nexthop_items[].oifname | String | 否 | 出接口名称 |
| nexthop_items[].type | String | 是 | gateway（网关）或 out_if（出接口） |
| nexthop_items[].gw | String | 否* | 网关IP（type=gateway时必填） |
| nexthop_items[].weight | String | 是 | 权重 |
| nexthop_items[].monitor | String | 否 | 健康检查（健康检查对象/健康检查组） |
| nexthop_items[].oiflabel | String | 否 | 出接口标签 |
| enable | Number | 是 | 启用状态，0禁用/1启用 |
| src_zone | String | 是 | 入接口 |
| src_addr | String | 是 | 源地址（地址对象/地址组） |
| dst_addr | String | 是 | 目的地址（地址对象/地址组） |
| users | String | 是 | 用户（用户对象/用户组） |
| service | String | 否 | 服务（服务对象/服务组） |
| apps | String | 是 | 应用（应用对象/应用组） |
| schedule | String | 是 | 时间（时间对象） |

**请求示例**:

```json
{
    "mp_alg": "per-source-address",
    "nexthop_items": [{
        "oifname": "",
        "gw": "1.1.1.2",
        "type": "gateway",
        "monitor": "",
        "weight": "3"
    }],
    "enable": "1",
    "src_zone": "ge0/0",
    "src_addr": "any",
    "dst_addr": "any",
    "users": "any",
    "service": "any",
    "apps": "any",
    "schedule": "always"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-17",
    "str": "相同的策略路由1已经存在"
}
```

---

## 修改 IPv4 策略路由

**端点**: `PUT /api/route-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | 策略ID |
| mp_alg | String | 是 | 多路径选择，per-source-address（按源地址）或 per-ip-connection（按连接） |
| nexthop_items | Array | 是 | 下一跳信息列表 |
| nexthop_items[].oifname | String | 否 | 出接口名称 |
| nexthop_items[].type | String | 是 | gateway（网关）或 out_if（出接口） |
| nexthop_items[].gw | String | 否* | 网关IP（type=gateway时必填） |
| nexthop_items[].weight | String | 是 | 权重 |
| nexthop_items[].monitor | String | 否 | 健康检查 |
| nexthop_items[].oiflabel | String | 否 | 出接口标签 |
| nexthop_items[].hits | Number | 否 | 命中计数 |
| nexthop_items[].status | String | 否 | 状态（active） |
| enable | Number | 否 | 启用状态，0禁用/1启用 |
| src_zone | String | 是 | 入接口 |
| src_addr | String | 是 | 源地址（地址对象/地址组） |
| dst_addr | String | 是 | 目的地址（地址对象/地址组） |
| users | String | 是 | 用户（用户对象/用户组） |
| apps | String | 是 | 应用（应用对象/应用组） |
| schedule | String | 否 | 时间（时间对象） |

**请求示例**:

```json
{
    "id": "4",
    "enable": "1",
    "src_zone": "ge0/0",
    "src_addr": "any",
    "dst_addr": "any",
    "users": "any",
    "service": "any",
    "apps": "any",
    "schedule": "always",
    "mp_alg": "per-source-address",
    "nexthop_items": [{
        "oifname": "ge0/0",
        "gw": "172.24.253.196",
        "type": "gateway",
        "monitor": "",
        "weight": "5"
    }]
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-2",
    "str": "策略路由 4 不存在"
}
```

---

## 删除 IPv4 策略路由

**端点**: `DELETE /api/route-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | 策略ID |

**请求示例**:

```json
{
    "id": "1"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-2",
    "str": "策略路由 20 不存在"
}
```

---

## 查询 IPv4 策略路由

**端点**: `GET /api/route-policy`

**查询参数（URL参数）**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 否 | 页数（分页查询时必填） |
| pageSize | Number | 否 | 每页展示条数（分页查询时必填） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| vrf_name | String | 策略路由所属vrf名称 |
| id | String | 路由ID |
| mp_alg | String | 多路径选择 |
| nexthop_items | Object | 下一跳信息 |
| nexthop_items.group[].oifname | String | 出接口名称 |
| nexthop_items.group[].type | String | gateway 或 out_if |
| nexthop_items.group[].gw | String | 网关IP |
| nexthop_items.group[].weight | String | 权重 |
| nexthop_items.group[].monitor | String | 健康检查 |
| nexthop_items.group[].oiflabel | String | 出接口标签 |
| hits | String | 命中次数 |
| enable | Number | 启用状态 |
| src_zone | String | 入接口 |
| src_addr | String | 源地址 |
| dst_addr | String | 目的地址 |
| users | String | 用户 |
| service | String | 服务 |
| apps | String | 应用 |
| schedule | String | 时间 |
| bingo | String | 命中次数 |

**响应示例**:

查询有数据返回：

```json
{
    "data": [
        {
            "vrf_name": "vsys0",
            "id": "1",
            "enable": "1",
            "src_zone": "ge0/0",
            "src_addr": "any",
            "dst_addr": "any",
            "users": "any",
            "service": "any",
            "apps": "any",
            "apps_show": "any",
            "schedule": "always",
            "action": "unicast",
            "mp_alg": "per-source-address",
            "bingo": "0",
            "nexthop_items": {
                "group": {
                    "oifname": "ge0/0",
                    "gw": "172.24.12.10",
                    "type": "gateway",
                    "monitor": "",
                    "weight": "3",
                    "hits": "0",
                    "status": "active"
                }
            }
        }
    ],
    "total": 1
}
```

无数据返回：

```json
{
    "data": [],
    "total": 0
}
```

---

## 新建 IPv6 策略路由

**端点**: `POST /api/route6-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| mp_alg | String | 是 | 多路径选择，per-source-address（按源地址）或 per-ip-connection（按连接） |
| oifname | String | 是 | 出接口名称 |
| gw | String | 是 | 网关IPv6地址 |
| enable | Number | 是 | 启用状态，0禁用/1启用 |
| src_zone | String | 是 | 入接口 |
| src_addr | String | 是 | 源地址（地址对象/地址组） |
| dst_addr | String | 是 | 目的地址（地址对象/地址组） |
| users | String | 是 | 用户（用户对象/用户组） |
| service | String | 否 | 服务（服务对象/服务组） |
| apps | String | 是 | 应用（应用对象/应用组） |
| schedule | String | 是 | 时间（时间对象） |

**请求示例**:

```json
{
    "mp_alg": "per-source-address",
    "enable": "1",
    "src_zone": "ge0/2",
    "oifname": "ge0/3",
    "gw": "2000::20",
    "src_addr": "any",
    "dst_addr": "any",
    "users": "any",
    "service": "any",
    "apps": "any",
    "schedule": "always"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-17",
    "str": "相同的策略路由1已经存在"
}
```

---

## 修改 IPv6 策略路由

**端点**: `PUT /api/route6-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略路由ID |
| mp_alg | String | 是 | 多路径选择，per-source-address（按源地址）或 per-ip-connection（按连接） |
| oifname | String | 是 | 出接口名称 |
| gw | String | 是 | 网关IPv6地址 |
| enable | Number | 是 | 启用状态，0禁用/1启用 |
| src_zone | String | 是 | 入接口 |
| src_addr | String | 是 | 源地址（地址对象/地址组） |
| dst_addr | String | 是 | 目的地址（地址对象/地址组） |
| users | String | 是 | 用户（用户对象/用户组） |
| service | String | 否 | 服务（服务对象/服务组） |
| apps | String | 是 | 应用（应用对象/应用组） |
| apps_show | String | 否 | 应用名称显示（中英文显示应用名称） |
| schedule | String | 是 | 时间（时间对象） |

**请求示例**:

```json
{
    "id": "1",
    "enable": "1",
    "src_zone": "ge0/2",
    "src_addr": "test1-v6",
    "dst_addr": "testv6-dip",
    "users": "any",
    "service": "server1",
    "apps": "online-community",
    "apps_show": "社交网络",
    "schedule": "always",
    "action": "unicast",
    "mp_alg": "per-ip-connection",
    "bingo": "0",
    "oifname": "ge0/5",
    "gw": "2022::20"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-2",
    "str": "策略路由 10 不存在"
}
```

---

## 删除 IPv6 策略路由

**端点**: `DELETE /api/route6-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | 策略ID |

**请求示例**:

```json
{
    "id": "1"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-2",
    "str": "策略路由 20 不存在"
}
```

---

## 查询 IPv6 策略路由

**端点**: `GET /api/route6-policy`

**查询参数（URL参数）**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 否 | 页数（分页查询时必填） |
| pageSize | Number | 否 | 每页展示条数（分页查询时必填） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | Number | 处理结果 |
| str | String | 处理结果 |
| id | Number | 策略路由ID |
| vrf_name | String | 策略路由所属vrf名称 |
| mp_alg | String | 多路径选择 |
| oifname | String | 出接口名称 |
| gw | String | 网关IPv6地址 |
| enable | Number | 启用状态 |
| src_zone | String | 入接口 |
| src_addr | String | 源地址 |
| dst_addr | String | 目的地址 |
| users | String | 用户 |
| service | String | 服务 |
| apps | String | 应用 |
| schedule | String | 时间 |
| bingo | String | 策略命中数 |

**响应示例**:

查询有数据返回所有数据：

```json
{
    "data": [
        {
            "vrf_name": "vsys0",
            "id": "1",
            "enable": "1",
            "src_zone": "ge0/2",
            "src_addr": "test1-v6",
            "dst_addr": "testv6-dip",
            "users": "any",
            "service": "server1",
            "apps": "online-community",
            "apps_show": "社交网络",
            "schedule": "always",
            "action": "unicast",
            "mp_alg": "per-ip-connection",
            "bingo": "0",
            "nexthop_items": {
                "group": {
                    "oifname": "ge0/5",
                    "gw": "2022::20",
                    "type": "gateway",
                    "status": "active",
                    "hits": "0"
                }
            }
        }
    ],
    "total": 1
}
```

查询无数据返回空：

```json
{
    "data": [],
    "total": 0
}
```

---

## 参数说明

### mp_alg 参数值说明

| 值 | 说明 |
|----|------|
| per-source-address | 按源地址进行多路径选择 |
| per-ip-connection | 按连接进行多路径选择 |

### enable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 禁用该策略路由 |
| 1 | 启用该策略路由 |

### type 参数说明

| 值 | 说明 |
|----|------|
| gateway | 使用网关IP |
| out_if | 使用出接口 |
