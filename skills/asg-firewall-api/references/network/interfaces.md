# 网络接口配置

## 概述

网络接口模块提供各种网络接口的配置管理功能，包括 VLAN 接口、GRE 隧道接口、环回接口、旁路部署和端口镜像。

## API 端点汇总

| 接口类型 | 功能 | 方法 | 端点 |
|----------|------|------|------|
| **VLAN** | 获取VLAN接口 | GET | `/api/interfaces-vlan` |
| **VLAN** | 新建VLAN接口 | POST | `/api/interfaces-vlan` |
| **VLAN** | 删除VLAN接口 | DELETE | `/api/interfaces-vlan` |
| **GRE** | 获取GRE接口配置 | GET | `/api/gre-interface` |
| **GRE** | 新建GRE接口配置 | POST | `/api/gre-interface` |
| **GRE** | 修改GRE接口配置 | PUT | `/api/gre-interface` |
| **GRE** | 删除GRE接口配置 | DELETE | `/api/gre-interface` |
| **环回IPv4** | 获取IPv4环回接口 | GET | `/api/loopback-ipv4` |
| **环回IPv4** | 新建IPv4环回接口 | POST | `/api/loopback-ipv4` |
| **环回IPv4** | 修改IPv4环回接口 | PUT | `/api/loopback-ipv4` |
| **环回IPv4** | 删除IPv4环回接口 | DELETE | `/api/loopback-ipv4` |
| **环回IPv6** | 获取IPv6环回接口 | GET | `/api/loopback-ipv6` |
| **环回IPv6** | 新建IPv6环回接口 | POST | `/api/loopback-ipv6` |
| **环回IPv6** | 编辑IPv6环回接口 | PUT | `/api/loopback-ipv6` |
| **环回IPv6** | 删除IPv6环回接口 | DELETE | `/api/loopback-ipv6` |
| **旁路部署** | 查询旁路部署配置 | GET | `/api/listen-interface` |
| **旁路部署** | 修改旁路部署配置 | PUT | `/api/listen-interface` |
| **旁路部署** | 获取旁路部署用户识别参数 | GET | `/api/user-recognition` |
| **旁路部署** | 修改旁路部署用户识别参数 | PUT | `/api/user-recognition` |
| **端口镜像** | 新建端口镜像 | POST | `/api/flow-mirror` |
| **端口镜像** | 编辑端口镜像 | PUT | `/api/flow-mirror` |
| **端口镜像** | 显示端口镜像 | GET | `/api/flow-mirror` |
| **端口镜像** | 删除端口镜像 | DELETE | `/api/flow-mirror` |

---

# VLAN 接口

## 获取 VLAN 接口

**端点**: `GET /api/interfaces-vlan`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| vlan_name | String | VLAN接口名称，范围（1-63） |
| vlan_tag | Number | VLAN接口ID，范围（1-4094） |
| shut | Number | 接口管理状态（1：关闭，0：开启） |
| status | Number | 状态（1：关闭，0：开启） |
| mtu | Number | MTU，范围（1280-1500，默认1280） |
| tagged_if_list | Array | 以tag模式加入vlan的接口列表 |
| tagged_if_list[].ifname | String | 接口名称 |
| untagged_if_list | Array | 以untag模式加入vlan的接口列表 |
| untagged_if_list[].ifname | String | 接口名称 |
| count | Number | 总数 |
| stp_enable | Number | 是否开启STP功能（1：开启，0：关闭） |
| stp_bridge_priority | Number | 桥优先级，范围（0-61440） |
| stp_hello_time | Number | Hello时间，范围（2-10） |
| stp_max_age | Number | 老化时间，范围（6-40） |
| port_forward_delay | Number | 端口状态延时，范围（4-30） |
| address_type | Number | 接口地址类型（1：静态，2：DHCP，3：PPPoE） |
| tb_interface_ip | Array | 接口IP地址，group形式 |
| tb_interface_ip[].tb_ip | String | 接口实际IP地址 |
| tb_interface_ip[].is_floating_ip | Number | 是否浮动IP（1：是，0：否） |
| tb_interface_ip[].unit_id | Number | Unit ID（为空，1，2） |
| tb_interface_ip[].tb_ip_version | Number | IP地址版本，4：IPv4地址，6：IPv6地址 |
| http | Number | 接口访问控制，能否以HTTP的形式访问（1：开启，0：关闭） |
| https | Number | 接口访问控制，能否以HTTPS的形式访问 |
| ping | Number | 接口访问控制，能否以PING的形式访问 |
| telnet | Number | 接口访问控制，能否以TELNET的形式访问 |
| ssh | Number | 接口访问控制，能否以SSH的形式访问 |
| bgp | Number | 接口访问控制，能否以BGP的形式访问 |
| ospf | Number | 接口访问控制，能否以OSPF的形式访问 |
| rip | Number | 接口访问控制，能否以RIP的形式访问 |
| dns | Number | 接口访问控制，能否以DNS的形式访问 |
| sslvpn | Number | 接口访问控制，能否以SSLVPN的形式访问 |
| tctrl | Number | 接口访问控制，能否以TCTRL的形式访问 |
| webauth | Number | 接口访问控制，能否以WEBAUTH的形式访问 |
| linkage | Number | 接口访问控制，能否以LINKAGE的形式访问 |
| vid_transparent | Number | 是否开启VLAN透传（1：开启，0：关闭，默认为0） |

**响应示例**:

```json
{
    "data": [
        {
            "vlan_name": "vlan1",
            "vlan_tag": "1",
            "shut": "0",
            "status": "0",
            "mtu": "1500",
            "tagged_if_list": "",
            "untagged_if_list": {
                "group": [
                    {
                        "ifname": "ge0/4"
                    },
                    {
                        "ifname": "ge0/3"
                    }
                ]
            },
            "count": "0",
            "stp_enable": "1",
            "stp_bridge_priority": "32768",
            "stp_hello_time": "2",
            "stp_max_age": "20",
            "port_forward_delay": "15",
            "address_type": "1",
            "tb_interface_ip": {
                "group": {
                    "tb_ip": "1.1.1.1/24",
                    "is_floating_ip": "1",
                    "unit_id": "1",
                    "tb_ip_version": "4"
                }
            },
            "http": "1",
            "https": "1",
            "ping": "1",
            "telnet": "1",
            "ssh": "1",
            "bgp": "1",
            "ospf": "1",
            "rip": "1",
            "dns": "1",
            "sslvpn": "1",
            "tctrl": "1",
            "webauth": "1",
            "linkage": "1",
            "vid_transparent": "1"
        }
    ],
    "total": 1
}
```

---

## 新建 VLAN 接口

**端点**: `POST /api/interfaces-vlan`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| vlan_name | String | 是 | VLAN接口名称，范围（1-63） |
| vlan_tag | Number | 是 | VLAN接口ID，范围（1-4094） |
| shut | Number | 否 | 接口管理状态（1：关闭，0：开启） |
| status | Number | 否 | 接口状态（1：接口up，0：接口down） |
| mtu | Number | 否 | MTU，范围（1280-1500，默认1280） |
| tagged_if_list | Array | 否 | 以tag模式加入vlan的接口列表 |
| untagged_if_list | Array | 否 | 以untag模式加入vlan的接口列表 |
| stp_enable | Number | 是 | 是否开启STP功能（1：开启，0：关闭） |
| stp_bridge_priority | Number | 是 | 桥优先级，范围（0-61440） |
| stp_hello_time | Number | 是 | Hello时间，范围（2-10） |
| stp_max_age | Number | 是 | 老化时间，范围（6-40） |
| port_forward_delay | Number | 是 | 端口状态延时，范围（4-30） |
| address_type | Number | 否 | 接口地址类型（1：静态，2：DHCP，3：PPPoE） |
| tb_interface_ip | Array | 否 | 接口IP地址，group形式 |
| http | Number | 否 | 接口访问控制（1：开启，0：关闭，默认为1） |
| https | Number | 否 | 接口访问控制（默认为1） |
| ping | Number | 否 | 接口访问控制（默认为1） |
| telnet | Number | 否 | 接口访问控制（默认为1） |
| ssh | Number | 否 | 接口访问控制（默认为1） |
| bgp | Number | 否 | 接口访问控制（默认为1） |
| ospf | Number | 否 | 接口访问控制（默认为1） |
| rip | Number | 否 | 接口访问控制（默认为1） |
| dns | Number | 否 | 接口访问控制（默认为1） |
| sslvpn | Number | 否 | 接口访问控制（默认为1） |
| tctrl | Number | 否 | 接口访问控制（默认为1） |
| webauth | Number | 否 | 接口访问控制（默认为1） |
| linkage | Number | 否 | 接口访问控制（默认为1） |
| vid_transparent | Number | 否 | 是否开启VLAN透传（1：开启，0：关闭，默认为0） |

**请求示例**:

```json
{
    "vlan_name": "vlan1",
    "vlan_tag": "",
    "shut": "0",
    "status": "0",
    "mtu": "1500",
    "tagged_if_list": [{"ifname": "ge0/3"}],
    "untagged_if_list": [{"ifname": "ge0/4"}],
    "count": "0",
    "stp_enable": "1",
    "stp_bridge_priority": "32768",
    "stp_hello_time": "2",
    "stp_max_age": "20",
    "port_forward_delay": "15",
    "address_type": "1",
    "tb_interface_ip": [{
        "tb_ip": "1.1.1.1/24",
        "is_floating_ip": "1",
        "unit_id": "1",
        "tb_ip_version": "4"
    }],
    "http": "0",
    "https": "1",
    "ping": "1",
    "telnet": "1",
    "ssh": "1",
    "bgp": "1",
    "ospf": "1",
    "rip": "1",
    "dns": "1",
    "sslvpn": "1",
    "tctrl": "1",
    "webauth": "1",
    "linkage": "1",
    "vid_transparent": "0"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "631",
    "str": "VLAN ID已被使用"
}
```

---

## 删除 VLAN 接口

**端点**: `DELETE /api/interfaces-vlan`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| vlan_name | String | 否 | VLAN接口名称，范围（1-63） |
| vlan_tag | Number | 是 | VLAN接口ID，范围（1-4094） |

**请求示例**:

```json
{
    "vlan_name": "vlan1",
    "vlan_tag": "1"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "10",
    "str": "接口不存在"
}
```

---

# GRE 隧道接口

## 获取 GRE 接口配置

**端点**: `GET /api/gre-interface`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| gre_num | Number | GRE接口ID，范围（0-2047） |
| name | String | GRE接口名称，范围（1-63） |
| ipaddr | String | GRE接口地址 |
| source_type | Number | 隧道源类型（接口：0，地址：1） |
| source_if | String | 隧道源接口名 |
| source | String | 隧道源地址 |
| dymatic | Number | 标识目的地址类型是否为dymatic（是：1，否：0） |
| dst_ip | String | 隧道目的IP |
| tunnel_id | Number | 隧道标识，范围（1-9999） |
| keep_alive | Number | Keepalive报文间隔时间，单位秒，范围（1-86400） |
| ttl | Number | 生存时间值，范围（0-255） |
| shut | Number | 接口管理状态（1：管理down，0：管理up） |
| mtu | Number | MTU，范围（1280-1420） |
| count | Number | 标识接口是否被引用 |

**响应示例**:

```json
{
    "data": [
        {
            "gre_num": "1",
            "name": "gre-1",
            "ipaddr": "1.1.1.1/24",
            "source_type": "0",
            "source_if": "ge0/5",
            "dymatic": "0",
            "dst_ip": "1.1.1.2",
            "tunnel_id": "88",
            "keep_alive": "88",
            "ttl": "88",
            "shut": "0",
            "mtu": "1420",
            "count": "0"
        }
    ],
    "total": 1
}
```

---

## 新建 GRE 接口配置

**端点**: `POST /api/gre-interface`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| gre_num | Number | 是 | GRE接口ID，范围（0-2047，默认为0） |
| name | String | 是 | GRE接口名称，范围（1-63） |
| ipaddr | String | 是 | GRE接口地址 |
| source_type | Number | 否 | 隧道源类型（接口：0，地址：1，默认为0） |
| source_if | String | 是 | 隧道源接口名 |
| source | String | 是 | 隧道源地址 |
| dymatic | Number | 否 | 标识目的地址类型是否为dymatic（是：1，否：0，默认为0） |
| dst_ip | String | 是 | 隧道目的IP |
| tunnel_id | Number | 否 | 隧道标识，范围（1-9999） |
| keep_alive | Number | 否 | Keepalive报文间隔时间，单位秒，范围（1-86400） |
| ttl | Number | 是 | 生存时间值，范围（0-255） |
| shut | Number | 否 | 接口管理状态（1：管理down，0：管理up） |
| mtu | Number | 否 | MTU，范围（1280-1420，默认为1280） |
| count | Number | 否 | 标识接口是否被引用 |

**请求示例**:

```json
{
    "gre_num": "1",
    "name": "gre-1",
    "ipaddr": "1.1.1.1/24",
    "source_type": "0",
    "source_if": "ge0/5",
    "dymatic": "0",
    "dst_ip": "1.1.1.2",
    "tunnel_id": "88",
    "keep_alive": "88",
    "ttl": "88",
    "shut": "0",
    "mtu": "1420",
    "count": "0"
}
```

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "84",
    "str": "别名重复"
}
```

---

## 修改 GRE 接口配置

**端点**: `PUT /api/gre-interface`

**请求参数**: 同新建接口

**响应示例**:

下发正确返回空，下发错误返回code和str：

```json
{
    "code": "250",
    "str": "参数错误"
}
```

---

## 删除 GRE 接口配置

**端点**: `DELETE /api/gre-interface`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| gre_num | String | 是 | GRE接口ID，范围（0-2047） |
| name | Number | 否 | GRE接口名称，范围（1-63） |

**请求示例**:

```json
{
    "gre_num": "1",
    "name": "gre-1"
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

# 环回接口

## 获取 IPv4 环回接口

**端点**: `GET /api/loopback-ipv4?get_type=1`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| is_floating_ip | Number | 是否浮动地址 |
| unit_id | Number | Unit ID |
| vlan_name | String | 环回接口名称 |
| selfip | String | IP地址 |
| mask | String | 掩码 |

**响应示例**:

```json
{
    "data": [
        {
            "selfip": "4.4.4.4",
            "mask": "255.255.255.255",
            "vlan_name": "lo",
            "is_floating_ip": "",
            "unit_id": ""
        }
    ],
    "total": 1
}
```

---

## 新建 IPv4 环回接口

**端点**: `POST /api/loopback-ipv4`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| is_floating_ip | Number | 否 | 是否浮动地址 |
| get_type | Number | 是 | 类型 |
| vlan_name | String | 是 | 环回接口名称 |
| selfip | String | 是 | IP地址 |
| mask | String | 是 | 掩码 |

**请求示例**:

```json
{
    "is_floating_ip": "0",
    "get_type": "1",
    "vlan_name": "lo",
    "selfip": "7.7.6.7",
    "mask": "255.255.255.0"
}
```

---

## 修改 IPv4 环回接口

**端点**: `PUT /api/loopback-ipv4`

**请求参数**: 同新建接口

---

## 删除 IPv4 环回接口

**端点**: `DELETE /api/loopback-ipv4`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| vlan_name | String | 是 | 环回接口名称 |
| selfip | String | 是 | IP地址 |
| mask | String | 是 | 掩码 |

**请求示例**:

```json
{
    "vlan_name": "lo",
    "selfip": "7.7.6.7",
    "mask": "255.255.0.0"
}
```

---

## 获取 IPv6 环回接口

**端点**: `GET /api/loopback-ipv6?get_type=1`

**响应示例**:

```json
{
    "data": [
        {
            "selfip": "2000::1/128",
            "vlan_name": "lo",
            "is_floating_ip": "",
            "unit_id": ""
        }
    ],
    "total": 1
}
```

---

## 新建 IPv6 环回接口

**端点**: `POST /api/loopback-ipv6`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| vlan_name | String | 是 | 接口名称，"lo" |
| selfip | String | 是 | IPv6地址 |
| get_type | Number | 是 | 值为"1" |
| is_floating_ip | Number | 是 | 浮动IP，"0" |

**请求示例**:

```json
{
    "is_floating_ip": "0",
    "get_type": "1",
    "vlan_name": "lo",
    "selfip": "2000::1:2345:6789:abcd/64"
}
```

---

## 编辑 IPv6 环回接口

**端点**: `PUT /api/loopback-ipv6`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| vlan_name | String | 是 | 接口名称，"lo" |
| selfip | String | 是 | IPv6地址 |
| unit_id | Number | 否 | HA的单元ID |
| is_floating_ip | Number | 否 | 浮动IP |

---

## 删除 IPv6 环回接口

**端点**: `DELETE /api/loopback-ipv6`

**请求参数**: 同编辑接口

---

# 旁路部署

## 查询旁路部署配置

**端点**: `GET /api/listen-interface`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| name | String | 接口名称 |
| listen_mode | String | 旁路功能开关，enable/disable |

**响应示例**:

```json
{
    "data": [
        {
            "name": "ge0/0",
            "listen_mode": "disable"
        },
        {
            "name": "ge0/1",
            "listen_mode": "enable"
        }
    ],
    "total": 2
}
```

---

## 修改旁路部署配置

**端点**: `PUT /api/listen-interface`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 是 | 接口名称 |
| listen_mode | String | 是 | 旁路功能开关，enable/disable |

**请求示例**:

```json
{
    "name": "ge0/3",
    "listen_mode": "enable"
}
```

---

## 获取旁路部署用户识别参数

**端点**: `GET /api/user-recognition`

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| recogs_num | Number | 当前在线用户总数 |
| recog_scope_name | String | 用户识别的有效地址范围 |

**响应示例**:

```json
{
    "data": [
        {
            "recogs_num": "4",
            "recog_scope_name": "addr1"
        }
    ],
    "total": 1
}
```

---

## 修改旁路部署用户识别参数

**端点**: `PUT /api/user-recognition`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| recog_scope_name | String | 是 | 用户识别的有效地址范围 |

**请求示例**:

```json
{
    "recog_scope_name": "test1"
}
```

---

# 端口镜像

## 新建端口镜像

**端点**: `POST /api/flow-mirror`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 是 | 端口镜像的名称 |
| src_ifname | String | 是 | 源端口名称 |
| dst_ifname_list | Array | 是 | 镜像目的端口信息列表 |
| dst_ifname_list[].dst_ifname | String | 是 | 镜像目的端口名称（监控接口） |
| dst_ifname_list[].direction | String | 是 | 方向（1：入流量，2：出流量，3：双向流量） |

**请求示例**:

```json
{
    "name": "test_mirror",
    "src_ifname": "ge0/3",
    "dst_ifname_list": [{
        "dst_ifname": "ge0/2",
        "direction": "2"
    }]
}
```

**响应示例**:

下发正确无返回值，下发错误会提示：

```json
{
    "code": "-1",
    "str": "端口镜像名称已存在"
}
```

---

## 编辑端口镜像

**端点**: `PUT /api/flow-mirror`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | String | 是 | 名称 |
| src_ifname | String | 是 | 源接口 |
| count | Number | 是 | 端口镜像数量 |
| dst_ifname_list | Array | 是 | 镜像接口列表 |
| dst_ifname_list[].dst_ifname | String | 是 | 镜像接口 |
| dst_ifname_list[].direction | Number | 是 | 规则类型，1：入流量，2：出流量，3：双向流量 |

**请求示例**:

```json
{
    "name": "test",
    "src_ifname": "ge0/0",
    "dst_ifname_list": [{
        "dst_ifname": "ge0/1",
        "direction": "1"
    }, {
        "dst_ifname": "ge0/2",
        "direction": "2"
    }],
    "count": "1"
}
```

---

## 显示端口镜像

**端点**: `GET /api/flow-mirror`

**响应参数**: 同编辑端口镜像

**响应示例**:

```json
{
    "data": [{
        "name": "test",
        "src_ifname": "ge0/0",
        "dst_ifname_list": {
            "group": [{
                "dst_ifname": "ge0/1",
                "direction": "1"
            }, {
                "dst_ifname": "ge0/2",
                "direction": "3"
            }]
        },
        "count": "1"
    }],
    "total": 1
}
```

---

## 删除端口镜像

**端点**: `DELETE /api/flow-mirror`

**请求参数**: 同编辑端口镜像

**请求示例**:

```json
{
    "name": "test",
    "src_ifname": "ge0/0",
    "dst_ifname_list": [{
        "dst_ifname": "ge0/1",
        "direction": "1"
    }, {
        "dst_ifname": "ge0/2",
        "direction": "2"
    }],
    "count": "1"
}
```

---

## 参数说明

### direction 参数说明

| 值 | 说明 |
|----|------|
| 1 | 入流量（仅镜像进入源端口的流量） |
| 2 | 出流量（仅镜像离开源端口的流量） |
| 3 | 双向流量（镜像进入和离开源端口的所有流量） |

### listen_mode 参数说明

| 值 | 说明 |
|----|------|
| enable | 启用旁路监听模式 |
| disable | 禁用旁路监听模式 |

### source_type 参数说明

| 值 | 说明 |
|----|------|
| 0 | 使用接口作为隧道源 |
| 1 | 使用IP地址作为隧道源 |

### shut 参数说明

| 值 | 说明 |
|----|------|
| 0 | 接口管理状态为开启 |
| 1 | 接口管理状态为关闭 |
