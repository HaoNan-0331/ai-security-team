# SSLVPN 配置

## 概述

SSLVPN 模块提供 SSL VPN 服务的配置、监控和用户绑定管理功能。

## API 端点

| 功能 | 方法 | 端点 |
|------|------|------|
| 修改SSLVPN配置 | PUT | `/api/sslvpn-config` |
| 查询SSLVPN配置 | GET | `/api/sslvpn-config` |
| 查询SSLVPN监控 | GET | `/api/sslvpn-monitor` |
| 清除SSLVPN监控 | DELETE | `/api/sslvpn-monitor` |
| 新建用户绑定 | POST | `/api/sslvpn-userbind` |
| 编辑用户绑定 | PUT | `/api/sslvpn-userbind` |
| 删除用户绑定 | DELETE | `/api/sslvpn-userbind` |
| 查询用户绑定 | GET | `/api/sslvpn-userbind` |
| 查询SSLVPN接口配置 | GET | `/api/sslvpn-tunn-if` |
| 编辑SSLVPN接口配置 | PUT | `/api/sslvpn-tunn-if` |

---

## 修改 SSLVPN 配置

**端点**: `PUT /api/sslvpn-config`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| enable | Number | 是 | 使能/去使能sslvpn功能开关，1：启用，0：禁用 |
| duplicate_cn | Number | 否 | 使能/去使能sslvpn多点登录功能，1：启用，0：禁用 |
| dns1 | String | 否 | DNS1，例如：192.168.0.100 |
| dns2 | String | 否 | DNS2，例如：192.168.0.100 |
| wins1 | String | 否 | WINS1，例如：192.168.0.100 |
| wins2 | String | 否 | WINS2，例如：192.168.0.100 |
| address_pool | String | 否 | 地址池，例如：192.168.0.0/24 |
| gw | String | 是 | 隧道地址，例如：192.168.0.100/24 |
| route_items | Array | 否 | 推送至客户端的路由列表 |
| route_items[].intranet_route | String | 否 | 内网路由，例如：192.168.0.100/24 |

**请求示例**:

```json
{
    "enable": "1",
    "duplicate_cn": "1",
    "gw": "192.10.10.10/24",
    "address_pool": "192.10.10.0/24",
    "dns1": "8.8.8.8",
    "dns2": "114.114.114.114",
    "wins1": "9.9.9.9",
    "route_items": [{
            "intranet_route": "192.11.0.0/16"
        },
        {
            "intranet_route": "192.12.12.0/24"
        }
    ]
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "250",
    "str": "参数错误"
}
```

---

## 查询 SSLVPN 配置

**端点**: `GET /api/sslvpn-config`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| enable | Number | 使能/去使能sslvpn功能开关 |
| duplicate_cn | Number | 使能/去使能sslvpn多点登录功能 |
| dns1 | String | DNS1 |
| dns2 | String | DNS2 |
| wins1 | String | WINS1 |
| wins2 | String | WINS2 |
| address_pool | String | 地址池 |
| gw | String | 隧道地址 |
| route_items | Array | 推送至客户端的路由 |
| route_items[].intranet_route | String | 内网路由 |

**响应示例**:

```json
{
    "data": [
        {
            "dns1": "8.8.8.8",
            "dns2": "114.114.114.114",
            "wins1": "9.9.9.9",
            "wins2": "9.9.9.10",
            "gw": "192.10.10.10/24",
            "route_items": {
                "group": [
                    {
                        "intranet_route": "192.11.0.0/16"
                    },
                    {
                        "intranet_route": "192.12.12.0/24"
                    }
                ]
            },
            "enable": "1",
            "duplicate_cn": "1",
            "address_pool": "192.10.10.0/24"
        }
    ],
    "total": 1
}
```

---

## 查询 SSLVPN 监控

**端点**: `GET /api/sslvpn-monitor`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| name | String | 用户名 |
| ip | String | 接入IP |
| vip | String | 虚拟IP |
| terminaltype | String | 终端类型 |
| terminalid | String | 硬件特征码 |
| online_time | Number | 在线时长（秒） |
| up_bytes | String | 发送字节数 |
| down_bytes | String | 接收字节数 |

**响应示例**:

```json
{
    "data": [
        {
            "name": "test",
            "ip": "36.36.1.2",
            "vip": "8.1.1.2",
            "terminaltype": "Windows64",
            "terminalid": "c4dac045115d77878c9b310cf2914310",
            "online_time": "33",
            "up_bytes": "20.93 KB",
            "down_bytes": "3.24 KB"
        }
    ],
    "total": 1
}
```

---

## 清除 SSLVPN 监控

**端点**: `DELETE /api/sslvpn-monitor`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 否 | 用户名 |
| ip | String | 否 | 接入IP |
| vip | String | 否 | 虚拟IP |

**请求示例**:

```json
{
    "name": "test",
    "ip": "36.36.1.2",
    "vip": "8.1.1.2"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "-22",
    "str": "接口不存在"
}
```

---

## 新建用户绑定

**端点**: `POST /api/sslvpn-userbind`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | String | 是 | 用户名，（1-63）字符，支持中英文大小写、数字以及@._-|()[]字符 |
| bindip | String | 是 | 绑定IP，需在SSLVPN地址池范围内，例如192.168.0.100 |

**请求示例**:

```json
{
    "username": "张三",
    "bindip": "192.10.10.1"
}
```

**响应示例**:

下发成功无返回值，下发错误返回值：

```json
{
    "code": "182",
    "str": "名称中不能包含空格"
}
```

---

## 编辑用户绑定

**端点**: `PUT /api/sslvpn-userbind`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | String | 是 | 用户名，（1-63）字符，支持中英文大小写、数字以及@._-|()[]字符 |
| bindip | String | 是 | 绑定IP，需在SSLVPN地址池范围内，例如192.168.0.100 |

**请求示例**:

```json
{
    "username": "张三",
    "bindip": "192.10.10.2"
}
```

**响应示例**:

下发正确无返回值，下发错误有返回值：

```json
{
    "code": "193",
    "str": "IP地址格式错误"
}
```

---

## 删除用户绑定

**端点**: `DELETE /api/sslvpn-userbind`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | String | 是 | 用户名，（1-63）字符，支持中英文大小写、数字以及@._-|()[]字符 |
| bindip | String | 是 | 绑定IP，需在SSLVPN地址池范围内，例如192.168.0.100 |

**请求示例**:

```json
{
    "username": "张三",
    "bindip": "192.10.10.2"
}
```

**响应示例**:

下发成功无返回值，下发错误返回值：

```json
{
    "code": "182",
    "str": "名称中不能包含空格"
}
```

---

## 查询用户绑定

**端点**: `GET /api/sslvpn-userbind`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| username | String | 用户名 |
| bindip | String | 绑定IP |

**响应示例**:

```json
{
    "data": [
        {
            "username": "张三",
            "bindip": "192.10.10.2"
        }
    ],
    "total": 1
}
```

---

## 查询 SSLVPN 接口配置

**端点**: `GET /api/sslvpn-tunn-if`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| tunn_ifname | String | 接口名称 |
| http | Number | 接口访问控制，能否以 http 的形式访问 |
| https | Number | 接口访问控制，能否以 https 的形式访问 |
| telnet | Number | 接口访问控制，能否以 telnet 的形式访问 |
| ping | Number | 接口访问控制，能否以 ping 的形式访问 |
| ssh | Number | 接口访问控制，能否以 ssh 的形式访问 |
| bgp | Number | 接口访问控制，能否以 bgp 的形式访问 |
| ospf | Number | 接口访问控制，能否以 ospf 的形式访问 |
| rip | Number | 接口访问控制，能否以 rip 的形式访问 |
| dns | Number | 接口访问控制，能否以 dns 的形式访问 |
| webauth | Number | 接口访问控制，能否以 webauth 的形式访问 |

**响应示例**:

```json
{
    "data": [
        {
            "tunn_ifname": "tunl1023",
            "http": "0",
            "https": "0",
            "ping": "0",
            "telnet": "0",
            "ssh": "0",
            "sslvpn": "0",
            "bgp": "0",
            "ospf": "0",
            "rip": "0",
            "dns": "0",
            "webauth": "0"
        }
    ],
    "total": 1
}
```

---

## 编辑 SSLVPN 接口配置

**端点**: `PUT /api/sslvpn-tunn-if`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| tunn_ifname | String | 是 | 接口名称 |
| http | Number | 否 | 接口访问控制，能否以 http 的形式访问 |
| https | Number | 否 | 接口访问控制，能否以 https 的形式访问 |
| telnet | Number | 否 | 接口访问控制，能否以 telnet 的形式访问 |
| ping | Number | 否 | 接口访问控制，能否以 ping 的形式访问 |
| ssh | Number | 否 | 接口访问控制，能否以 ssh 的形式访问 |
| bgp | Number | 否 | 接口访问控制，能否以 bgp 的形式访问 |
| ospf | Number | 否 | 接口访问控制，能否以 ospf 的形式访问 |
| rip | Number | 否 | 接口访问控制，能否以 rip 的形式访问 |
| dns | Number | 否 | 接口访问控制，能否以 dns 的形式访问 |
| webauth | Number | 否 | 接口访问控制，能否以 webauth 的形式访问 |

**请求示例**:

```json
{
    "tunn_ifname": "tunl1023",
    "http": "1",
    "https": "1",
    "ping": "1",
    "telnet": "1",
    "ssh": "1",
    "sslvpn": "0",
    "bgp": "0",
    "ospf": "0",
    "rip": "0",
    "dns": "0",
    "webauth": "0"
}
```

**响应示例**:

下发正确返回空，下发错误返回值：

```json
{
    "code": "250",
    "str": "参数错误"
}
```
