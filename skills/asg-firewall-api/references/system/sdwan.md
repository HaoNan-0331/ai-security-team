# SD-WAN

## 概述

SD-WAN模块提供SD-WAN云平台连接功能的配置管理。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| **SD-WAN配置** | 获取SD-WAN配置 | GET | `/api/cloud-agent` |
| **SD-WAN配置** | 修改SD-WAN配置 | PUT | `/api/cloud-agent` |

---

# SD-WAN 配置

## 获取SD-WAN配置

**端点**: `GET /api/cloud-agent`

**请求参数**: 无

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| Version | Number | 云平台版本 |
| Enable | Number | 云平台启用状态 |
| Log_state | Number | 上报日志状态 |
| Bind_code | String | 绑定码 |
| mwan | String | 上线接口 |
| mwan1 | String | 上线接口 |
| Alive_cycle | Number | 状态上报间隔 |
| Curr_state | String | 状态 |
| Cloud_domain | String | 域 |
| Cloud_ip | String | 云平台地址 |
| Cloud_port | Number | 云平台端口 |

**响应示例**:

```json
{
    "data": [
        {
            "version": "3",
            "enable": "1",
            "bind_code": "73aab29485f24b07af79a1022222222",
            "cloud_domain": "www.123.com",
            "cloud_ip": "::",
            "cloud_port": "2000",
            "alive_cycle": "20",
            "curr_state": "DNS_resolving",
            "log_state": "1",
            "mwan": "ge0/1",
            "mwan1": "ge0/3"
        }
    ],
    "total": 1
}
```

---

## 修改SD-WAN配置

**端点**: `PUT /api/cloud-agent`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Version | Number | 是 | 云平台版本 |
| Enable | Number | 是 | 云平台启用状态 |
| Log_state | Number | 是 | 上报日志状态 |
| Bind_code | String | 是 | 绑定码 |
| mwan | String | 否 | 上线接口 |
| mwan1 | String | 否 | 上线接口 |
| Alive_cycle | Number | 是 | 状态上报间隔 |
| Curr_state | String | 是 | 状态 |
| Cloud_domain | String | 否 | 域 |
| Cloud_ip | String | 是 | 云平台地址 |
| Cloud_port | Number | 是 | 云平台端口 |

**请求示例**:

```json
{
    "cloud_domain": "172.17.130.93",
    "mwan": "ge0/1",
    "mwan1": "ge0/5",
    "enable": 1,
    "bind_code": "aed995e7ce694c4287d9cd512e3d3229",
    "alive_cycle": 1,
    "log_state": "1"
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
