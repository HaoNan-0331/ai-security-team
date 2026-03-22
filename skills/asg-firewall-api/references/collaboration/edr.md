# EDR 联动

## 概述

EDR联动模块提供与终端检测响应系统的联动配置功能，包括EDR中心配置、安装路径、联动策略和资产列表管理。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **EDR中心** | 获取EDR中心配置 | GET | `/api/edr-center` |
| **EDR中心** | 修改EDR中心配置 | PUT | `/api/edr-center` |
| **安装路径** | 获取EDR安装路径 | GET | `/api/edr-install` |
| **安装路径** | 修改EDR安装路径 | PUT | `/api/edr-install` |
| **联动策略** | 获取EDR联动列表 | GET | `/api/edr-policy` |
| **联动策略** | 新建EDR联动策略 | POST | `/api/edr-policy` |
| **联动策略** | 修改EDR联动策略 | PUT | `/api/edr-policy` |
| **联动策略** | 删除EDR联动策略 | DELETE | `/api/edr-policy` |
| **联动策略** | 移动EDR联动策略 | PUT | `/api/edr-policy` |
| **联动策略** | 获取EDR联动https触发 | GET | `/api/edr-https` |
| **联动策略** | 修改EDR联动https触发 | PUT | `/api/edr-https` |
| **资产列表** | 获取EDR资产列表 | GET | `/api/edr-user` |
| **资产列表** | 临时放行EDR资产 | PUT | `/api/edr-user` |

---

# EDR 中心

## 获取 EDR 中心配置

**端点**: `GET /api/edr-center`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 否 | 语言（cn：中文，en：英文） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| central | String | 管理中心地址 |
| tenant_admin | String | 租户管理员 |
| auth_type | String | 密码认证（password：开启密码认证，none：关闭密码认证） |
| password | String | 管理员密码 |
| asset_sync | Number | 资产发现同步（1：开启，0：关闭） |
| enable | Number | 启用（1：开启，0：关闭） |
| asset_count | Number | 同步资产数量 |

**响应示例**:

```json
{
    "data": [{
        "central": "192.168.0.42:666",
        "tenant_admin": "zhaoxin",
        "auth_type": "password",
        "password": "admin!11",
        "asset_sync": "1",
        "asset_count": "100",
        "enable": "1"
    }],
    "total": 1
}
```

---

## 修改 EDR 中心配置

**端点**: `PUT /api/edr-center`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| central | String | 否 | 管理中心地址 |
| tenant_admin | String | 否 | 租户管理员 |
| auth_type | String | 是 | 密码认证（password：开启密码认证，none：关闭密码认证，缺省为none） |
| password | String | 是 | 管理员密码 |
| asset_sync | Number | 是 | 资产发现同步（1：开启，0：关闭，缺省为0） |
| enable | Number | 是 | 启用（1：开启，0：关闭，缺省为0） |
| asset_count | Number | 是 | 同步资产数量，缺省为1 |

**请求示例**:

```json
{
    "central": "192.168.0.42:666",
    "tenant_admin": "zhaoxin",
    "auth_type": "password",
    "password": "admin!11",
    "asset_sync": 1,
    "asset_count": 100,
    "enable": 1
}
```

---

# EDR 安装路径

## 获取 EDR 安装路径

**端点**: `GET /api/edr-install`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 是 | 语言（cn：中文，en：英文） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| edr_install_url | String | 用户定义EDR安装路径 |

**响应示例**:

```json
{
    "data": [{
        "edr_install_url": ""
    }],
    "total": 1
}
```

---

## 修改 EDR 安装路径

**端点**: `PUT /api/edr-install`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| edr_install_url | String | 是 | 用户定义EDR安装路径 |

**请求示例**:

```json
{
    "edr_install_url": "http://www.sunyainfo/bbbb/aaa/abc.exe"
}
```

---

# EDR 联动策略

## 获取 EDR 联动列表

**端点**: `GET /api/edr-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 是 | 语言（cn：中文，en：英文） |
| page | Number | 是 | 当前页数，缺省为1 |
| pageSize | Number | 是 | 页码，缺省为10000000 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | Number | EDR联动策略ID |
| enable | Number | 启用（1：开启，0：关闭） |
| addr_src | String | 源地址 |
| addr_dst | String | 目的地址 |
| action | Number | 动作（1：始终允许，2：EDR管控并允许，3：EDR管控） |

**响应示例**:

```json
{
    "data": [{
        "id": "3",
        "enable": "1",
        "addr_src": "any",
        "addr_dst": "ISP_CTT.dat",
        "action": "1"
    }],
    "total": 1
}
```

---

## 新建 EDR 联动策略

**端点**: `POST /api/edr-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | ID字段，必填字段，自增长填写0 |
| enable | Number | 是 | 启用（1：开启，0：关闭，缺省为0） |
| addr_src | String | 否 | 源地址 |
| addr_dst | String | 否 | 目的地址 |
| action | Number | 是 | 动作（1：始终允许，2：EDR管控并允许，3：EDR管控，缺省为1） |

**请求示例**:

```json
{
    "id": 0,
    "enable": 1,
    "action": 1,
    "addr_src": "any",
    "addr_dst": "any"
}
```

---

## 修改 EDR 联动策略

**端点**: `PUT /api/edr-policy`

**请求参数**: 同新建EDR联动策略

---

## 删除 EDR 联动策略

**端点**: `DELETE /api/edr-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | ID字段，必填字段，自增长填写0 |

**请求示例**:

```json
{
    "id": 1
}
```

---

## 移动 EDR 联动策略

**端点**: `PUT /api/edr-policy`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 否 | 移动策略ID字段，必填 |
| move | Number | 是 | 移动操作（1：移动策略之前，2：移动策略之后） |
| dst_id | String | 否 | 目标策略ID |

**请求示例**:

```json
{
    "id": 2,
    "move": 2,
    "dst_id": 4
}
```

---

## 获取 EDR 联动 HTTPS 触发

**端点**: `GET /api/edr-https`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 是 | 语言（cn：中文，en：英文） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | Number | HTTPS触发开启状态（0：关闭，1：开启） |

**响应示例**:

```json
{
    "data": [{
        "status": "0"
    }],
    "total": 1
}
```

---

## 修改 EDR 联动 HTTPS 触发

**端点**: `PUT /api/edr-https`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| status | Number | 否 | HTTPS触发开启状态（0：关闭，1：开启） |

**请求示例**:

```json
{
    "status": "1"
}
```

---

# EDR 资产列表

## 获取 EDR 资产列表

**端点**: `GET /api/edr-user`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 是 | 语言（cn：中文，en：英文） |
| page | Number | 是 | 当前页数，缺省为1 |
| pageSize | Number | 是 | 页码，缺省为10000000 |
| filter_type | String | 是 | 地址类型，可为空，可输入ip4、ip6 |
| filter_address | String | 是 | 过滤地址，根据filter_type字段，查询ipv4或者ipv6地址 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| addr_type | String | 地址类型（ip4、ip6） |
| ipaddr | String | IP地址，根据addr_type展示对应的地址格式 |
| is_infected_virus | Number | 中毒状态（0：未中毒，1：中毒） |
| is_offline | Number | 在线状态（0：在线，1：离线，2：已卸载） |
| is_unavaliable | Number | 可用性（0：可用，1：不可用） |
| need_block | Number | 阻断状态（0：不需要阻断，1：需阻断） |
| os_type | String | 操作系统 |

**响应示例**:

```json
{
    "data": [{
        "ipaddr": "10.23.0.64",
        "addr_type": "ip4",
        "is_unavaliable": "0",
        "is_offline": "2",
        "is_infected_virus": "0",
        "need_block": "0",
        "os_type": "Windows"
    }],
    "total": 1
}
```

---

## 临时放行 EDR 资产

**端点**: `PUT /api/edr-user`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| addr_type | Number | 是 | 地址类型，可为空，可输入ip4、ip6 |
| ipaddr | String | 是 | IP地址，根据addr_type展示对应的地址格式 |

**请求示例**:

```json
{
    "addr_type": "ip4",
    "ipaddr": "10.23.0.203"
}
```

---

## 参数说明

### auth_type 参数说明

| 值 | 说明 |
|----|------|
| password | 开启密码认证 |
| none | 关闭密码认证 |

### action 参数说明

| 值 | 说明 |
|----|------|
| 1 | 始终允许 |
| 2 | EDR管控并允许 |
| 3 | EDR管控 |

### move 参数说明

| 值 | 说明 |
|----|------|
| 1 | 移动策略之前 |
| 2 | 移动策略之后 |

### is_offline 参数说明

| 值 | 说明 |
|----|------|
| 0 | 在线 |
| 1 | 离线 |
| 2 | 已卸载 |

### is_infected_virus 参数说明

| 值 | 说明 |
|----|------|
| 0 | 未中毒 |
| 1 | 中毒 |

### need_block 参数说明

| 值 | 说明 |
|----|------|
| 0 | 不需要阻断 |
| 1 | 需阻断 |

### is_unavaliable 参数说明

| 值 | 说明 |
|----|------|
| 0 | 可用 |
| 1 | 不可用 |
