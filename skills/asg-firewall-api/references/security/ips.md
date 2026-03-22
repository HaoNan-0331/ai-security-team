# 入侵防护 (IPS)

## 概述

入侵防护模块提供入侵防护模板和事件集的配置管理功能。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **IPS模板** | 获取入侵防护模板配置 | GET | `/api/ips-rule` |
| **IPS模板** | 新建入侵防护模板 | POST | `/api/ips-rule` |
| **IPS模板** | 修改入侵防护模板 | PUT | `/api/ips-rule` |
| **IPS模板** | 删除入侵防护模板 | DELETE | `/api/ips-rule` |
| **事件集** | 获取事件集策略 | GET | `/api/ips-set` |
| **事件集** | 新建事件集策略 | POST | `/api/ips-set` |
| **事件集** | 修改事件集策略 | PUT | `/api/ips-set` |
| **事件集** | 删除事件集策略 | DELETE | `/api/ips-set` |
| **事件集** | 获取事件集详情 | GET | `/api/ips-set-detail` |
| **事件集** | 将预定义事件集添加到入侵防护事件集 | POST | `/api/ips-sig-node` |
| **事件集** | 修改事件集详情 | PUT | `/api/ips-set-detail` |
| **事件集** | 删除事件集详情 | DELETE | `/api/ips-set-detail` |

---

# IPS 模板

## 获取入侵防护模板配置

**端点**: `GET /api/ips-rule`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | Number | 策略ID |
| name | String | 名称（1-63个字符） |
| desc | String | 描述（0-127个字符） |
| set | Number | 事件集类型 |
| log | Number | 日志（0：关闭，1：开启） |
| enable | Number | 是否使能（0：禁用，1：启用） |
| refcnt | Number | 引用计数 |

**响应示例**:

```json
{
    "data": [
        {
            "name": "入侵防护模板1",
            "desc": "111",
            "refcnt": "0",
            "id": "1",
            "enable": "1",
            "log": "1",
            "set": "All"
        }
    ],
    "total": 1
}
```

---

## 新建入侵防护模板

**端点**: `POST /api/ips-rule`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID |
| name | String | 否 | 名称（1-63个字符） |
| desc | String | 是 | 描述（0-127个字符） |
| set | Number | 否 | 事件集类型（All：全部，Common：常规，Application：应用，Attack：攻击） |
| log | Number | 是 | 日志（0：关闭，1：开启，默认为0） |

**请求示例**:

```json
{
    "id": "1",
    "name": "入侵防护模板1",
    "log": "0",
    "desc": "111",
    "set": "Application"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "-1",
    "str": "入侵防护策略的名称入侵防护模板3已经存在"
}
```

---

## 修改入侵防护模板

**端点**: `PUT /api/ips-rule`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID |
| name | String | 否 | 名称（1-63个字符） |
| desc | String | 是 | 描述（0-127个字符） |
| set | Number | 否 | 事件集类型 |
| log | Number | 是 | 日志（0：关闭，1：开启，默认为0） |
| enable | Number | 是 | 是否使能（0：禁用，1：启用） |
| refcnt | Number | 是 | 引用计数 |

**请求示例**:

```json
{
    "id": "1",
    "name": "入侵防护模板1",
    "log": "1",
    "desc": "test-修改",
    "set": "Common",
    "enable": "1"
}
```

---

## 删除入侵防护模板

**端点**: `DELETE /api/ips-rule`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Number | 是 | 策略ID（默认为1） |
| name | String | 是 | 名称（1-63个字符） |

**请求示例**:

```json
{
    "id": "1",
    "name": "入侵防护模板7"
}
```

---

# 事件集

## 获取事件集策略

**端点**: `GET /api/ips-set`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| name | String | 名称（1-63个字符） |
| desc | String | 描述（0-127个字符） |
| member_count | Number | 入侵防护事件数量 |
| protect_level | Number | 防护级别（1：低，2：中，3：高） |
| type | Number | 是否默认（0：默认不可删除，1：自定义可删除） |
| ref | Number | 是否被引用（0：不启用，1：启用） |

**响应示例**:

```json
{
    "data": [
        {
            "name": "All",
            "desc": "最大事件集",
            "protect_level": "1",
            "type": "0",
            "member_count": "3236",
            "ref": "0"
        },
        {
            "name": "Common",
            "desc": "常规事件集",
            "protect_level": "1",
            "type": "0",
            "member_count": "344",
            "ref": "0"
        },
        {
            "name": "Application",
            "desc": "应用事件集",
            "protect_level": "1",
            "type": "0",
            "member_count": "888",
            "ref": "0"
        },
        {
            "name": "Attack",
            "desc": "攻击事件集",
            "protect_level": "1",
            "type": "0",
            "member_count": "577",
            "ref": "0"
        }
    ],
    "total": 4
}
```

---

## 新建事件集策略

**端点**: `POST /api/ips-set`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 名称（1-63个字符） |
| desc | String | 是 | 描述（0-127个字符） |
| protect_level | Number | 否 | 防护级别（1：低，2：中，3：高） |

**请求示例**:

```json
{
    "name": "test1",
    "desc": "test1",
    "protect_level": "1"
}
```

---

## 修改事件集策略

**端点**: `PUT /api/ips-set`

**请求参数**: 同新建事件集策略

---

## 删除事件集策略

**端点**: `DELETE /api/ips-set`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 名称（1-63个字符） |

**请求示例**:

```json
{
    "name": "test1"
}
```

---

## 获取事件集详情

**端点**: `GET /api/ips-set-detail`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| set_name | String | 否 | 入侵防护事件集名称 |
| mode | Number | 否 | 添加模式，固定为3 |
| op | String | 否 | 操作 |
| page | Number | 是 | 分页 |
| pageSize | Number | 是 | 页面数量 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| type_name | String | 名称（1-63个字符） |
| type_name_cn | String | 描述（0-127个字符） |
| num | Number | 入侵防护事件数量 |
| enable | Number | 是否被引用（0：不启用，1：启用） |
| log | Number | 是否开启日志（0：不启用，1：启用） |
| act | Number | 事件动作（0：通过，1：重置，2：丢弃，3：阻断会话，4：阻断源地址） |
| level | Number | 防护等级（0：信息，1：通知，2：警示，3：告警） |
| risk | Number | 风险等级（1：低危，2：中危，3：高危） |
| popularity | Number | 热度 |
| is_capture | Number | 是否开启抓包（0：不开启，1：开启） |

**响应示例**:

```json
{
    "data": [
        {
            "type_name": "CommandExecution",
            "type_name_cn": "命令执行",
            "num": "664",
            "enable": "1",
            "log": "1",
            "act": "0",
            "level": "3",
            "risk": "2",
            "popularity": "4"
        },
        {
            "type_name": "WormVirus",
            "type_name_cn": "蠕虫病毒",
            "num": "165",
            "enable": "1",
            "log": "1",
            "act": "2",
            "level": "2",
            "risk": "3",
            "popularity": "2"
        }
    ],
    "total": 2
}
```

---

## 将预定义事件集添加到入侵防护事件集

**端点**: `POST /api/ips-sig-node`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Member | Array | 否 | 成员列表 |
| Member[].mode_name | String | 否 | 添加事件集成员 |
| Set_name | String | 否 | 入侵防护事件集名称 |
| mode | Number | 否 | 添加模式，添加二级菜单固定为3 |

**请求示例**:

```json
{
    "set_name": "test1",
    "mode": "3",
    "member": [{
        "mode_name": "VulnerabilityScanning"
    }]
}
```

---

## 修改事件集详情

**端点**: `PUT /api/ips-set-detail`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type_name | String | 是 | 事件集名称（1-63个字符） |
| type_name_cn | String | 是 | 事件集中文名称（1-63个字符） |
| num | Number | 是 | 事件集个数 |
| enable | Number | 否 | 是否启用（0：不启用，1：启用） |
| log | Number | 否 | 是否开启日志（0：不启用，1：启用） |
| act | Number | 否 | 动作（0：通过，1：重置，2：丢弃，3：阻断会话，4：阻断源地址） |
| level | Number | 否 | 级别（0：信息，1：通知，2：警示，3：告警） |
| risk | Number | 否 | 风险等级（1：低危，2：中危，3：高危） |
| popularity | Number | 否 | 热度 |
| tb_level | Number | 否 | 菜单级别（1：一级菜单项，2：二级菜单项） |
| mode | Number | 否 | 添加模式，固定为3 |
| mode_name | String | 否 | 事件集名称 |
| set_name | Number | 否 | 事件集策略名称 |
| is_capture | Number | 否 | 是否开启抓包 |

**请求示例**:

```json
{
    "type_name": "InformationDisclosure",
    "type_name_cn": "信息泄露",
    "num": "191",
    "enable": "0",
    "log": "0",
    "act": "0",
    "level": "2",
    "risk": "2",
    "popularity": "3",
    "tb_level": "1",
    "mode": "3",
    "mode_name": "InformationDisclosure",
    "set_name": "test1",
    "is_capture": "0"
}
```

---

## 删除事件集详情

**端点**: `DELETE /api/ips-set-detail`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| set_name | String | 否 | 事件集名称 |
| mode | Number | 否 | 删除模式，固定为3 |
| mode_name | String | 否 | 事件集名称 |

**请求示例**:

```json
{
    "set_name": "test1",
    "mode": "3",
    "mode_name": "VulnerabilityScanning"
}
```

---

## 参数说明

### set 参数说明

| 值 | 说明 |
|----|------|
| All | 全部事件集 |
| Common | 常规事件集 |
| Application | 应用事件集 |
| Attack | 攻击事件集 |

### protect_level 参数说明

| 值 | 说明 |
|----|------|
| 1 | 低 |
| 2 | 中 |
| 3 | 高 |

### act 参数说明

| 值 | 说明 |
|----|------|
| 0 | 通过 |
| 1 | 重置 |
| 2 | 丢弃 |
| 3 | 阻断会话 |
| 4 | 阻断源地址 |

### level 参数说明

| 值 | 说明 |
|----|------|
| 0 | 信息 |
| 1 | 通知 |
| 2 | 警示 |
| 3 | 告警 |

### risk 参数说明

| 值 | 说明 |
|----|------|
| 1 | 低危 |
| 2 | 中危 |
| 3 | 高危 |
