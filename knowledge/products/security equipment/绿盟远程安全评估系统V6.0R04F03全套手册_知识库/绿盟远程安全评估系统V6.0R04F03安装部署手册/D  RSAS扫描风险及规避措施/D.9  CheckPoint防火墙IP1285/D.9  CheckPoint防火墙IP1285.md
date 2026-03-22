# D.9  CheckPoint防火墙IP1285

> 来源: 第379页 - 第379页

绿盟远程安全评估系统安装部署手册
解决方法
关闭交换机web server，命令：
config t
no ip http server
no ip http secure-server
详细说明（可参考下面网页中的Software Versions and Fixes查看受影响和修复版本）：
⚫ http://www.cisco.com/en/US/products/products_security_advisory09186a0080a96478.shtml
⚫ http://www.cisco.com/en/US/products/products_security_advisory09186a0080a9648d.shtml
D.8 juniper 防火墙存在 CVE-2014-2842 漏洞，此漏洞被触发会造成
防火墙自动宕机
原因
juniper 6.3版本之前的系统在443端口存在拒绝服务漏洞，漏洞名称为CVE-2014-2842漏洞，
此漏洞被触发时会导致防火墙因拒绝服务而发生宕机。
该漏扫有两个插件OpenSSL TLS心跳扩展协议包远程信息泄露漏洞和检测到Skype客户端，
这两个插件都属于CVE-2014-2842漏洞同类型检查的插件，此问题属于RSAS都存在的问题，
只要RSAS有检查此漏洞类型的相应插件，juniper防火墙都会宕机，非我司RSAS个例问题。
OpenSSL TLS心跳扩展协议包远程信息泄露漏洞插件是在5.0.12.46插件版本上添加的。检测
到Skype客户端插件是51100加的插件文件。
CVE-2014-2842：NetScreen ScreenOS SSL/TLS协议报文处理拒绝服务漏洞
受影响的版本
juniper 6.3版本及之前的系统版本
参考链接可见各应用产品所存在的漏洞风险：http://www.tuicool.com/articles/QZnyq2。
解决方法
扫描前屏蔽443端口。
D.9 CheckPoint 防火墙 IP1285
扫描checkpoint IP1285型号的防火墙，导致设备部分路由失效。
版权所有 © 绿盟科技 372 V6.0R04F03 限制分发级

绿盟远程安全评估系统安装部署手册
D.10 全端口扫描以下设备，导致设备负载过高，直至宕机
防火墙h3c secpath f1000-e
硬件版本ver.b
软件版本ver5.20 build3177
四层交换 radware 负载均衡
硬件版本c.5
软件版本2.14.03
核心交换 Cisco Catalyst4506 ver12.1 EA1a
Cisco 3550 ver12.1
原因
由于没有开启调试模式且客户侧无法再做扫描，经研发人员析得出结论为，客户侧开启了全
端口扫描，即扫描1-65535端口，会造成网络大流量，如果网络设备本身配置的策略问题或
者对大流量承受能力差，会造成宕机。而客户此次扫描，在执行端口扫描时已经宕机。
临时解决方法
不执行全端口扫描，可以尝试标准端口或指定端口扫描。
D.11 扫描 hp 刀箱管理地址时-onboard adminitrator 界面异常不能
登录
问题现象
目前查看网关各HP刀箱设备，出现大量严重错误，如图 D-1所示。咨询HP工程师，得出
结论为ilo与刀片之间的连接出现问题，ilo无法获取刀片的信息，导致刀片出现严重告警。
 此情况不会影响业务正常运行，只是无法从OA上管理刀片。
 解决方法为拔出刀片重新插入刀箱（经验证一台未使用的刀片，刀片能恢复
正常）。
版权所有 © 绿盟科技 373 V6.0R04F03 限制分发级