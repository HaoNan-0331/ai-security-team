# IP组播

组播分为二层和三层组播协议，其中，IGMP Snooping是运行在二层设备上的组播约束机制，用于管理和控制组播组，IGMP负责IP组播成员管理，用来在IP主机和与其直接相邻的组播路由器之间建立、维护组播组成员关系，PIM-DM和PIM-SM是运行在路由器之间或三层交换机之间的三层组播路由协议，通过单播路由协议产生相应的组播路由表项。

## IGMP协议故障排查

IGMP协议定位故障的思路是：先查组信息，再查配置，最后查报文。

### 查看IGMP组信息

查看设备的IGMP组信息，可以检查对应接口或VLAN是否作为成员端口加入相应组播组。

例如：通过命令查看，可以确认Vlan-interface101下有IP为10.1.1.2的Host加入组播组225.0.0.1。

**命令：** `display igmp group group-address`

### 查看组是否包含主机接口

查看IGMP跟踪的主机信息，检查组播组是否包含正确的主机接口，需要在全局或接口视图下使能主机跟踪功能。

**命令：** `display igmp host interface interface-type interface-number group group-address`

例如：通过命令查看，可以确认正在接收组播数据的成员主机信息（包括主机的IP地址、运行时间和超时时间等），检查主机是否在GigabitEthernet2/0/18下。

如果想要在设备上查看主机信息，需要在全局或接口下使能主机跟踪功能。

```bash
igmp host-tracking
#
interface GigabitEthernet2/0/18
 igmp host-tracking
#
```

### 检查端口协议报文交互

通过在主机侧抓包，查看当前主机的成员报告报文是否正常发送，设备是否正确回应，协议交互是否正常。

例如：通过设备上debug IGMP的leave和report报文，可以看到设备正常收到主机发来的加入/离开报文。

```bash
<H3C>debugging igmp leave
<H3C>debugging igmp report
<H3C>terminal monitor
Info: Current terminal monitor is on.
<H3C>terminal debugging
Info: Current terminal debugging is on.
```

在主机侧抓包，能抓到对应的主机发出的加入/离开报文。IP为1.1.1.2的主机发出加入报文，组播组地址为225.1.1.1。主机离开时，向本网段所有路由器发出Leave Group报文，目的地址为224.0.0.2。

### 检查IGMP配置

查看路由器上IGMP的版本和参数配置，连接在同一网段的所有路由器最好运行相同版本的IGMP，且参数配置需要一致，否则将导致IGMP组成员关系的混乱。

**命令：** `display igmp interface verbose`

例如：通过命令查看，可以确认当前路由器的IGMP版本为v2，发送IGMP普遍组查询报文的时间间隔为60秒，IGMP其他查询器的存在时间为125秒，IGMP普遍组查询的最大响应时间为10秒。

```bash
display igmp interface verbose

 information of VPN-Instance: public net
 Vlan-interface101(2.1.1.1):
 IGMP is enabled
 Current IGMP version is 2
 Value of query interval for IGMP(in seconds): 60
 Value of other querier present interval for IGMP(in seconds): 125
 Value of maximum query response time for IGMP(in seconds): 10
 Value of last member query interval(in seconds): 1
 Value of startup query interval(in seconds): 15
 Value of startup query count: 2
 General query timer expiry (hours:minutes:seconds): 00:00:20
 Querier for IGMP: 2.1.1.1 (this router)
 IGMP activity: 2 joins, 1 leaves
 Multicast routing on this interface: enabled
 Robustness: 2
 Require-router-alert: disabled
 Fast-leave: disabled
 Ssm-mapping: disabled
 Startup-query-timer-expiry: off
 Other-querier-present-timer-expiry: off
 Proxying interface: None
 Total 1 IGMP Group reported
```

### 检查组播组过滤

确认是否应用了组播组过滤功能，使能该功能的接口将按照ACL规则对收到的IGMP成员关系报告报文进行过滤，只为该规则所允许的组播组维护组成员关系。

例如：通过命令查看，接口下的过滤器配置，有匹配ACL规则号3000的过滤器。

```bash
interface Vlan-interface101
 ip address 2.1.1.1 255.255.255.0
 igmp enable
 igmp group-policy 3000
 pim dm
#
return
```

查看所配置的ACL规则，检查是否将所要实现的组播组进行了过滤。

**命令：** `display acl acl-number`

例如：只需要过滤IP地址为225.0.0.1的组播组。

```bash
[H3C] display acl 3000
Advanced ACL 3000, named -none-, 2 rules,
ACL's step is 5
rule 0 deny ip destination 225.0.0.1 0
rule 5 permit ip
```

### 检查组播组协议报文交互

通过在主机侧抓包，查看当前组播组的查询报文是否正常发送，主机是否回应，协议交互是否正常。

例如：通过设备上debug IGMP的Query报文，可以看到设备正常发出通用查询报文。在主机上抓包，也能看到对应报文。

### 检查PIM配置

如果发现IGMP组正常，主机加入正常，但组播流无法收到的情况，查看是否有PIM路由，检查PIM相关配置。

## IGMP-Snooping协议故障排查

IGMP-Snooping协议定位故障的思路是：先查组信息，再查配置，最后查报文。

### 查看IGMP-Snooping组

查看设备的IGMP-Snooping组信息，可以检查对应接口或VLAN是否作为成员端口加入相应组播组。

例如：通过命令查看，可以确认GE6/0/1端口下有Host加入组播组225.0.0.1，VLAN为100。

**命令：** `display igmp-snooping group vlan vlan-id verbose`

```bash
[H3C]display igmp-snooping group vlan 100 verbose
Total 1 IP Group(s).
Total 1 IP Source(s). Total 1 MAC Group(s).
Port flags: D-Dynamic port, S-Static port, C-Copy port, P-PIM port
Subvlan flags: R-Real VLAN, C-Copy VLAN
Vlan(id):100.
Total 1 IP Group(s). Total 1 IP Source(s). Total 1 MAC Group(s).
Router port unit board: Mask(0x40) Router port(s): total 1 port(s).
GE6/0/2	(D)
IP group(s): the following ip group(s) match to one mac group.
IP group address: 225.0.0.1
(0.0.0.0, 225.0.0.1):
Attribute: Host Board
Host port unit board: Mask(0x40) Host port(s): total 1 port(s).
GE6/0/1	(D)
MAC group(s):
MAC group address: 0100-5e00-0001
Host port unit board: Mask(0x40) Host port(s): total 1 port(s).
GE6/0/1
```

### 查看组是否包含主机接口

查看IGMP-Snooping跟踪的主机信息，检查组播组是否包含正确的主机接口，需要在全局或VLAN内使能主机跟踪功能。

**命令：** `display igmp-snooping host vlan vlan-id group group-address`

例如：通过命令查看，可以确认正在接收组播数据的成员主机信息，检查主机是否在GE6/0/1下。

```bash
[H3C] display igmp-snooping host vlan 100 group 225.0.0.1
Vlan-id: 100
Group address: 225.0.0.1
Host port: GE6/0/1
Uptime: 00:12:54
Expires: 00:03:56
```

如果想要在设备上查看主机信息，需要在全局或VLAN内使能主机跟踪功能。

### 检查端口协议报文交互

通过在主机侧抓包，查看当前主机的成员报告报文是否正常发送，设备是否正确回应，协议交互是否正常。

例如：通过设备上debug IGMP-Snooping报文，可以看到设备收到主机发来的加入/离开报文。

```bash
<H3C>debugging igmp-snooping packet
<H3C>terminal monitor
The current terminal is enabled to display debugging logs.
<H3C>terminal debugging
The current terminal is enabled to display debugging logs.
<H3C>
*Jan 1 01:18:53:125 2011 H3C MCS/7/PACKET: Receive IGMPv2 report packet from port XGE1/0/2 on VLAN 10
*Jan 1 01:18:53:125 2011 H3C MCS/7/PACKET: The IGMP packet which receive from port XGE1/0/2 on VLAN 10 on Main slot, forward it locally.
<H3C>
*Jan 1 01:23:01:672 2011 H3C MCS/7/PACKET: Receive IGMP leave packet from port XGE1/0/2 on VLAN 10
```

在主机侧抓包，能抓到对应的主机发出的加入/离开报文。IP为1.1.1.2的主机发出加入报文，组播组地址为225.1.1.1。主机离开时，向本网段所有路由器发出Leave Group报文，目的地址为224.0.0.2。

### 检查IGMP-Snooping配置

检查设备是否在全局使能了IGMP-Snooping，以及在相应的VLAN中使能了IGMP-Snooping。检查当前IGMP-Snooping版本的配置，是否能够处理主机侧的Report报文。

例如：默认情况下，IGMP-Snooping的版本为2，能够对IGMPv1和IGMPv2的报文进行处理，对IGMPv3的报文则不进行处理，而是在VLAN内将其广播。

**命令：**
```bash
igmp-snooping enable
igmp-snooping version version-number
```

例如：
```bash
[H3C-vlan100]display this
#
vlan 1
#
vlan 100
 igmp-snooping enable
 igmp-snooping version 3
#
return
```

### 检查组播组过滤

检查是否正确应用了组播组策略，在全局或接口视图下查看配置。

**命令：** `igmp-snooping group-policy acl-number [ vlan vlan-list ]`

例如：通过命令查看，配置的组播组策略是否正确。

```bash
[H3C-igmp-snooping]display this
#
igmp-snooping
 group-policy 3000 vlan 100
#
return
```

```bash
[H3C-GigabitEthernet6/0/1] display this
#
interface GigabitEthernet6/0/1
 port link-mode bridge
 port access vlan 100
 igmp-snooping group-policy 3000 vlan 100
```

查看所配置的ACL规则，检查其是否与所要实现的组播组过滤策略相符合。

**命令：** `display acl acl-number`

例如：只需要过滤IP地址为225.0.0.1的组播组。

```bash
[H3C] display acl 3000
Advanced ACL 3000, named -none-, 2 rules,
ACL's step is 5
rule 0 deny ip destination 225.0.0.1 0
rule 5 permit ip
```

### 查看网络有无IGMP查询器

在一个没有三层组播设备的网络中，需要在二层设备上使能IGMP-Snooping查询器，使二层设备能够在数据链路层建立并维护组播转发表项，从而在数据链路层正常转发组播数据。查看全网设备中，是否有一台配置了IGMP的三层组播路由器充当IGMP查询器，或者在二层设备上有查询器配置。

**命令：** `display current-configuration interface Vlan-interface`

例如：在连接二层设备的接口下配置了IGMP。

```bash
[H3C] display current-configuration interface Vlan-interface101
#
interface Vlan-interface101
 ip address 2.1.1.1 255.255.255.0
 igmp enable
#
```

例如：在二层设备上配置了查询器。

```bash
igmp-snooping querier
igmp-snooping general-query source-ip 1.1.1.1
igmp-snooping special-query source-ip 1.1.1.1
#
return
```

### 检查IGMP查询报文源IP地址

对于收到源IP地址为0.0.0.0的查询报文的端口，设备不会将其设置为动态路由器端口，从而影响数据链路层组播转发表项的建立，最终导致组播数据无法正常转发。当由二层设备充当IGMP-Snooping查询器时，可以把IGMP查询报文的源IP地址配置为一个有效的IP地址以避免上述问题的出现。

**命令：**
```bash
igmp-snooping general-query source-ip { ip-address | current-interface }
igmp-snooping special-query source-ip { ip-address | current-interface }
```

例如：通过命令查看，可以确认VLAN内配置了IGMP普遍组和特定组查询报文源IP地址。

```bash
[H3C-vlan10]display this
#
vlan 1
#
vlan 10
 igmp-snooping enable
 igmp-snooping drop-unknown
 igmp-snooping querier
 igmp-snooping general-query source-ip 1.1.1.1
 igmp-snooping special-query source-ip 1.1.1.1
#
return
```

### 检查组播组协议报文交互

通过在主机侧抓包，查看当前组播组的查询报文是否正常发送，主机是否回应，协议交互是否正常。

例如：通过设备上debug IGMP-Snooping报文，可以看到设备正常发出通用查询报文。

```bash
<H3C>
*Jan 1 01:36:06:321 2011 H3C MCS/7/PACKET: Receive IGMPv2 query packet from port XGE1/0/1 on VLAN 10
*Jan 1 01:36:06:554 2011 H3C MCS/7/PACKET: The IGMP packet which receive from port XGE1/0/1 on VLAN 10 on Main slot, forward it locally.
Jan 1 01:36:06:554 2011 H3C MCS/7/PACKET: Broadcast general query packet which receive from port XGE1/0/1 on VLAN 10.
Jan 1 01:36:06:554 2011 H3C MCS/7/PACKET: Succeed in broadcasting the packet on VLAN 10.
```

在主机上抓包，也能看到对应报文。

## PIM-SM协议故障排查

PIM-SM协议定位故障的思路是：先查路由，再查邻居，最后查RP/BSR等配置。

### 查看PIM路由

在PIM-SM中，RPT树开始转发报文后，沿途的组播路由器上都会建立对应的(*,G)表项，并且通过查看组播路由表，如果有接收者加入组播组G，则从RP到接收者侧DR路径上的路由器会在其转发表中生成一个(*,G)表项。

**命令：** `display pim routing-table [ group-address ]`

例如：通过命令查看当前组播路由表，组播流量经过的所有路由器都有组播组225.0.0.1的(S,G)表项存在，从RP到接收者侧DR路径上的所有路由器都有组播组225.0.0.1的(*,G)和(S,G)表项，且上下游接口信息正确。

```bash
[H3C]display pim routing-table 225.0.0.1
VPN-Instance: public net
Total 1 (*,G) entry; 1 (S,G) entry

(*, 225.0.0.1):
 RP: 10.1.1.2 (local)
 Protocol: pim-sm, Flag: WC
 UpTime: 00:02:28
 Upstream interface: Register
 Upstream neighbor: NULL
 RPF prime neighbor: NULL
 Downstream interface(s) information: Total number of downstreams: 1
  1: Vlan-interface101
 Protocol: igmp, UpTime: 00:02:28, Expires: -

(1.1.1.10, 225.0.0.1):
 RP: 10.1.1.2 (local)
 Protocol: pim-sm, Flag: SPT 2MSDP ACT
 UpTime: 00:05:22
 Upstream interface: Vlan-interface100
```

### 检查IGMP配置

检查在需要建立和维护组播组成员关系的接口上是否使能了IGMP。

**命令：** `display current-configuration interface interface-type interface-number`

例如：
```bash
[H3C] display current-configuration interface Vlan-interface101
#
interface Vlan-interface101
 ip address 2.1.1.1 255.255.255.0
 igmp enable
#
return
```

### 检查组播数据过滤配置

检查是否应用了组播数据过滤功能，使能该功能的路由器将按照ACL规则对流经自己的组播数据进行过滤，决定是否继续转发组播数据。

例如：通过命令查看，PIM节点下的过滤配置，有匹配ACL规则号3000的过滤器，未通过匹配的报文会被丢弃。

**命令：** `display this` (PIM视图下)

```bash
[H3C-pim] display this
#
pim
 source-policy 3000
#
return
```

查看所配置的ACL规则，检查是否将所要实现的组播组或邻居进行了过滤。

**命令：** `display acl acl-number`

例如：只需要过滤IP地址为225.0.0.1的组播组。

```bash
[H3C] display acl 3000
Advanced ACL 3000, named -none-, 2 rules,
ACL's step is 5
rule 0 deny ip destination 225.0.0.1 0
rule 5 permit ip
```

### 检查RPF接口和路由一致性

组播数据由直连组播源的第一跳路由器扩散到直连客户端的最后一跳路由器。无论组播数据扩散到哪一台路由器，只有该路由器存在到达组播源的路由，才会创建(S,G)表项。查看组播域内路由器，针对组播源到RP的SPT树，检查是否有到达组播源的路由，检查RPF接口和到达组播源的单播路由的下一跳接口是否一致。针对RP到接收者的RPT树，检查RPF接口和到达RP的单播路由的下一跳接口是否一致。

**命令：** `display ip routing-table ip-address`

例如：通过命令查看，可以确认存在到达组播源的路由1.1.1.0/24，下一跳是10.1.1.1，并且查看PIM路由表，10.1.1.1是RPF邻居接口。

```bash
[H3C]display ip routing-table 1.1.1.0
Destination/Mask    Proto   Pre   Cost        NextHop         Interface
1.1.1.0/24          OSPF    10    2           10.1.1.1        Vlan100

[H3C]display pim routing-table 225.0.0.1
```

### 查看PIM邻居信息

查看路由器上PIM邻居信息，检查RPF邻居是否是PIM邻居。

**命令：** `display pim neighbor`

例如：通过命令查看，可以确认两台设备互联网段上存在PIM邻居，且是RPF邻居。

```bash
[H3C]display pim neighbor
VPN-Instance: public net
Total Number of Neighbors = 1
Interface: Vlan100
Neighbor IP Address: 10.1.1.2
Uptime: 07:07:41
Expires: 00:01:35
DR-Priority: 1
Mode: -
```

### 检查HELLO报文收发

通过在设备上debug，检查PIM Hello报文是否正常交互。

例如：通过debugging命令查看PIM邻居交互报文，可以看到正常发出Hello报文，也能收到邻居发出的Hello报文。

```bash
* May 30 14:18:18:011 2013 H3C PIM/7/NBR: (public net): Option:1, length: 2. (P011730)
* May 30 14:18:35:561 2013 H3C PIM/7/NBR: (public net): PIM ver 2 HEL receiving 2; 1.1.1.2 -> 224.0.0.13 on GigabitEthernet3/0/2 (P011695)
* May 30 14:18:35:581 2013 H3C PIM/7/NBR: (public net): Option: 1, length:2 (P011730)
```

### 检查PIM配置一致性

检查RPF接口和RPF邻居所在路由器的对应接口上是否使能了相同模式的PIM。

**命令：** `display pim interface verbose`

例如：通过命令查看，可以确认相关接口下配置了PIM-SM。

```bash
[H3C] display pim interface verbose
VPN-Instance: public net
Interface: Vlan-interface100, 10.1.1.1
 PIM version: 2
 PIM mode: Sparse
 PIM DR: 10.1.1.2 (local)
 PIM DR Priority (configured): -
 PIM neighbor count: 1
```

### 查看RP信息

RP是PIM-SM的核心，为特定的组服务。网络中可以同时存在多个RP。必须保证所有路由器的RP信息完全一致，并且对于某个特定的组映射到相同的RP，否则必然导致组播数据转发异常。如果使用静态RP机制，必须在全网所有路由器上配置完全相同的静态RP命令。如果通过配置C-RP，通过自举机制动态选举RP，则必须保证C-RP和BSR之间路由可达。

**命令：** `display pim rp-info [ group-address ]`

例如：通过命令查看路由器上的RP信息，可以看到公网实例中组播组225.0.0.1对应的RP地址为10.1.1.1。

```bash
[H3C] display pim rp-info 225.0.0.1
VPN-Instance: public net
 BSR RP Address is: 10.1.1.1
 Priority: 192
 HoldTime: 150
 Uptime: 02:38:20
 Expires: 00:02:11
 RP mapping for this group is: 10.1.1.1 (local host)
```

### 检查BSR信息

在一个PIM-SM域中只能有一个BSR，但需要配置至少一个C-BSR。BSR负责在PIM-SM域中收集并发布RP信息。

**命令：** `display pim bsr-info`

例如：通过命令查看当前路由器上的BSR信息，以及本地配置并生效的C-RP信息。

```bash
[H3C]display pim bsr-info
VPN-Instance: public net
 Elected BSR Address: 10.1.1.1
 Priority: 64
 Hash mask length: 30
 State: Accept Preferred
 Scope: Not scoped
 Uptime: 00:18:00
 Expires: 00:01:59
 Candidate RP: 10.1.1.1
 Priority: 192
 HoldTime: 150
 Interval: 60
 Uptime: 00:00:39
```
