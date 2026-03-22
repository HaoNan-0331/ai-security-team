# 快速IPSec配置示例

组网需求

按照下图所示配置接口IP地址，DUT2与DUT1建立IPSec隧道，使PC3与PC2正常通信。

配置步骤

在设备DUT2上，在系统菜单点击“网络>IPSec-VPN>IPSec快速配置”，进入IPSec快速配置页面，点击<新建>，按照下图进行配置：

DUT2配置完成快速配置后，在系统菜单点击“网络>IPSec隧道接口”，能够看到自动创建的隧道接口：

在设备DUT1上，在系统菜单点击“网络>IPSec-VPN>IPSec快速配置”，进入IPSec快速配置页面，点击<新建>，按照下图进行配置:

DUT1配置完成快速配置后，在系统菜单点击“网络>IPSec隧道接口”，能够看到自动创建的隧道接口如下图：

两边设备配置完成后，分别在系统菜单点击“网络>IPSes-VPN>IPSec SA”，进入IKE SA和IPSec SA页签，状态显示连接，表示IPSec建立正常。

PC2 ping PC3，流量走IPSec隧道。