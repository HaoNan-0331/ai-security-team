# SNMP 配置

## 概述

SNMP配置模块提供SNMP服务的配置管理功能。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **SNMP配置** | 修改SNMP配置 | PUT | `/api/snmp-config` |

---

# SNMP 配置

## 修改SNMP配置

**端点**: `PUT /api/snmp-config`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| enable | Number | 是 | SNMP启用状态 |
| trap_addr_ipv6 | String | 是 | Trap6地址 |
| trap_addr | String | 是 | Trap地址 |
| location | String | 是 | 位置 |
| community | String | 是 | 团体名 |
| v1_tag | Number | 是 | 版本号（0：否，1：是） |
| v2c_tag | Number | 是 | 版本号（0：否，1：是） |
| V3_tag | Number | 是 | 版本号（0：否，1：是） |

**请求示例**:

```json
{
    "enable": "1",
    "location": "",
    "trap_addr": "1.1.1.1",
    "trap_addr_ipv6": "1100::1",
    "community": "public",
    "v1_tag": "1",
    "v2c_tag": "1",
    "v3_tag": "1"
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "193",
    "str": "IP地址格式错误"
}
```

---

## 参数说明

### v1_tag 参数说明

| 值 | 说明 |
|----|------|
| 0 | 否 |
| 1 | 是 |

### v2c_tag 参数说明

| 值 | 说明 |
|----|------|
| 0 | 否 |
| 1 | 是 |

### V3_tag 参数说明

| 值 | 说明 |
|----|------|
| 0 | 否 |
| 1 | 是 |
