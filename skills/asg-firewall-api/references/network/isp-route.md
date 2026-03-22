# ISP 路由配置

## 概述

ISP 路由模块提供运营商策略路由的配置管理功能，支持基于运营商地址库的路由选择。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 新建ISP策略路由 | POST | `/api/route-isp` |
| 修改ISP策略路由 | PUT | `/api/route-isp` |
| 查询ISP策略路由 | GET | `/api/route-isp` |
| 删除ISP策略路由 | DELETE | `/api/route-isp` |

---

## 新建 ISP 策略路由

**端点**: `POST /api/route-isp`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| mp_alg | String | 是 | 多路径选择，per-source-address（按源地址）或 per-ip-connection（按连接） |
| nexthop_items | Array | 是 | 下一跳信息列表 |
| nexthop_items[].oifname | String | 否* | 出接口名称（type=out_if时必填） |
| nexthop_items[].type | String | 是 | gateway（网关）或 out_if（出接口） |
| nexthop_items[].gw | String | 否* | 网关IP（type=gateway时必填） |
| nexthop_items[].weight | String | 是 | 权重 |
| nexthop_items[].monitor | String | 是 | 健康检查（健康检查对象/健康检查组） |
| nexthop_items[].oiflabel | String | 否 | 出接口标签 |
| enable | Number | 是 | 启用状态，0禁用/1启用 |
| dst_addr | String | 是 | ISP地址库（地址对象/地址组） |

**请求示例（类型为网关）**:

```json
{
    "mp_alg": "per-source-address",
    "nexthop_items": [{
        "type": "gateway",
        "gw": "172.24.0.1",
        "oifname": "",
        "monitor": "health1",
        "weight": "1"
    }],
    "enable": "1",
    "dst_addr": "ISP_CMCC.dat"
}
```

**请求示例（类型为出接口）**:

```json
{
    "mp_alg": "per-ip-connection",
    "nexthop_items": [{
        "type": "out_if",
        "gw": "",
        "oifname": "tunl0",
        "monitor": "health1",
        "weight": "1",
        "oiflabel": "tunl0"
    }],
    "enable": "1",
    "dst_addr": "ISP_CMCC.dat"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-22",
    "str": "下一跳信息数据选项不能为空"
}
```

---

## 修改 ISP 策略路由

**端点**: `PUT /api/route-isp`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | 策略ID |
| mp_alg | String | 是 | 多路径选择，per-source-address（按源地址）或 per-ip-connection（按连接） |
| nexthop_items | Array | 是 | 下一跳信息列表 |
| nexthop_items[].oifname | String | 否* | 出接口名称（type=out_if时必填） |
| nexthop_items[].type | String | 是 | gateway（网关）或 out_if（出接口） |
| nexthop_items[].gw | String | 否* | 网关IP（type=gateway时必填） |
| nexthop_items[].weight | String | 是 | 权重 |
| nexthop_items[].monitor | String | 是 | 健康检查 |
| nexthop_items[].oiflabel | String | 否 | 出接口标签 |
| nexthop_items[].hits | Number | 否 | 命中计数 |
| nexthop_items[].status | String | 否 | 状态（active/inactive） |
| enable | Number | 否 | 启用状态，0禁用/1启用 |
| action | String | 是 | 单播（unicast） |
| dst_addr | String | 是 | ISP地址库 |

**请求示例**:

```json
{
    "id": "2",
    "mp_alg": "per-source-address",
    "action": "unicast",
    "nexthop_items": [{
        "type": "out_if",
        "gw": "",
        "oifname": "tunl0",
        "monitor": "health1",
        "weight": "1",
        "oiflabel": "tunl0",
        "hits": "0",
        "status": "inactive"
    }, {
        "type": "gateway",
        "gw": "172.24.0.1",
        "oifname": "ge0/0",
        "monitor": "health1",
        "weight": "1"
    }],
    "enable": "1",
    "dst_addr": "ISP_CMCC.dat",
    "bingo": "0"
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

## 删除 ISP 策略路由

**端点**: `DELETE /api/route-isp`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | String | 是 | 策略ID |

**请求示例**:

```json
{
    "id": 2
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

## 查询 ISP 策略路由

**端点**: `GET /api/route-isp`

**查询参数（URL参数）**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 否 | 页数（分页查询时必填） |
| pageSize | Number | 否 | 每页展示条数（分页查询时必填） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| vrf_name | String | ISP路由所属vrf名称 |
| id | String | 策略ID |
| mp_alg | String | 多路径选择 |
| nexthop_items | Object | 下一跳信息 |
| nexthop_items.group[].oifname | String | 出接口名称 |
| nexthop_items.group[].type | String | gateway 或 out_if |
| nexthop_items.group[].gw | String | 网关IP |
| nexthop_items.group[].weight | String | 权重 |
| nexthop_items.group[].monitor | String | 健康检查 |
| nexthop_items.group[].oiflabel | String | 出接口标签 |
| nexthop_items.group[].hits | Number | 命中计数 |
| nexthop_items.group[].status | String | 状态（active/inactive） |
| enable | Number | 启用状态 |
| action | String | 单播（unicast） |
| dst_addr | String | ISP地址库 |
| hits | Number | 命中次数 |
| bingo | String | 策略命中次数 |

**响应示例**:

查询有数据返回所有数据：

```json
{
    "data": [
        {
            "vrf_name": "vsys0",
            "id": "2",
            "enable": "1",
            "dst_addr": "ISP_CMCC.dat",
            "action": "unicast",
            "mp_alg": "per-source-address",
            "bingo": "12",
            "nexthop_items": {
                "group": [
                    {
                        "oifname": "tunl0",
                        "type": "out_if",
                        "monitor": "health1",
                        "weight": "1",
                        "hits": "0",
                        "status": "inactive"
                    },
                    {
                        "oifname": "ge0/0",
                        "gw": "172.24.0.1",
                        "type": "gateway",
                        "monitor": "health1",
                        "weight": "1",
                        "hits": "8",
                        "status": "active"
                    }
                ]
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

### type 参数说明

| 值 | 说明 |
|----|------|
| gateway | 使用网关IP |
| out_if | 使用出接口 |

### status 参数说明

| 值 | 说明 |
|----|------|
| active | 激活状态 |
| inactive | 未激活状态 |

### enable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 禁用该策略路由 |
| 1 | 启用该策略路由 |

---

## ISP 地址库说明

ISP 路由使用预定义的运营商地址库，常见的地址库包括：

- `ISP_CMCC.dat` - 中国移动地址库
- `ISP_CTCC.dat` - 中国电信地址库
- `ISP_CUCC.dat` - 中国联通地址库

地址库文件需要预先在系统中配置。
