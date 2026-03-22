# DNS Zones

DNS区域(ZONE)是DNS域名空间中连续的树，将域名空间按照需要划分为若干较小的管理单位。例如在CCTV中设置一个DNS服务器，这个DNS服务器将完成域名空间“cctv.com”下的域名解析工作，我们称这是一个区域。在DNS服务器中，必须先建立区域，在区域中建立子域，在区域或者子域中添加主机记录。一台DNS服务器可以管理一个或多个区域, 而一个区域也可以由多台DNS服务器来管理。

在系统菜单点击“网络>DNS>DNS Zones”，进入DNS Zones页面，显示设备上配置的所有DNS Zones信息，在该页面可以对DNS Zones进行新建、查看和删除。

在DNS Zones页面下点击<新建>，进入到DNS Zones的配置中，进行Zone名称、SOA记录服务器、NS记录服务器的配置、点击<下一步>，可以配置DNS Zone的记录信息的配置，支持A、NS、CNAME、MX、TXT、PTR、AAAA记录的配置。

DNS Zone 新建页配置项及详细说明如下：

DNS Zone 下一步页配置项及详细说明如下：

在DNS Zones页面下点击已有的DNS Zones的“DNS记录”列下的数字，进入对应DNS Zones的DNS记录页面显示该DNS Zones下记录信息，在该页面可以对DNS Zones的记录进行新建、查看和删除。

进入需要配置的DNS Zone的DNS记录页面点击<新建>，进入DNS记录创建，支持A、NS、CNAME、MX、TXT、PTR、AAAA记录的配置。