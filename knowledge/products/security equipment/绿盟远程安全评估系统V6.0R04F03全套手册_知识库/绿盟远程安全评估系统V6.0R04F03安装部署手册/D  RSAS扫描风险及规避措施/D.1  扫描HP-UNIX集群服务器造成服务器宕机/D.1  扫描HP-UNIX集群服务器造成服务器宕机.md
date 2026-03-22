# D.1  扫描HP-UNIX集群服务器造成服务器宕机

> 来源: 第374页 - 第374页

绿盟远程安全评估系统安装部署手册
D
RSAS 扫描风险及规避措施
扫描任何设备都是有风险的，但有的风险在可控范围之内（如扫描终端pc等），但如果涉及
被扫描的设备角色、业务等十分重要（如服务器集群、网络设备等），风险一旦出现，将造
成非常大的损失。因此在扫描此类设备之前，需要做一定的规避措施，但未知风险是仍然存
在的。
RSAS在对目标网络或主机进行漏洞扫描时，会发出一系列的探测数据包，这些数据包主要
包括存活判断数据包、端口扫描数据包、信息获取数据包、和漏洞检测数据包。
虽然RSAS在设计时已经最大限度地考虑了如何减少对扫描目标主机的影响，但是由于个别
系统设计存在严重的缺陷，所以当RSAS的探测数据包对这些系统扫描时，还是可能会引起
这些系统的拒绝服务或重启。
所以对业务系统进行扫描时建议在不对外提供服务的时间扫描或业务下线的时间扫描，扫描
前需要系统管理员在现场看护，如果出现拒绝服务，需要手工重启恢复服务。
下面是某些系统在扫描时曾遇到的风险的情况、原因和规避方法：
D.1 扫描 HP-UNIX 集群服务器造成服务器宕机
原因
HP-unix集群服务存在拒绝服务漏洞。漏洞描述（HP-UXcmcld Service Port Scan Remote DoS）
详细信息参见：
http://osvdb.org/show/osvdb/59821
http://h10025.www1.hp.com/ewfrf/wc/document?cc=us&lc=en&dlc=en&docname=c02678446
受影响的版本
Serviceguard A.11.19 on HP-UX 11.23
Serviceguard A.11.19 on HP-UX 11.31
原理
群集守护程序：cmcld（cluster management）通过向 Serviceguard 群集内其他节点上的 cmcld
守护程序发送心跳线消息，该守护程序可确定群集成员。它按照实时优先级运行且锁定在内
版权所有 © 绿盟科技 367 V6.0R04F03 限制分发级

绿盟远程安全评估系统安装部署手册
存中。cmcld 守护程序在内核中设置了一个安全定时器，用于检测内核挂起。如果此定时器
未由cmcld 定期复位，则内核将产生系统 TOC（即控制转移），也就是立即暂停系统而不是
进行正常关闭。发生这种情况的原因可能是 cmcld 无法与大多数群集成员通信；或者是因
为 cmcld 异常退出、中止以及无法运行足够长的时间并无法更新内核计时器（内核挂起）。
在因安全定时器过期而导致 TOC 之前，消息将会写入 /var/adm/syslog/syslog.log 和内核消
息的缓冲区中，并执行系统转储。
⚫ 现象说明：
系统A和系统B在一个群集组当中，它们之间通过该进程互相进行通信，但是由于RSAS
对系统A的扫描，导致可能在短暂的瞬间系统A只忙于和RSAS的交互，而无法和系
统B进行通信，于是会立即暂停系统。上述链接报告的就是该服务很容易导致DOS攻
击，只要发起大流量的报文，就可以使得整个集群系统崩溃。
⚫ 规避方法：
如果不确认HP服务器是否安装了补丁，扫描时需要避开HP-UNIX集群服务器。
⚫ 解决方案：
− 安装补丁
分析受影响系统后，所需补丁如下。使用补丁后，扫描过程中HP-UNIX不再出现宕
机现象。（请对应好版本，不同版本有不同补丁）
受影响版本：ServiceguardA.11.19 on HP-UX 11.23 补丁：PHSS_ 40793
受影响版本：ServiceguardA.11.19 on HP-UX 11.31 补丁：PHSS_ 40794
− 使用防火墙屏蔽以下端口端口：
hacl-gs 5301/tcp # HA Cluster General Services
hacl-cfg 5302/tcp # HA Cluster TCP configuration
hacl-cfg 5302/udp # HA Cluster UDP configuration
hacl-probe 5303/tcp # HA Cluster TCP probe
hacl-probe 5303/udp # HA Cluster UDP probe
hacl-local 5304/tcp # HA Cluster Commands
hacl-test 5305/tcp # HA Cluster Test
hacl-dlm 5408/tcp # HA Cluster distributed lock manager
D.2 扫描 HP-UNIX 时出现 auth 服务异常，进而造成 HA 失效
HP-UX版本：11.31
服务：TCP113端口，auth服务
处理方法
研发人员查看扫描日志后，发现对改端口并没有调用插件，只是进行了服务识别：发送一条
get请求"GET / HTTP/1.0\r\n\r\n"，根据返回的特征判断出auth服务。这条get请求不会对auth
服务造成伤害。因此判断非RSAS问题。
⚫ 客户提供了syslog日志，分析后得出原因如下：
syslog报错的原因为inetd启动时没有加–c参数：
⚫ 可参考以下链接解决：
http://h10025.www1.hp.com/ewfrf/wc/document?docname=c02020078&cc=lb&dlc=en&lc=
fr
版权所有 © 绿盟科技 368 V6.0R04F03 限制分发级