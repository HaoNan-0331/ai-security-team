# BGP

BGP（Border Gateway Protocol）是一种不同自治系统的路由器之间进行通信的外部网关协议(Exterior Gateway Protocol，EGP)，其主要功能是在不同的自治系统(Autonomous Systems，AS)之间交换网络可达信息，并通过协议自身机制来消除路由环路。

BGP 使用TCP协议作为传输协议，通过TCP协议的可靠传输机制保证BGP的传输可靠性。

运行BGP协议的Router称为BGPSpeaker，建立BGP会话连接(BGP Session)的BGP Speaker之间被称作对等体(BGP Peers)。BGPspeaker之间建立对等体的模式有两种： IBGP(Internal BGP)和EBGP(External BGP)。IBGP是指在相同AS内建立的BGP连接，EBGP 是指在不同AS之间建立的BGP连接。二者的作用简而言之就是：EBGP是完成不同AS之间路由信息的交换，IBGP是完成路由信息在本AS内的过渡。

BGP协议需要路由器ID，作为本路由器在自治系统中的唯一标识。在协议任务启动后，虚拟化防火墙会选择状态up的接口地址大的作为本路由器ID，也可指定一个路由器ID。

在系统菜单中点击“网络>IPv4路由>BGP>BGP”，进入BGP配置页签。

BGP的配置项及详细说明如下：

在系统菜单中点击“网络>IPv4路由>BGP>BGP发布网络”，进入BGP发布网络配置页签。

用户可在BGP发布网络页签，点击<新建>，创建发布网络。

BGP发布网络的配置项及详细说明如下：

在系统菜单中点击“网络>IPv4路由>BGP>BGP对等体”，进入BGP对等体配置页签。

用户可在BGP对等体页签，点击<新建>，创建BGP对等体。

BGP对等体的配置项及详细说明如下：

组网需求

如下图所示，配置接口IP地址，要求设备DUT1在ge0/1接口上启用BGP协议，设备DUT2在接口ge0/1上启用BGP协议。PC1 ping PC2的IP地址可通。

配置步骤

在设备DUT1上，在系统菜单中点击“网络>IPv4路由>BGP>BGP”，进入BGP配置页签，具体信息请参考下图：

在设备DUT1上，在系统菜单中点击“网络>IPv4路由>BGP>BGP发布网络”，进入BGP发布网络页签，配置网络172.16.1.0/24，具体信息请参考下图：

在设备DUT1上，在系统菜单中点击“网络>IPv4路由>BGP>BGP对等体”，进入BGP对等体页签，点击<新建>IP地址和远端AS，具体信息请参考下图：

设备DUT2请参考DUT1配置方法。

配置完成后，在PC1上使用ping命令验证PC2可达。