# IP路由

## 静态路由故障排查

静态路由是否能够加入到全局路由表中并成功指导报文正确转发，取决于其出接口状态与下一跳地址可达性，以及相关检测联动的状态等方面。因此静态路由定位故障的思路是：首先查看全局路由表中是否有该静态路由；然后据此相应地检查出接口状态、下一跳地址可达性、BFD/NQA配置、路由优先级等。

### 查看全局路由表中是否有该静态路由

**命令：** `display ip routing-table xxx.xxx.xxx.xxx`（目的IP网段）

例如：通过上述命令查看，可以确认全局路由表中存在该静态路由。

### 检查出接口状态

查看静态路由对应的出接口状态是否正常，正常情况下该接口的物理层状态、协议层状态均为Up。接口状态问题参见接口排错。

**命令：** `display interface brief`

例如：通过上述命令查看，可以确认出接口的物理层和协议层状态均正常。

### 检查下一跳地址可达性

查看静态路由下一跳地址，验证其是否可达。

**命令：** `display ip routing-table protocol static xxx.xxx.xxx.xxx`（目的IP网段）
`ping xxx.xxx.xxx.xxx`（下一跳IP地址）

例如：通过上述命令，可以确认静态路由下一跳地址可达。

### 查看是否绑定BFD或NQA

查看静态路由是否绑定了BFD或NQA，与BFD或NQA检测进行联动。

**命令：** `display current-configuration | include xxx.xxx.xxx.xxx`（目的IP网段）

例如：通过上述命令查看，可以确认静态路由绑定了BFD或NQA。

```bash
ip route-static 192.168.2.0 24 192.168.1.2 bfd control-packet
track 1
```

### 检查BFD或NQA配置与状态

在配置了静态路由与BFD或NQA联动的情况下，查看相关配置、状态信息是否正确。正常情况下BFD的会话状态为Up；NQA track项的状态信息为Positive。

**命令：** `display bfd session` 或 `display track xxx`（静态路由绑定的track号）

例如：通过上述命令查看，可以确认BFD或NQA状态正常。

```bash
<H3C>display track 1
Track ID: 1
Status: Positive (NQA entry: admin test reaction: 10)
```

### 检查静态路由的优先级

检查去往同一目的网段的路由中，静态路由的优先级是否最高。

**命令：** `display ip routing-table xxx.xxx.xxx.xxx`（目的IP网段）
`display ip routing-table xxx.xxx.xxx.xxx verbose`（目的IP网段）

例如：通过上述命令查看，可以确认静态路由的优先级不是最高，因而未出现在全局路由表中。

```bash
<H3C>display ip routing-table 192.168.2.0
Routing Tables: Public
Destinations: 1	Routes: 1

Destination/Mask    Proto   Pre   Cost        NextHop         Interface
192.168.2.0/24      OSPF    10    2           192.168.1.2     GE0/0

<H3C>display ip routing-table 192.168.2.0 verbose
Routing Table: Public
Summary Count: 2

Destination: 192.168.2.0/24
Protocol: OSPF	Process ID: 1
Preference: 10
NextHop: 192.168.1.2
BakNextHop: 0.0.0.0
RelyNextHop: 0.0.0.0
Tunnel ID: 0x0
State: Active	Adv
Tag: 0
Interface: GigabitEthernet0/0
BakInterface: -
Neighbor: 0.0.0.0
Label: NULL
Age: 00h00m23s

Destination: 192.168.2.0/24
Protocol: Static	Process ID: 0
Preference: 60	Cost: 0
NextHop: 192.168.3.2
Interface: GigabitEthernet0/1
BakNextHop: 0.0.0.0
Neighbor: 0.0.0.0
Tunnel ID: 0x0
Label: NULL
State: Inactive	Adv
Age: 00h21m52s
Tag: 0
```

### 检查静态路由掩码长度

检查到目的IP网段的报文转发能否匹配静态路由，即检查该静态路由的掩码是否最长。

**命令：** `display ip routing-table xxx.xxx.xxx.xxx`（目的IP网段）

例如：通过上述命令查看，可以确认静态路由的掩码不是最长。

```bash
<H3C>display ip routing-table 192.168.2.0
Routing Table: Public
Destination/Mask    Proto   Pre   Cost        NextHop         Interface
192.168.2.0/24      Static  60    0           192.168.1.2     GE0/0
192.168.2.0/25      RIP     100   1           192.168.3.2     GE0/1
```

## RIP路由故障排查

RIP是一种较为简单的内部网关协议，维护起来较为容易，通常情况下只要参数配置正确，就能够计算出正确的路由表。当发生路由表缺失现象时，首先需要检查RIP的各种参数设置，是否正确启动，接口功能是否使能。

因此定位思路是，先查基本配置，再查看是否验证问题，是否引入外部路由，路由表是否完整。

### 查看RIP配置

查看RIP进程的当前运行状态及配置信息。

**命令：** `display rip`

例如：通过命令查看，确认全局正确使能RIPv2并且接口未设置成silent端口。

### 是否开启密码验证

查看使能RIP的端口是否开启密码验证功能，如果开启，确保对端端口同样开启密码验证功能，同时验证密码一致。

**命令：** 接口视图下`display this`

例如：通过命令查看接口是否开启密码验证。

如果端口下配置了密码，需要确保两端密码配置一致。由于密文配置的密码采用了加密显示，在无法确定密码是否一致的情况下，请重新配置确认密码一致。

**命令：** 接口视图下`rip authentication-mode`

例如：在接口GigabitEthernet0/1上配置rfc2453格式的md5验证，验证字为rose。

```bash
[H3C-GigabitEthernet0/1]rip authentication-mode md5 rfc2453 cipher rose
```

### 是否属于引入的外部路由

在RIP引入外部路由时，只能引入路由表中状态为Active的路由，是否为Active状态通过命令查看。

**命令：** `display ip routing-table protocol`

例如：以静态路由为例，通过命令来查看引入的静态路由是否为Active状态。

```bash
[H3C]display ip routing-table protocol static
Static Routing Table Status:
Summary Count: 1
Destination/Mask    Proto   Cost        NextHop         Interface
192.168.2.0/24      Static  0           0.0.0.0         NULL0
```

### 查看路由表

查看RIP路由表中是否存在相应路由。

**命令：** `display rip route xxx.xxx.xxx.xxx`

例如：查看RIP路由表中56.0.0.0/8网段的路由信息。

### 接口是否开启接收和发送路由的功能

若查看RIP路由表未发现相应路由信息，请确认对应的接口未关闭发送和接收RIP报文的功能。

**命令：** `display rip interface`

```bash
<H3C>display rip 1 interface
Interface-name: Vlan-interface11
Address/Mask: 1.1.1.1/24
Version: RIPv2
Metricin: 5	Metricin route policy: 123
MetricOut: 5	MetricOut route policy: 234
Split-horizon/Poison-reverse: on/off
Input/Output: on/on
Current packets number/Maximum packets number: 234/2000
```

如果通过上述命令查看到rip Input/Output存在off状态，可以通过命令将其修改为on状态，在修改前，请确认该端口是否的确需要将rip Input/Output置于off状态。

**命令：** 接口视图下`rip input/output`

- 如果在ATM和FR接口上配置RIP，确保开启了接口的广播传送功能。以ATM接口为例，在对应的接口开启接收RIP报文的情况下，使能了RIP的Atm链路上无法传送RIP路由时，确认在pvc上开启了广播功能。

**命令：** `display current-configuration interface atm`

例如：通过命令查看使能了RIP的Atm配置信息。

```bash
<H3C>display current-configuration interface atm
#
interface Atm3/1/0
 pvc 2/32
  map ip 10.0.0.1 broadcast
```

如果对应pvc没有使能广播功能，请在创建映射时配置使能广播功能。

**命令：** `map ip xxx.xxx.xxx.xxx yyy.yyy.yyy.yyy broadcast`

例如：在pvc 1/32上创建一个静态映射，指定对端IP地址为10.0.0.1，并支持广播。

```bash
[H3C-Atm3/1/0]pvc 1/32
[H3C-Atm3/1/0-pvc-1/32]map ip 10.0.0.1 10.0.0.2 broadcast
```

- 是否存在不连续的子网。如果本地路由表中缺失的路由信息和本地路由表中存在的路由信息属于不连续的子网，则需要取消接口的聚合功能。summary命令用来使能RIP-2自动路由聚合功能，聚合后的路由以使用自然掩码的路由形式发布，减小了路由表的规模。undo summary命令用来关闭自动路由聚合功能，以便将所有子网路由广播出去。

**命令：** `undo summary`

例如：本地存在162.16.1.0/24网段，无法学习到邻居路由器上的162.16.3.0/24网段路由信息。

```bash
<H3C>system-view
[H3C]rip
[H3C-rip-1]undo summary
```

- 度量值是否大于等于16。如果本地路由表无相关路由，请查看存在该路由的相邻路由器上该路由的度量值，并且确认该度量值和该设备端口配置的发送路由度量附加值以及本设备端口配置的接收路由的附加度量值（如果有）之和小于16。

**查看路由度量值的命令：** `display rip database`

```bash
[H3C]interface GigabitEthernet2/1/2
[H3C-GigabitEthernet2/1/2]display rip 1 database
1.1.1.0/24, cost 2, nexthop 1.1.1.1, Rip-interface
```

**查看接口附加度量值的命令：** `display rip interface`

通过上述命令查看接口的MetricIn是接收路由的附加度量值，MetricOut是发送路由的附加度量值。

## OSPF路由故障排查

由于OSPF路由正确地加入到全局路由表，依赖于正确的OSPF路由计算，而OSPF计算路由依赖于正确的OSPF LSDB数据库信息，要建立正确的OSPF LSDB数据库则首先要确保邻居之间能够形成正确的邻接关系。因此OSPF路由问题的排查整体思路为：首先检查OSPF邻居关系，其次检查OSPF LSDB数据库信息，最后检查全局路由表。

### 查看OSPF邻居状态是否正确

查看两端OSPF邻居状态是否正常，正常情况下DRother之间的邻居关系应该稳定在2-way状态，非DRother之间的邻居关系应该稳定在Full状态。

**命令：** `display ospf peer x.x.x.x`

例如：通过命令查看，可以确认OSPF的邻居状态是否正常。

```bash
<H3C>display ospf peer 2.2.2.2
OSPF Process 1 with Router ID 1.1.1.1
Neighboring Router ID: 2.2.2.2
Area: 0.0.0.0
State: Full/BDR		Mode: Nbr is  Master or Slave
Priority: 1
Dead Time: 35 sec
Interface Address: 10.1.1.2
```

### 确认接口启动OSPF及邻居两端OSPF参数相匹配

- 确认接口启动OSPF。OSPF的运行是基于设备接口的，如果OSPF没有在接口启动，那么邻居关系肯定无法形成。在接口上启用OSPF是通过Area视图下的network命令实现的，必须确保network中的网络范围包括需要启动OSPF的接口地址。

**命令：** `display ospf interface`

例如：通过命令查看接口是否启动OSPF。

```bash
<H3C>display ospf interface
OSPF Process 1 with Router ID 3.3.3.3
Interfaces
Area: 0.0.0.0
IP Address          Type      State         DR            BDR
12.1.1.1            Broadcast  DR           12.1.1.1      12.1.1.2
```

- 确认邻居两端OSPF参数相匹配，具体包括以下几点：
  - OSPF区域配置是否匹配。启动OSPF的接口属于某个区域，同时区域有多种类型，区域依靠区域ID进行标识，如果两边的区域类型或区域ID不匹配，则不会形成邻居关系。
  - OSPF验证配置是否匹配。OSPF支持报文验证功能，验证分为简单验证和md5验证两种类型，如果两边验证类型或密钥配置不同，则OSPF无法通过验证，邻居关系无法形成。
  - 两端OSPF接口上计时器设定值是否匹配。OSPF通过周期性的交互Hello报文维系邻居关系，Hello报文中携带了Hello报文的发送间隔计时器及邻居失效计时器，如果这些计时器的值在两边的Hello报文中不匹配，那么OSPF的邻居关系无法形成。注意dead timer的值至少应为hello timer值的4倍。
  - 两端OSPF接口类型是否匹配。OSPF邻居关系的正常建立需要确保邻居两端接口的OSPF网络类型一致，否则将无法形成邻居关系。需要说明的是若邻居双方一端设置为P2P类型另一端设置为广播类型，那么邻居状态可以达到FULL状态，但此时无法计算出路由信息。
  - 广播网络中两端接口子网掩码是否相同。OSPF Hello报文中携带子网掩码信息。在广播网络中，如果两端接口属于不同的IP子网，那么邻居关系无法形成。
  - NBMA网络是否指定邻居。OSPF网络类型为NBMA时必须手工指定邻居的IP地址，否则端口无法发送Hello报文，无法形成邻居关系。

**命令：** `display current-configuration interface interface-type interface-number`

例如：通过命令查看接口下的OSPF参数设置是否一致。

```bash
[H3C]display current-configuration interface Ethernet0/1/0.1
#
interface Ethernet0/1/0.1
 vlan-type dot1q vid 100
 ip address 20.1.1.2 255.255.255.0
 ospf network-type p2p
#
```

### 确认邻接关系的两端接口没有设置为静默端口

当接口在OSPF协议视图中被设置为静默端口时，它将不能发送OSPF Hello报文，因此OSPF邻居关系无法形成。

**命令：** `display current-configuration configuration ospf`

例如：通过命令查看接口正确启动OSPF并设置为非静默端口。

```bash
[H3C]display current-configuration configuration ospf
#
ospf 1
 silence GigabitEthernet1/0/1
 network 10.1.0.0 0.0.0.255
 network 10.10.2.1 0.0.0.0
 area 0.0.0.1
#
```

### 查看路由是否加入OSPF路由表

查看OSPF路由表中是否存在相应路由。

**命令：** `display ospf routing x.x.x.x`

例如：查看外部路由9.9.9.9是否加入ospf路由表。

```bash
<H3C>display ospf routing 9.9.9.9
OSPF Process 1 with Router ID 4.4.4.4
Routing Tables
Routing for ASEs
Destination     Cost     Type      Tag
9.9.9.9/32      1        Type2     1
NextHop: 10.10.5.1     AdvRouter: 3.3.3.3
```

### 确认路由信息正确发布

若查看OSPF路由表未发现相应路由信息，请首先确认路由信息是否在OSPF中正确发布，对于未进行发布的路由请修改配置将路由正确发布。

**命令：** `display current-configuration configuration ospf`

例如：查看10.10.4.0/24的路由信息是否在OSPF中发布。

```bash
<H3C>display current-configuration configuration ospf
#
ospf 1
 area 0.0.0.0
  network 10.10.1.0 0.0.0.255
  network 10.10.4.0 0.0.0.255
 area 0.0.0.1
  network 10.10.2.0 0.0.0.255
#
```

### 确认LSA信息正确

确认OSPF LSDB数据库中是否存在路由计算所需的正确LSA信息。对于区域内的路由需要检查是否存在该路由始发者的Router LSA，DR的Network LSA（广播网络）；对于区域间的路由需要首先检查是否存在LS ID为该网段的Summary LSA，然后检查是否存在该Summary LSA所对应Adv Rtr的Router LSA；如果外部路由是通过区域内学习到的，需要首先检查是否存在LS ID为该网段的ASE LSA，然后检查是否存在该ASE LSA中所对应Adv Rtr的Router LSA；如果外部路由是通过区域间学到的那么首先检查对应的ASE LSA，其次检查是否存在该ASE LSA所对应Adv Rtr的Asbr Summary LSA，最后检查该Asbr Summary LSA所对应Adv Rtr的Router LSA。

**命令：**
- `display ospf lsdb router x.x.x.x`
- `display ospf lsdb network x.x.x.x`
- `display ospf lsdb summary x.x.x.x`
- `display ospf lsdb asbr x.x.x.x`
- `display ospf lsdb ase x.x.x.x`

例如：通过命令查看外部路由9.9.9.9相关的LSA信息。

```bash
<H3C>display ospf lsdb ase 9.9.9.9
OSPF Process 1 with Router ID 4.4.4.4
Link State Database
Type: External
LS ID: 9.9.9.9
Adv Rtr: 3.3.3.4
LS Age: 1
Len: 36
Options: E
Seq#: 80000001
Checksum: 0xc76b
Net Mask: 255.255.255.255
TOS: 0	 Metric: 1
Forward Address: 0.0.0.0
External Route Tag: 0

<H3C>display ospf lsdb asbr 3.3.3.3
OSPF Process 1 with Router ID 4.4.4.4
Area: 0.0.0.0
Link State Database
Type: Sum-Asbr
LS ID: 3.3.3.3
Adv Rtr: 2.2.2.2	LS Age: 1091
Len: 28
Options: E
Seq#: 80000002
Checksum: 0x46fb

<H3C>display ospf lsdb router 2.2.2.2
OSPF Process 1 with Router ID 4.4.4.4
Area: 0.0.0.2
Link State Database
Type: Router
LS ID: 2.2.2.2
Adv Rtr: 2.2.2.2
Link Count: 1
Link ID: 10.10.5.1
Data: 10.10.5.1
Link Type: TransNet	Metric: 1
```

例如：通过命令查看区域内路由10.10.4.0/24相关的LSA信息。

```bash
<H3C>display ospf lsdb network
OSPF Process 1 with Router ID 2.2.2.2
Area: 0.0.0.0
Link State Database
Type: Network
LS ID: 10.10.1.1
Adv Rtr: 1.1.1.1	LS Age: 934
Len: 32
Options: E
Seq#: 80000002
Checksum: 0xc76b
Net Mask: 255.255.255.0
Attached Router: 2.2.2.2
Attached Router: 1.1.1.1

<H3C>display ospf lsdb router 1.1.1.1
OSPF Process 1 with Router ID 2.2.2.2
Area: 0.0.0.0
Link State Database
Type: Router
LS ID: 1.1.1.1
Adv Rtr: 1.1.1.1	LS Age: 823
Len: 48
Options: ABR E	Seq#: 80000007
Checksum: 0x8d61
Link Count: 2
Link ID: 10.10.1.1
Data: 10.10.1.1
Link Type: TransNet	Metric: 1
Link ID: 10.10.4.0
Data: 255.255.255.0
Link Type: StubNet	Metric: 1
```

例如：通过命令查看区域间路由10.10.2.0/24相关的LSA信息。

```bash
<H3C>display ospf lsdb summary 10.10.2.0
OSPF Process 1 with Router ID 2.2.2.2
Area: 0.0.0.0
Link State Database
Type: Sum-Net
LS ID: 10.10.2.0
Adv Rtr: 1.1.1.1	LS Age: 1400
Len: 28
Options: E
Seq#: 80000001
Checksum: 0x46fb
Net Mask: 255.255.255.0
Tos: 0	Metric: 1
```

导致OSPF数据库中LSA异常或缺失的原因主要包括如下几种情况，需要从相关的配置或规划角度进行修正。

- 骨干区域被分割，导致LSA缺失。
- 虚连接配置错误，导致LSA缺失。
- RouterID冲突，导致LSA震荡。

### 若外部路由携带FA地址确认FA路由为有效路由

若外部路由携带FA地址确认FA路由为有效路由。OSPF必须能够通过区域内或区域间路由到达该FA地址，否则该外部路由不会加入OSPF路由表。

例如：外部路由9.9.9.9携带了FA地址为10.10.6.2，通过OSPF内部路由能够学习到10.10.6.2的路由，外部路由9.9.9.9正确加入路由表。

```bash
<H3C>display ospf lsdb ase 9.9.9.9
OSPF Process 1 with Router ID
Link State Database
Type: External
LS ID: 9.9.9.9
Adv Rtr: 3.3.3.4	LS Age: 1
Len: 36
Options: E	Seq#: 80000001
Checksum: 0xc76b
Net Mask: 255.255.255.255
TOS: 0	Metric: 1
Forwarding Address: 10.10.6.2
External Route Tag: 0

<H3C>display ospf routing
OSPF Process 1 with Router ID
Routing for Network
Destination     Cost     Type
10.10.6.0/24    3       Inter
NextHop: 10.10.5.1	AdvRouter: 2.2.2.2
```

### 查看路由是否加入全局路由表

查看OSPF路由是否正确加入到全局路由表内，只有加入到全局路由表的路由才能指导数据包的转发。如果相同的路由信息同时也从其他路由协议学到，为了确保OSPF学习的路由能够最终加入全局路由表，需要确保其优先级为最优。

**命令：** `display ip routing-table x.x.x.x verbose`

例如：
```bash
<H3C>display ip routing-table 9.9.9.9 verbose
Routing Table: Public
Summary Count: 2

Destination: 9.9.9.9/32
Protocol: O_ASE	Process ID: 1
Preference: 150	Cost: 1
NextHop: 10.10.5.1	Interface: Ethernet0/1/0
Tag: 0
Age: 00h52m12s
Tunnel ID: 0x0	Cost: 0

Destination: 9.9.9.9/32
Protocol: Static	Process ID: 0
Preference: 200	Cost: 0
NextHop: 0.0.0.0	Interface: NULL
Tag: 0
Age: 00h00m00s
Tunnel ID: 0x0	Cost: 0
```

## BGP路由故障排查

为了保证BGP路由正确加入到全局路由表中，首先需要确保BGP路由有效，其次要确保能够在和通过其他路由协议学到的路由比较中被优选。

BGP故障定位思路：首先，查看BGP邻居状态；其次，查看BGP路由表，查看路由是否存在，是否有效，是否优选；最后，查看BGP的属性，查看是否优选到了正确的路由。

### 查看BGP邻居状态

如果在BGP路由表中，未能查到相匹配路由信息，需要查看BGP邻居状态是否正常。

**命令：** `display bgp peer`

例如：通过命令查看BGP邻居是否正常。

```bash
<H3C>display bgp peer
BGP local router ID: 1.1.1.1
Local AS number: 100
Total number of peers: 1	Peers in established state: 1
Peer            AS    MsgRcvd    MsgSent    Up/Down
3.3.3.3         100   100        95         100:12:36
```

### 查看路由表，确认BGP邻居是否可达，查看邻居配置是否正确

如果BGP邻居不能正常建立，需要查看路由表确认BGP邻居是否可达。

**命令：** `display ip routing-table x.x.x.x`

例如：通过命令查看BGP邻居的IP地址是否存在匹配的路由。

```bash
<H3C>display ip routing-table 3.3.3.3
Routing Tables: Public
Destinations: 1	Routes: 1

Destination/Mask    Proto   Pre   Cost        NextHop         Interface
3.3.3.3/32          OSPF    10    1           9.1.1.1         S2/2/0
```

如果BGP邻居不能正常建立，还需要查看BGP邻居配置是否正确。

**命令：** `display current-configuration configuration bgp`

例如：通过命令查看BGP邻居的配置。还需要用同样的方法确认对端设备的配置是否正确。

### 查看BGP路由表信息，相关路由是否存在

查看BGP路由表信息，确认相关路由是否存在于BGP路由表中。

**命令：** `display bgp routing-table x.x.x.x`

例如：通过命令查看，可以确认BGP路由表中是否存在相关路由。

```bash
<H3C>display bgp routing-table 8.1.1.0/24
Total Number of Routes: 1
BGP Local router ID is 1.1.1.1
Status codes: * - valid, > - best, d - damped,
h - history, i - internal, s - suppressed, S - Stale
Origin: i - IGP, e - EGP, ? - incomplete

Network          NextHop         MED    LocPrf    PrefVal   Path/Ogn
*>i 8.1.1.0/24     9.1.1.1         0       100       0         65002?
```

### 确认BGP邻居是否将路由发送出来

如果BGP路由表中未有相关路由，需要确认BGP邻居是否将相关路由发送出来。

**命令：** `display bgp routing-table peer x.x.x.x advertised-routes`

例如：在对端路由器上通过命令查看邻居发送的路由信息。

```bash
<H3C>display bgp routing-table peer 2.2.2.2 advertised-routes
Total Number of Routes: 2
BGP Local router ID is 3.3.3.3
Status codes: * - valid, > - best, d - damped,
h - history, i - internal, s - suppressed, S - Stale
Origin: i - IGP, e - EGP, ? - incomplete

Network          NextHop         MED    LocPrf    PrefVal   Path/Ogn
*> 8.1.1.0/24     0.0.0.0         0       0         0         ?
```

### 查看BGP路由表信息，相关路由是否有效

查看BGP路由表信息，确认相关路由在BGP路由表中是否有效。

**命令：** `display bgp routing-table x.x.x.x`

例如：通过命令查看，可以确认BGP路由表中相关路由是否有效。

```bash
<H3C>display bgp routing-table 8.1.1.0/24
Total Number of Routes: 1
BGP Local router ID is 1.1.1.1
Status codes: * - valid, > - best, d - damped,
h - history, i - internal, s - suppressed, S - Stale
Origin: i - IGP, e - EGP, ? - incomplete

Network          NextHop         MED    LocPrf    PrefVal   Path/Ogn
* i 8.1.1.0/24    9.1.1.1         0       100       0         65002?
```

### 查看路由表，确认BGP路由下一跳是否可达

如果BGP路由表中存在相应的路由信息，但是该路由为无效路由，需要确认该BGP路由下一跳是否可达。

**命令：** `display ip routing-table x.x.x.x`

例如：通过命令查看BGP路由的下一跳是否存在匹配的路由。

```bash
<H3C>display ip routing-table 9.1.1.1
Routing Tables: Public
Destinations: 1	Routes: 1

Destination/Mask    Proto   Pre   Cost        NextHop         Interface
9.1.1.1/32          OSPF    10    1           192.168.1.2     Vlan100
```

### 查看路由表，确认BGP路由是否被选中

查看路由表，确认路由表是否优选了BGP的路由。

**命令：** `display ip routing-table x.x.x.x`

例如：通过命令查看相关路由是否由BGP学习到。

```bash
<H3C>display ip routing-table 8.1.1.0/24
Routing Tables: Public
Destinations: 1	Routes: 1

Destination/Mask    Proto   Pre   Cost        NextHop         Interface
8.1.1.0/24          OSPF    10    1           9.1.1.1         S2/2/0
```

### 查看路由配置信息，确认路由表中选中路由所属路由协议的优先级是否高于BGP

查看设备配置信息，确认在路由表中选中的路由所属的路由协议的优先级。

**命令：** `display current-configuration bgp`、`display current-configuration ospf`

例如：查看OSPF路由的优先级是多少，BGP的路由优先级是多少？注意H3C设备默认的各个路由协议优先级。

### 查看BGP路由表，查看BGP属性，确认BGP是否优选到正确的路由

查看BGP路由表，确认BGP是否优选到正确的路由。

**命令：** `display bgp routing-table x.x.x.x`

例如：通过命令查看相关BGP路由的属性。

```bash
<H3C>display bgp routing-table 8.1.1.0/24
Total Number of Routes: 2
BGP Local router ID is 1.1.1.1
Status codes: * - valid, > - best, d - damped,
h - history, i - internal, s - suppressed, S - Stale
Origin: i - IGP, e - EGP, ? - incomplete

Network          NextHop         MED    LocPrf    PrefVal   Path/Ogn
*> i 8.1.1.0/24   9.1.1.1         0       100       0         65002?
*  i 8.1.1.0/24   10.1.1.1        0       100       0         65003?
```

常用BGP属性比较顺序：
1. 比较LocPrf属性大小；
2. 比较AS-Path的长短；
3. 比较Origin属性，i优先于e，e优先于？；
4. 比较MED属性大小；
5. 优先选择从EBGP邻居学来的路由。
