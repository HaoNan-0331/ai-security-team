# 镜像策略

## 概述

镜像策略模块提供流量镜像功能的配置管理，包括新建、修改、删除和获取镜像策略。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **镜像策略** | 新建镜像策略 | POST | `/api/mirror-policy` |
| **镜像策略** | 修改镜像策略 | PUT | `/api/mirror-policy` |
| **镜像策略** | 删除镜像策略 | DELETE | `/api/mirror-policy` |
| **镜像策略** | 获取镜像策略 | GET | `/api/mirror-policy` |

---

# 镜像策略

## 新建镜像策略

**端点**: `POST /api/mirror-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | 策略id（范围：0-10000），0：不填写，按照顺序添加 |
| if_in | String | 否 | 入接口 |
| if_out | String | 否 | 出接口 |
| protocol | Number | 否 | 协议类型（0：ipv4，1：ipv6） |
| enable | Number | 否 | 策略是否启用（0：不启用，1：启用） |
| app | String | 否 | 应用对象名称，默认是any |
| sip | String | 否 | 源地址 |
| dip | String | 否 | 目的地址 |
| sev | String | 否 | 服务对象 |
| user | String | 否 | 用户对象 |
| tr | String | 否 | 时间对象 |
| dst_ifname_list | Array | 否 | 镜像出接口列表 |
| replace_dest_mac_status | Number | 否 | MAC转换状态（0：不转换mac，1：转换mac） |
| replace_dest_mac | String | 是 | 依赖replace_dest_mac_status的值，1必须填写 |
| strip_vlan | Number | 否 | VLAN剥除（0：不剥除Vlan，1：剥除Vlan） |
| mirror_dev | String | 否 | 镜像出接口名称 |

**请求示例**:

```json
{
    "if_in": "any",
    "if_out": "any",
    "protocol": "1",
    "vrf_name": "vrf0",
    "id": "0",
    "app": "any",
    "dst_ifname_list": [
        {
            "replace_dest_mac_status": "1",
            "strip_vlan": "1",
            "mirror_dev": "ge0/3",
            "replace_dest_mac": "22:22:22:22:22:22"
        }
    ],
    "sip": "any",
    "dip": "any",
    "sev": "any",
    "user": "any",
    "tr": "always",
    "lang": "cn"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "122",
    "str": "该策略已经存在"
}
```

---

## 修改镜像策略

**端点**: `PUT /api/mirror-policy`

**请求参数**: 同新建镜像策略

**请求示例**:

```json
{
    "if_in": "any",
    "if_out": "any",
    "protocol": "1",
    "vrf_name": "vrf0",
    "id": "1",
    "app": "any",
    "dst_ifname_list": [
        {
            "replace_dest_mac_status": "1",
            "strip_vlan": "1",
            "mirror_dev": "ge0/3",
            "replace_dest_mac": "22:22:22:22:22:22"
        }
    ],
    "sip": "any",
    "dip": "any",
    "sev": "any",
    "user": "any",
    "tr": "always",
    "lang": "cn"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "87",
    "str": "目标策略不存在 "
}
```

---

## 删除镜像策略

**端点**: `DELETE /api/mirror-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | 策略id（范围：1-10000） |
| protocol | Number | 否 | 协议类型（0：ipv4，1：ipv6） |

**请求示例**:

```json
{
    "id": "1",
    "protocol": "1"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "87",
    "str": "目标策略不存在 "
}
```

---

## 获取镜像策略

**端点**: `GET /api/mirror-policy`

**请求参数**: 通过URL参数传递

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| protocol | Number | 是 | 协议类型（0：ipv4，1：ipv6） |
| page | Number | 是 | 当前页数 |
| pageSize | Number | 是 | 页码 |
| lang | String | 是 | 语言（cn：中文，en：英文） |
| api_key | String | 是 | 接口的api |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | Number | 策略id（范围：0-10000）0：不填写，按照顺序添加 |
| if_in | String | 入接口 |
| if_out | String | 出接口 |
| protocol | Number | 协议类型（0：ipv4，1：ipv6） |
| enable | Number | 策略是否启用（0：不启用，1：启用） |
| app | String | 应用对象名称，默认是any |
| sip | String | 源地址 |
| dip | String | 目的地址 |
| sev | String | 服务对象 |
| user | String | 用户对象 |
| tr | String | 时间对象 |
| dst_ifname_list | Array | 镜像出接口列表 |
| replace_dest_mac_status | Number | MAC转换状态（0：不转换mac，1：转换mac） |
| replace_dest_mac | String | 依赖replace_dest_mac_status的值，1必须填写 |
| strip_vlan | Number | VLAN剥除（0：不剥除Vlan，1：剥除Vlan） |
| mirror_dev | String | 镜像出接口名称 |

**响应示例**:

```json
{
    "data": [{
        "id": "1",
        "protocol": "1",
        "vrf_name": "",
        "if_in": "any",
        "if_out": "any",
        "sip": "any",
        "dip": "any",
        "sev": "any",
        "user": "any",
        "user_show": "所有用户",
        "app": "any",
        "app_show": "any",
        "tr": "always",
        "dst_ifname_list": {
            "group": {
                "mirror_dev": "ge0/3",
                "strip_vlan": "0",
                "replace_dest_mac_status": "0"
            }
        },
        "enable": "1",
        "bingo": "0"
    }],
    "total": 1
}
```

---

## 参数说明

### protocol 参数说明

| 值 | 说明 |
|----|------|
| 0 | ipv4 |
| 1 | ipv6 |

### enable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 不启用 |
| 1 | 启用 |

### replace_dest_mac_status 参数说明

| 值 | 说明 |
|----|------|
| 0 | 不转换mac |
| 1 | 转换mac |

### strip_vlan 参数说明

| 值 | 说明 |
|----|------|
| 0 | 不剥除Vlan |
| 1 | 剥除Vlan |
