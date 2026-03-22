# MPLS

## MPLS L2VPN故障排查

由于MPLS L2VPN的报文由内层私网VC标签和外层公网标签构成，转发主要依赖于外层LSP。所以定位故障的思路是：先查VC标签，再查公网标签；先查远程LDP Peer，再查本地LDP Peer。

### 查看LDP Remote Peer是否正常

查看本端PE路由器是否与对端PE正确建立远程LDP Peer关系。

**命令：** `display mpls ldp remote-peer`

例如：通过命令查看，可以确认与远端PE正确建立Remote Peer关系。

```bash
<H3C>display mpls ldp remote-peer
LDP Remote Entity Information
LDP ID: 10.10.10.10:0
Configured Keepalive Timer: 45 Sec
Configured Hello Timer: 45 Sec
Negotiated Hello Timer: 45 Sec
Hello Message Sent/Rcvd: 307/304 (Message Count)
```

### 确认和修改LDP Remote Peer配置

在两端PE上创建ldp remote peer，并配置对端PE的loopback地址。

例如：本端PE上创建ldp remote peer 1，指定对端PE地址为10.10.10.2，命令为`mpls ldp remote-peer 1 remote-ip 10.10.10.2`。

### 查看VC状态是否Up

分别查看两端PE路由器的mpls l2vc连接状态是否Up，本端和远端VC Label是否正确。

**命令：** `display mpls l2vc`

例如：通过命令查看，可以确认VC ID为101的L2VPN状态是否正常。

```bash
<H3C>display mpls l2vc
Total ldp vc: 1, 1 up, 0 down, 0 blocked
VC ID    Transport Client
101      S0/2/1
```

### 确认和修改两端VC ID及端口L2VC配置

在连接CE的端口上配置对端PE的loopback地址和VC ID，而且两端PE的VC ID必须一致。

例如：将本端PE的Serial0/2/1与对端PE(10.10.10.2)建立L2VPN连接，VC ID为101，命令为`mpls l2vc 10.10.10.2 101`。

```bash
<H3C>display current-configuration interface Serial0/2/1
#
interface Serial0/2/1
 mpls l2vc 10.10.10.2 101
#
```

### 查看公网LSP及LDP PEER是否正常

查看整个LSP上的所有设备是否已经为两个PE的loopback地址正确的分配了公网标签，以及LDP Peer是否正常。

**命令：** `display mpls lsp`、`display mpls ldp peer`

例如：通过命令查看，可以确认对端loopback地址10.10.10.2/32的公网标签为1024，LDP Peer状态正常。

```bash
<H3C>display mpls lsp
LSP Information: LDP LSP
FEC              In/Out Label  In/Out IF
10.10.10.2/32    NULL/1024     -/S0/2/0
Vrf Name: -

<H3C>display mpls ldp peer
LDP Peer Information in Public network
Total number of peers: 2
Peer-ID          Transport-Address  Discovery-Source
10.10.10.1:0     10.10.10.1         Serial0/2/0
```

### 确认和修改全局及接口MPLS LDP配置

在两端PE上全局开启MPLS和MPLS LDP，并在接口下配置MPLS和MPLS LDP。

例如：本端PE上设置`mpls lsr-id 10.10.10.10`，全局和接口下开启MPLS和MPLS LDP，命令为`mpls`、`mpls ldp`。

```bash
[H3C] display current-configuration
#
mpls lsr-id 10.10.10.10
mpls
#
mpls ldp
#
interface Serial0/2/0
 mpls
 mpls ldp
#
```

### 查看公网路由是否正确

确认是否在公网LSP途径的所有设备上都存在两端PE的loopback地址精确路由。

**命令：** `display ip routing-table`

例如：通过命令查看，可以确认本端存在去往对端的公网路由10.10.10.2/32，下一跳为192.168.1.2。

```bash
<H3C>display ip routing-table
Routing Tables: Public
Destinations: 12	Routes: 12

Destination/Mask    Proto   Pre   Cost        NextHop         Interface
10.10.10.2/32       OSPF    10    2           192.168.1.2     S0/2/0
```

### 确认和修改公网IGP配置及loopback是否可达

是否通过公网IGP将PE的loopback地址的路由发布出去。

例如：公网IGP使用OSPF，查看OSPF配置，确认已将PE的loopback地址10.10.10.10发布进公网OSPF内。

```bash
[H3C] display current-configuration configuration ospf
#
ospf 1
 area 0.0.0.0
  network 10.10.10.10 0.0.0.0
#
return
```

## BGP/MPLS VPN故障排查

由于BGP/MPLS VPN的报文转发是基于LSP的，而LSP是依附于路由的。所以定位故障的思路是：先查路由、再查标签；先查私网、再查公网。

### 查看VPN实例路由

分别查看两端PE路由器的vpn-instance中是否存在对端PE的VPN路由。

**命令：** `display ip routing-table vpn-instance vpn-instance-name x.x.x.x`

例如：通过命令查看，可以确认存在对端PE的VPN路由200.200.200.200/32，下一跳是3.3.3.3。

```bash
[H3C]display ip routing-table vpn-instance vpn1 200.200.200.200
Routing Tables: vpn1
Destinations: 1	Routes: 1

Destination/Mask        Proto   Pre   Cost        NextHop         Interface
200.200.200.200/32      BGP     255   0           3.3.3.3         Vlan100
```

### 查看BGP VPNv4路由

查看本端PE路由器是否已经正确获得BGP VPNv4路由。

**命令：** `display bgp vpnv4 all routing-table x.x.x.x <0-32>`

例如：通过命令查看，可以确认已获得VPNv4路由200.200.200.200，且私网标签为1025。

```bash
[H3C]display bgp vpnv4 all routing-table 200.200.200.200 32
BGP Local router ID is 1.1.1.1
Status codes: * - valid, > - best, d - damped,
h - history, i - internal, s - suppressed, S - Stale
Origin: i - IGP, e - EGP, ? - incomplete

 Network          NextHop         MED    LocPrf    PrefVal   Path/Ogn
*>i 200.200.200.200/32 3.3.3.3        0       100       0        100?
```

### 查看MP-BGP邻居

确认邻居状态机是否达到Established状态。

**命令：** `display bgp vpnv4 all peer`

例如：通过命令查看，可以确认本端AS100内BGP邻居3.3.3.3状态已为Established。

```bash
<H3C>display bgp vpnv4 all peer
BGP local router ID: 1.1.1.1
Local AS number: 100
Total number of peers: 1	Peers in established state: 1
Peer            AS    MsgRcvd    MsgSent    OutQ    PrefRcvd    Up/Down
3.3.3.3         100   17         13         0       100         100:12:36
```

### 查看公网路由

确认是否在公网LSP途径的所有设备上都存在对端PE的loopback地址的精确路由（必须是32位掩码）。

**命令：** `display ip routing-table`

例如：通过命令查看，可以确认本端存在去往对端的公网路由3.3.3.3/32，下一跳为192.168.1.2。

```bash
<H3C>display ip routing-table
Routing Tables: Public
Destinations: 12	Routes: 12

Destination/Mask    Proto   Pre   Cost        NextHop         Interface
3.3.3.3/32          OSPF    10    4686        192.168.1.2     S0/2/0
```

### 查看BGP配置

确认在VPNv4地址族下是否正确配置了BGP邻居关系。

**命令：** `display current-configuration configuration bgp`

例如：
```bash
<H3C>display current-configuration configuration bgp
#
bgp 100
 undo synchronization
 peer 3.3.3.3 as-number 100
 peer 3.3.3.3 connect-interface LoopBack0
#
 ipv4-family vpnv4
  peer 3.3.3.3 enable
#
```

### 检查本地VPN实例RT配置

检查本地VPN实例配置中RT是否配置匹配。

**命令：** `display this` (VPN实例地址族下执行)

例如：
```bash
[H3C-vpn-instance-vpn1] display this
#
ip vpn-instance vpn1
 route-distinguisher 100:1
 vpn-target 100:1 export-extcommunity
 vpn-target 100:1 import-extcommunity
#
return
```

### 检查对端PE与CE之间的路由协议

查看对于每个vpn-instance，是否将该vpn-instance的路由引入到MP-BGP中。

**命令：** `display this` (BGP视图下)

例如：将vpn-instance vpn1的OSPF路由引入到MP-BGP中。

```bash
[H3C-bgp] display this
#
peer 1.1.1.1 as-number 100
#
 ipv4-family vpnv4
#
 ipv4-family vpn-instance vpn1
  import-route ospf 100
#
```

### 检查公网IGP配置

是否通过公网IGP将PE的loopback地址的路由发布出去。

**命令：** `display current-configuration configuration ospf`

例如：公网IGP使用OSPF，查看OSPF配置，可以确认已将PE的loopback地址1.1.1.1发布进公网OSPF内。

```bash
[H3C] display current-configuration configuration ospf
#
ospf 1
 area 0.0.0.0
  network 1.1.1.1 0.0.0.0
#
return
```

### 查看公网标签

查看整个LSP上的所有设备是否已经为两个PE的loopback地址正确的分配了公网标签。

**命令：** `display mpls lsp include x.x.x.x <0-32>`

例如：通过命令查看，可以确认已正确分配公网标签1026。

```bash
<H3C>display mpls lsp include 3.3.3.3 32
LSP Information: LDP LSP
FEC              In/Out Label  In/Out IF
3.3.3.3/32       NULL/1026     -/S0/2/0
Vrf Name: -
```

### 查看LDP会话关系

查看两台相邻的PE或P路由器之间是否正确建立了LDP邻居会话关系。

**命令：** `display mpls ldp session x.x.x.x`

例如：通过命令查看，可以确认本端已存在LDP邻居3.3.3.3:0。

```bash
<H3C>display mpls ldp session 3.3.3.3
LDP Session Information in Public network
Peer-ID         State        LagRole Role
3.3.3.3:0      Operational  Active   Passive
```

### 检查MPLS及LDP配置

查看该设备是否在全局使能了MPLS和LDP，以及在相应的接口上使能了LDP。

**命令：** `display current-configuration`

例如：
```bash
[H3C] display current-configuration
#
mpls lsr-id 1.1.1.1
mpls
#
mpls ldp
#
interface Vlan-interface100
 mpls
 mpls ldp
#
```
