# ISP路由

一些用户会申请多条ISP（Internet Service Provider，简称ISP）线路进行流量负载均衡。在这种业务场景下，如果通过ISPA的线路访问ISP的服务器，会降低网络传输速率。针对该问题，虚拟化防火墙设备提供ISP路由功能，使不同ISP流量走专有路由，从而提高网络速度。

配置ISP路由，配置以ISP地址库名称为目的地址的ISP路由。虚拟化防火墙设备提供多个预定义 ISP 地址库，分别是ISP_INTL.dat、ISP_CERNET.dat、ISP_CT.dat、ISP_UNICOM.dat、ISP_CTT.dat、ISP_CMCC.dat、ISP_CHINA.dat。

在系统菜单中点击“网络>IPv4路由>ISP路由”，进入ISP路由页面，用户可以在此页面新建、编辑或删除ISP路由。

用户可在ISP路由页面下，点击<新建>按钮，创建新的ISP路由，或在右侧“操作”列下点击图标修改已有的ISP路由配置。

ISP路由的配置项及详细说明如下：