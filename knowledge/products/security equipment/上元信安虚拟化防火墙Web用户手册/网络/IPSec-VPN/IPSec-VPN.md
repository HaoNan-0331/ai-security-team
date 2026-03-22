# IPSec-VPN

IPSec用于保护敏感信息在Internet上传输的安全性。它在网络层对IP数据包进行加密和认证。 IPSec提供以下网络安全服务，这些安全服务是可选的，通常情况下，本地安全策略决定采用以下安全服务的一种或多种。

安全服务包含以下几种：

数据的机密性—IPSec的发送方对发给对端的数据进行加密。

数据的完整性—IPSec的接收方对接收到的数据进行验证以保证数据在传送的过程中

没有被修改。

数据来源的认证—IPSec接收方验证数据的起源。

抗重播—IPSec的接收方可以检测到重播的IP包丢弃。

使用IPSec可以避免数据包的监听、修改和欺骗，数据可以在不安全的公共网络环境下安全的传输，IPSec的典型运用是构建VPN。IPSec使用“封装安全载荷（Encapsulating Security Payload,简称ESP）”或者“鉴别头（Authentication Header，简称AH）”证明数据的起源地、保障数据的完整性以及防止相同数据包的不断重播；使用ESP保障数据的机密性。密钥管理协议（Internet Security Association and Key Management Protocol,简称ISAKMP） 根据安全策略数据库（Security Policy Database,简称SPDB）随IPSec使用，用来协商安全联盟（Security Association,简称SA）并动态的管理安全联盟数据库。

相关术语解释：

鉴别头（AH）：用于验证数据包的安全协议。

封装安全有效载荷（ESP）：用于加密和验证数据包的安全协议；可与AH配合工作可也以单独工作。

加密算法：ESP所使用的加密算法。

验证算法：AH或ESP用来验证对方的验证算法。

密钥管理：密钥管理的一组方案，其中Internet密钥交换协议（Internet Key Exchange Protocol，简称IKE）是默认的密钥自动交换协议。

在系统菜单点击“网络>IPSec-VPN>IPSec提案”，进入IPSec提案配置页面，点击<新建>创建IPSec一阶段。

IPSec一阶段配置项及详细说明如下：

在系统菜单点击“网络>IPSec-VPN>IPSec提案”，进入IPSec提案配置页面，若存在已经配置好的一阶段IKE协商提案，直接点击已创建好的一阶段名称，进入二阶段配置页面，点击<新建>。

IPSec二阶段配置项及详细说明如下：

注意：

如果发起端同时配置AH：MD5-HMAC和AH：NULL，此时对端不应只配置AH：NULL。因为当加密方式存在时，将采取加密方式来进行协商。

除上文所述的IPSec VPN的典型配置方式，虚拟化防火墙还提供快速配置方式，适用于简单化、自动化的VPN部署。与典型配置方式相比，快速配置方式隐藏IKE协商策略、IPSec协商策略和IPSec隧道接口的创建，无需配置所要保护的网段，用户可以快速配置做到“简单部署、快速上线、动态适应”。

在系统菜单点击“网络>IPSec-VPN>IPSec快速配置”，进入IPSec快速配置页面，点击<新建>，配置如下：

IPSec快速配置项及详细说明如下：

在系统菜单点击“网络<IPSec-VPN<IPSec隧道接口”，进入IPSec隧道接口配置页面，点击<新建>，创建IPSec隧道接口。

IPSec隧道接口配置项及详细说明如下：

在系统菜单点击“网络>IPSec-VPN>IPSec SA>IPSec SA”,进入IPSec SA页签,查看IPSec SA的建立情况。

点击IPSec SA监控后的，可以查看IPSec VPN相关详细信息。

在系统菜单点击“网络>IPSec-VPN>IPSec SA>IKE SA”，进入IKE SA页签，查看IKE SA的建立情况。

在系统菜单点击“网络>IPSec-VPN>IPSec SA>用户接入监控”，进入用户接入监控页签，查看IOS客户端通过IPSec VPN进行VPN连接后的信息。

用户接入监控信息及详细说明如下：

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

组网需求

按照下图所示配置接口IP地址，IOS客户端与DUT1建立IPSec隧道，使IOS客户端与内网进行通信。

配置步骤

在设备DUT1上，系统菜单点击“网络>IPSec-VPN>IPSec提案”，进入IPsec提案页面，点击<新建>，按照下图进行配置（IOS客户端仅支持野蛮模式，DH组仅支持2，加密算法支持3DES、DES、AES128、AES192、AES256；认证MD5、SHA）：

配置完提案后，点击<网关名称>，并<新建>IPSec二阶段，按照下图进行配置（算法支持3DES_MD5、3DES_SHA1、AES128_MD5、AES128_SHA1、AES192_MD5、AES192_SHA1、AES256_MD5、AES256_SHA1，PFS支持无、1、2、5）

系统菜单点击“网络>IPSec-VPN>IPSec隧道接口”，点击<新建>，按照下图进行配置：

系统菜单点击“网络>VPN管理>VPN用户中心”，打开用户中心端口，按照下图进行配置：

系统菜单点击“对象>用户对象>用户”，<新建>用户，按照下图进行配置：

使用IOS客户端输入服务器地址、端口号、预共享密钥、用户名密码即可登录，按照下图进行配置：

首次登录会提示允许添加VPN配置，再次输入用户的密码。

登录成功后，页面可查看连接信息，包括连接时长、已用流量、上下行流速等。

系统菜单点击“网络>IPSec-VPN>IPSec SA”，在“用户接入监控”页查看连接信息。

组网需求

按照下图所示配置接口IP地址，DUT2与DUT1建立IPSec隧道，使PC3与PC2正常通信。

配置步骤

在设备DUT2上，在系统菜单点击“网络>IPSec-VPN>IPSec快速配置”，进入IPSec快速配置页面，点击<新建>，按照下图进行配置：

DUT2配置完成快速配置后，在系统菜单点击“网络>IPSec隧道接口”，能够看到自动创建的隧道接口：

在设备DUT1上，在系统菜单点击“网络>IPSec-VPN>IPSec快速配置”，进入IPSec快速配置页面，点击<新建>，按照下图进行配置:

DUT1配置完成快速配置后，在系统菜单点击“网络>IPSec隧道接口”，能够看到自动创建的隧道接口如下图：

两边设备配置完成后，分别在系统菜单点击“网络>IPSes-VPN>IPSec SA”，进入IKE SA和IPSec SA页签，状态显示连接，表示IPSec建立正常。

PC2 ping PC3，流量走IPSec隧道。