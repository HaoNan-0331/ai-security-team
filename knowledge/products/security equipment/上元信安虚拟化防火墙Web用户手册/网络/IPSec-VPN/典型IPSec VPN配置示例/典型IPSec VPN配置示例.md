# 典型IPSec VPN配置示例

组网需求

按照下图所示配置接口IP地址，DUT2与DUT1建立IPSec隧道，使PC3能够与PC2正常通信。

配置步骤

在设备DUT2上，在系统菜单点击“网络>IPSec-VPN>IPSec提案”，进入IPSec提案配置页面，点击<新建>，按照下图进行配置：

DUT2点击创建好的一阶段名称<DUT2-peer>，配置二阶段，点击<新建>，按照下图配置

配置完成二阶段后，点击“网络>IPSec-VPN>IPSec隧道接口”，进入IPSec隧道接口配置页面，点击<新建>，按如下图配置：

在设备DUT1上，在系统菜单点击“网络>IPSec-VPN>IPSec提案”，进入IPSec提案配置页面，点击<新建>，按照下图进行配置：

DUT1点击创建好的一阶段名称<DUT1-local>，配置二阶段，点击<新建>按照下图配置：

DUT1配置完成二阶段后，点击“网络>IPSec-VPN>IPSec隧道接口”，进入IPSec隧道接口配置页面，点击<新建>，按下图配置：

两边设备配置完成后，分别在系统菜单点击“网络>IPSes-VPN>IPSec SA”，进入IKE SA和IPSec SA配置页签，状态显示连接，表示IPSec建立正常。

PC3 ping PC2，流量走IPSec隧道。