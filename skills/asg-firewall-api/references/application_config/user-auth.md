# 用户认证

## 概述

用户认证模块提供跨三层用户和MAC绑定功能的配置管理，包括用户管理和SNMP用户同步。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **用户管理** | 新建用户 | POST | `/api/auth-user` |
| **用户管理** | 编辑用户 | PUT | `/api/auth-user` |
| **用户管理** | 删除用户 | DELETE | `/api/auth-user` |
| **用户管理** | 获取用户 | GET | `/api/auth-user` |
| **SNMP用户同步** | 新建SNMP用户同步 | POST | `/api/snmp-sync` |
| **SNMP用户同步** | 编辑SNMP用户同步 | PUT | `/api/snmp-sync` |
| **SNMP用户同步** | 删除SNMP用户同步 | DELETE | `/api/snmp-sync` |
| **SNMP用户同步** | 显示SNMP用户同步 | GET | `/api/snmp-sync` |

---

# 用户管理

## 新建用户

**端点**: `POST /api/auth-user`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Id | Number | 是 | 用户id |
| predefined | Number | 是 | 1：预定义；0：自定义 |
| bind_type | String | 是 | Ip：静态绑定；none：非静态绑定 |
| readonly | Number | 是 | 1：只读；0：可编辑 |
| name | String | 是 | 用户名称 |
| show_name | String | 是 | 展示用户名称 |
| alias | String | 是 | 别名 |
| description | String | 是 | 描述 |
| ref_num | Number | 是 | 引用计数 |
| enable | Number | 是 | 使用状态（1：开启，0：关闭） |
| type | String | 是 | 用户类型（local_db：本地用户；radius：radius用户；ldap：ldap用户；bind：静态绑定用户；none：匿名用户） |
| ldap | String | 是 | ldap服务器名字 |
| bind_include | Array | 是 | 绑定ip |
| bind_include[].type | String | 是 | 类型（Range：ip地址范围；host：ip地址） |
| bind_include[].address | String | 是 | 地址 |
| bind_exclude | Array | 是 | 排除ip |
| bind_exclude[].type | String | 是 | 类型（Range：ip地址范围；host：ip地址） |
| bind_exclude[].address | String | 是 | 地址 |
| bind_include_ip6 | Array | 是 | 绑定ipv6 |
| bind_include_ip6[].type | String | 是 | 类型（Range：ip地址范围；host：ip地址） |
| bind_include_ip6[].address | String | 是 | 地址 |
| bind_exclude_ip6 | Array | 是 | 排除ipv6 |
| bind_exclude_ip6[].type | String | 是 | 类型（Range：ip地址范围；host：ip地址） |
| bind_exclude_ip6[].address | String | 是 | 地址 |
| bind_include_mac | Array | 是 | 绑定mac |
| bind_include_mac[].type | String | 是 | 类型（host：mac地址） |
| bind_include_mac[].address | String | 是 | 地址 |

**请求示例**:

```json
{
    "type": "bind",
    "enable": 1,
    "name": "admin",
    "bind_include_mac": {
        "group": {
            "type": "host",
            "address": "22:22:22:22:22:23"
        }
    }
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

## 编辑用户

**端点**: `PUT /api/auth-user`

**请求参数**: 同新建用户

**请求示例**:

```json
{
    "id": "2002",
    "predefined": "0",
    "readonly": "0",
    "name": "2",
    "show_name": "2",
    "alias": "",
    "description": "",
    "ref_num": "0",
    "enable": "1",
    "type": "bind",
    "bind_type": "ip",
    "bind_include": {
        "group": {
            "type": "host",
            "address": "2.2.2.2"
        }
    },
    "bind_exclude": {
        "group": [
            {
                "type": "host",
                "address": "4.4.4.4"
            },
            {
                "type": "range",
                "address": "3.3.3.3-4.4.4.4"
            }
        ]
    },
    "bind_include_ip6": {
        "group": [
            {
                "type": "host",
                "address": "6000::1"
            },
            {
                "type": "range",
                "address": "6000::2-6000::7"
            }
        ]
    },
    "bind_exclude_ip6": {
        "group": [
            {
                "type": "host",
                "address": "3000::2"
            },
            {
                "type": "range",
                "address": "3000::1-3000::3"
            }
        ]
    },
    "bind_include_mac": {
        "group": [
            {
                "type": "host",
                "address": "22:22:22:22:22:22"
            },
            {
                "type": "host",
                "address": "22:22:22:22:22:23"
            }
        ]
    }
}
```

**响应示例**: 同新建用户

---

## 删除用户

**端点**: `DELETE /api/auth-user`

**请求参数**: 同新建用户

**请求示例**:

```json
{
    "id": "1",
    "predefined": "1",
    "readonly": "1",
    "name": "any",
    "show_name": "所有用户",
    "alias": "",
    "description": "",
    "ref_num": "2",
    "enable": "1",
    "type": "none",
    "bind_type": "none"
}
```

**响应示例**: 同新建用户

---

## 获取用户

**端点**: `GET /api/auth-user`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 是 | 当前页数 |
| pageSize | Number | 是 | 页码 |
| lang | String | 是 | 语言（cn：中文，en：英文） |
| api_key | String | 是 | 接口的api |

**响应参数**: 同新建用户请求参数

**响应示例**:

```json
{
    "data": [
        {
            "id": "1",
            "predefined": "1",
            "readonly": "1",
            "name": "any",
            "show_name": "所有用户",
            "alias": "",
            "description": "",
            "ref_num": "2",
            "enable": "1",
            "type": "none",
            "bind_type": "none"
        },
        {
            "id": "2001",
            "predefined": "0",
            "readonly": "0",
            "name": "1",
            "show_name": "1",
            "alias": "",
            "description": "",
            "ref_num": "0",
            "enable": "1",
            "type": "local_db",
            "passwd": "1111111",
            "bind_type": "none"
        }
    ],
    "total": 4
}
```

---

# SNMP用户同步

## 新建SNMP用户同步

**端点**: `POST /api/snmp-sync`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 是 | 名称 |
| desc | String | 是 | 描述 |
| v1 | String | 是 | 版本号（0：否，1：是） |
| v2c | Number | 是 | 版本号（0：否，1：是） |
| v3 | Number | 是 | 版本号（0：否，1：是） |
| enable | Number | 是 | 启用（1：是，0：否） |
| interval | Number | 是 | 任务周期(秒) |
| peername | String | 是 | 服务器IP地址 |
| community | String | 是 | 团体名 |

**请求示例**:

```json
{
    "enable": "1",
    "interval": "60",
    "name": "test123",
    "desc": "test",
    "peername": "192.168.1.12",
    "community": "test123",
    "v2c": "1"
}
```

**响应示例**: 下发正确无返回值

---

## 编辑SNMP用户同步

**端点**: `PUT /api/snmp-sync`

**请求参数**: 同新建SNMP用户同步，增加以下参数：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| nr_entrys | String | 是 | 查询中的条目数 |
| state | String | 是 | 状态（waiting：等待中，querying：查询中，canceling：取消中，success：同步成功，fail：同步失败） |
| cost | Number | 是 | 花费时间 |
| mac | String | 是 | MAC地址 |
| nr_reco | Array | 是 | 记录数量 |

**请求示例**:

```json
{
    "name": "test123",
    "desc": "test",
    "v1": "0",
    "v3": "0",
    "v2c": "1",
    "enable": "1",
    "interval": "60",
    "peername": "192.168.1.12",
    "community": "test123",
    "nr_entrys": "0",
    "cost": "1",
    "state": "querying",
    "mac": "00:00:00:00:00:00",
    "nr_reco": "0"
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

## 删除SNMP用户同步

**端点**: `DELETE /api/snmp-sync`

**请求参数**: 同编辑SNMP用户同步

**请求示例**:

```json
{
    "name": "test123",
    "desc": "test",
    "v1": "0",
    "v3": "0",
    "v2c": "1",
    "enable": "1",
    "interval": "60",
    "peername": "192.168.1.12",
    "community": "test123",
    "nr_entrys": "0",
    "cost": "1",
    "state": "querying",
    "mac": "00:00:00:00:00:00",
    "nr_reco": "0"
}
```

**响应示例**: 同编辑SNMP用户同步

---

## 显示SNMP用户同步

**端点**: `GET /api/snmp-sync`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | Number | 是 | 当前页数 |
| pageSize | Number | 是 | 页码 |
| lang | String | 是 | 语言（cn：中文，en：英文） |
| api_key | String | 是 | 接口的api |

**响应参数**: 同编辑SNMP用户同步，增加以下参数：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| group | Array | 包含每条同步结果 |
| group[].year | Number | 年 |
| group[].month | Number | 月 |
| group[].day | Number | 日 |
| group[].hour | Number | 时 |
| group[].minute | Number | 分 |
| group[].second | Number | 秒 |
| group[].current | Number | 记录属性（1：最新记录，非1：历史记录） |
| group[].nr_pair | Number | 已同步IP-MAC地址对 |

**响应示例**:

```json
{
    "data": [
        {
            "name": "test123",
            "desc": "test",
            "v1": "0",
            "v3": "0",
            "v2c": "1",
            "enable": "1",
            "interval": "60",
            "peername": "192.168.1.12",
            "community": "test123",
            "nr_entrys": "0",
            "cost": "1",
            "state": "querying",
            "mac": "00:00:00:00:00:00",
            "nr_reco": [
                "20",
                "20"
            ],
            "snmp_rspan_reco": {
                "group": [
                    {
                        "year": "2022",
                        "month": "11",
                        "day": "3",
                        "hour": "14",
                        "minute": "1",
                        "second": "48",
                        "current": "1",
                        "nr_pair": "99"
                    },
                    {
                        "year": "2022",
                        "month": "11",
                        "day": "3",
                        "hour": "14",
                        "minute": "0",
                        "second": "43",
                        "current": "0",
                        "nr_pair": "99"
                    }
                ]
            }
        }
    ],
    "total": 1
}
```

---

## 参数说明

### type 参数说明

| 值 | 说明 |
|----|------|
| local_db | 本地用户 |
| radius | radius用户 |
| ldap | ldap用户 |
| bind | 静态绑定用户 |
| none | 匿名用户 |

### bind_type 参数说明

| 值 | 说明 |
|----|------|
| Ip | 静态绑定 |
| none | 非静态绑定 |

### predefined 参数说明

| 值 | 说明 |
|----|------|
| 0 | 自定义 |
| 1 | 预定义 |

### state 参数说明

| 值 | 说明 |
|----|------|
| waiting | 等待中 |
| querying | 查询中 |
| canceling | 取消中 |
| success | 同步成功 |
| fail | 同步失败 |
