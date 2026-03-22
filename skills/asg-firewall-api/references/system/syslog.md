# Syslog 日志加密传输

## 概述

Syslog日志加密传输模块提供Syslog服务器配置和加密传输功能的配置管理。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **Syslog服务器** | 获取syslog日志加密 | GET | `/api/syslog-server` |
| **Syslog服务器** | 修改syslog日志加密 | PUT | `/api/syslog-server` |
| **Syslog对接标准** | 查询syslog对接标准 | GET | `/api/syslog-docking` |
| **Syslog对接标准** | 修改syslog对接标准 | PUT | `/api/syslog-docking` |

---

# Syslog 服务器配置

## 获取syslog日志加密

**端点**: `GET /api/syslog-server`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 是 | 语言（cn：中文，en：英文） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| syslog_csv | Number | 启用syslog服务器（缺省为0：1为开启，0为关闭） |
| syslog_tls | Number | 服务器1加密传输（缺省为0，1为开启，0为关闭） |
| syslog_addr | String | 服务器1ip地址，可为空 |
| syslog_port | String | 服务器1端口 |
| syslog_sec_tls | Number | 服务器2加密传输（缺省为0，1为开启，0为关闭） |
| syslog_sec_addr | String | 服务器2ip地址，可为空 |
| syslog_sec_port | Number | 服务器2端口 |
| syslog_thi_tls | Number | 服务器3加密传输（缺省为0，1为开启，0为关闭） |
| syslog_thi_location | String | 服务器3ip地址，可为空 |
| syslog_thi_port | Number | 服务器3端口 |

**响应示例**:

```json
{
    "data": [
        {
            "syslog_location": "3.3.3.3",
            "syslog_port": "514",
            "syslog_tls": "1",
            "syslog_sec_location": "4.4.4.4",
            "syslog_sec_port": "514",
            "syslog_sec_tls": "1",
            "syslog_thi_location": "5.5.5.5",
            "syslog_thi_port": "514",
            "syslog_thi_tls": "1",
            "syslog_csv": "1"
        }
    ],
    "total": 1
}
```

---

## 修改syslog日志加密

**端点**: `PUT /api/syslog-server`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| syslog_csv | Number | 是 | 启用syslog服务器（缺省为0：1为开启，0为关闭） |
| syslog_tls | Number | 是 | 服务器1加密传输（缺省为0，1为开启，0为关闭） |
| syslog_addr | String | 是 | 服务器1ip地址 |
| syslog_port | String | 否 | 服务器1端口 |
| syslog_sec_tls | Number | 是 | 服务器2加密传输（缺省为0，1为开启，0为关闭） |
| syslog_sec_addr | String | 是 | 服务器2ip地址 |
| syslog_sec_port | Number | 否 | 服务器2端口 |
| syslog_thi_tls | Number | 是 | 服务器3加密传输（缺省为0，1为开启，0为关闭） |
| syslog_thi_location | String | 是 | 服务器3ip地址 |
| syslog_thi_port | Number | 否 | 服务器3端口 |

**请求示例**:

```json
{
    "syslog_location": "3.3.3.3",
    "syslog_port": 514,
    "syslog_tls": 1,
    "syslog_sec_location": "4.4.4.4",
    "syslog_sec_port": 514,
    "syslog_sec_tls": 1,
    "syslog_thi_location": "5.5.5.5",
    "syslog_thi_port": 514,
    "syslog_thi_tls": 1,
    "syslog_csv": 1
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "50",
    "str": "IP地址错误"
}
```

---

# Syslog 对接标准

## 查询syslog对接标准

**端点**: `GET /api/syslog-docking`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lang | String | 是 | 语言（cn：中文，en：英文） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| docking_firm | Number | 对接标准 |

**响应示例**:

```json
{
    "data": [
        {
            "docking_firm": "0"
        }
    ],
    "total": 1
}
```

---

## 修改syslog对接标准

**端点**: `PUT /api/syslog-docking`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| docking_firm | Number | 是 | 对接标准 |

**请求示例**:

```json
{
    "docking_firm": 2
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

## 参数说明

### syslog_csv 参数说明

| 值 | 说明 |
|----|------|
| 0 | 关闭 |
| 1 | 开启 |

### syslog_tls 参数说明

| 值 | 说明 |
|----|------|
| 0 | 关闭 |
| 1 | 开启 |

### docking_firm 参数说明

| 值 | 说明 |
|----|------|
| 0 | 默认 |
| 1 | 中国电信 |
| 2 | 国电网防火墙 |
| 3 | 国电网IDS |
