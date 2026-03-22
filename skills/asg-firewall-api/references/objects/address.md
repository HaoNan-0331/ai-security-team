# 地址对象

## 概述

地址对象模块提供地址对象和地址组对象的配置管理功能。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **地址对象** | 添加地址对象 | POST | `/api/address` |
| **地址对象** | 修改地址对象 | PUT | `/api/address` |
| **地址对象** | 删除地址对象信息 | DELETE | `/api/address` |
| **地址组对象** | 添加地址组对象 | POST | `/api/address-group` |
| **地址组对象** | 删除地址组对象 | DELETE | `/api/address-group` |

---

# 地址对象

## 添加地址对象

**端点**: `POST /api/address`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 地址对象名称 |
| desc | String | 否 | 地址对象描述 |
| type | Number | 否 | 地址对象类型（0代表ipv4地址） |
| item | Array | 是 | 地址项列表 |
| item[].type | Number | 是 | 地址类型（0：主机，1：子网，2：范围） |
| item[].host | String | 否 | ip地址 |
| item[].range1 | String | 否 | 地址起始 |
| item[].range2 | String | 否 | 地址结束 |
| item[].net | String | 否 | 网络地址 |

**请求示例**:

```json
{
    "name": "my_new",
    "desc": "my_new_add_obj",
    "type": 0,
    "item": [
        {
            "host": "7.7.7.7",
            "type": 0
        },
        {
            "net": "7.1.7.7/16",
            "type": 1
        },
        {
            "range1": "7.7.7.7",
            "range2": "7.7.7.70",
            "type": 2
        }
    ]
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "106",
    "str": "名称冲突"
}
```

---

## 修改地址对象

**端点**: `PUT /api/address`

**请求参数**: 同添加地址对象

**请求示例**:

```json
{
    "name": "my_new",
    "desc": "my_new_add_obj",
    "type": 0,
    "item": [
        {
            "host": "7.7.8.7",
            "type": 0
        },
        {
            "net": "7.1.7.8/16",
            "type": 1
        },
        {
            "range1": "7.7.7.8",
            "range2": "7.7.7.70",
            "type": 2
        }
    ]
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "116",
    "str": "非法的MAC地址"
}
```

---

## 删除地址对象信息

**端点**: `DELETE /api/address`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 地址对象名称 |
| type | Number | 否 | 地址对象类型（0代表ipv4地址） |
| def | Number | 否 | 地址对象定义类型（0表示自定义类型，1表示预定义类型） |

**请求示例**:

```json
{
    "name": "my_new",
    "type": 0,
    "def": 0
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "107",
    "str": "对象名称不存在"
}
```

---

# 地址组对象

## 添加地址组对象

**端点**: `POST /api/address-group`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 地址组对象名称 |
| desc | String | 否 | 地址对象描述 |
| item | Array | 是 | 地址项列表 |
| item[].addr_name | String | 是 | 该地址组对象应用的地址对象数组，"addr_name"引用的地址对象的名称 |

**请求示例**:

```json
{
    "name": "alan_addr_grp",
    "desc": "Just a test",
    "item": [
        {
            "addr_name": "bbbb"
        },
        {
            "addr_name": "my_new"
        }
    ]
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "106",
    "str": "名称冲突"
}
```

---

## 删除地址组对象

**端点**: `DELETE /api/address-group`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 要删除的地址组对象名称 |

**请求示例**:

```json
{
    "name": "alan_addr_grp"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "107",
    "str": "对象名称不存在"
}
```

---

## 参数说明

### type 参数说明

| 值 | 说明 |
|----|------|
| 0 | ipv4地址 |

### item[].type 参数说明

| 值 | 说明 |
|----|------|
| 0 | 主机 |
| 1 | 子网 |
| 2 | 范围 |

### def 参数说明

| 值 | 说明 |
|----|------|
| 0 | 自定义类型 |
| 1 | 预定义类型 |
