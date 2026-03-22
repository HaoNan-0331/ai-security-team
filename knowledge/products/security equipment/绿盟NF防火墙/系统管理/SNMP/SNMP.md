# SNMP

NF中的SNMP支持SNMP V3版本，兼容SNMP V1和V2C版本。

进入 系统 > SNMP 页面，如图3-16所示。

SNMP

NF中SNMP的相关配置包括：

基础信息配置：SNMP Agent和Trap的总体开关、设备的信息配置、私有MIB库下载，以及SNMP相关说明文件下载。

SNMP配置：包括SNMP Agent和Trap的配置。

基础信息配置

在如图3-16所示的页面中，在“基础信息配置”区域配置SNMP Agent和Trap的总体开关、设备的信息配置、私有MIB库下载，以及SNMP相关说明文件下载。参数说明如表3-20所示。

SNMP系统信息配置

SNMP配置

在如图3-16所示的页面中，首先要选择SNMP的版本，可选项有：V1V2、V3。然后分别配置Agent和Trap的参数，不同的版本参数略有不同。

Agent配置

SNMP Agent用于在NF上收集可以向NMS报告的信息，支持SNMP V1V2和V3。

V1V2：采用团体名（Community Name）认证，非设备认可的团体名的SNMP报文将被丢弃。

V3：采用用户名和密码认证方式，而且支持加密传输，比V1和V2提供了更高的安全性。

单击Agent配置列表右上方的【新建】按钮，配置参数，即可新建一个SNMP Agent。参数说明如表3-21所示。不同版本的SNMP页面会有区别。

新建Agent后，可以对其进行编辑、查询和删除等操作。

SNMP Agent参数

Trap配置

NF可以主动向SNMP NMS发送SNMP Trap告警信息。NF的SNMP Trap支持SNMP V1、V2C和V3。此处配置接收告警事件Trap信息的SNMP NMS的IP地址和端口。

单击Trap配置列表右上方的【新建】按钮，配置参数，即可新建一个SNMP Trap。参数说明如表3-22所示。不同版本的SNMP页面会有区别。

新建Trap后，可以对其进行编辑、查询和删除等操作。

SNMP Trap主机参数