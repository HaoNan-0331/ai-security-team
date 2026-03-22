# D.2  扫描HP-UNIX时出现auth服务异常，进而造成HA失效

> 来源: 第375页 - 第375页

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

绿盟远程安全评估系统安装部署手册
D.3 RSAS 扫描 IBM AIX 集群服务器时造成服务器宕机
原因
AIX上的集群服务HAES/HACMP存在脆弱性，当端口扫描到HAES/HACMP服务相关端口时会
导致服务器宕机。
影响版本
IBM AIX操作系统
HACMP: 4.4.X
HACMP: 4.5
HACMP: 5.1
HACMP: 5.2
原理
当集群服务器的某个节点 clstrmgr 服务接收到非法数据包（端口扫描数据包）时，会引起
clstrmgr 服务退出，这时其他服务器尝试接管服务停止的服务。如果所有节点都接收到非法
数据包（端口扫描数据包）时，整个集群将宕机。
⚫ 临时解决方法：
1. 在AIX服务器上使用ipfilter过滤掉除应用以外所有端口。
2. 扫描时避开AIX集群服务器。
⚫ IBM官方在2008年已公布了该宕机风险的说明：
https://www-304.ibm.com/support/docview.wss?uid=isg3T1000505
D.4 扫描 SCO Unix 5.0.6 服务器后影响 TELNET 终端用户登录服务
器
原因
RSAS缺省会进行弱口令猜测，而服务器配置了登录3次失败，自动锁定账号的功能，RSAS
在猜测口令时，服务器锁定了帐号。
受影响的版本
系统配置了帐号锁定策略，如登录失败3次自动锁定账号。
受影响的系统：windows登录帐号、UNIX系统TELNET帐号。
规避方法
在新建扫描任务时，在附加选项中去掉口令猜测。
版权所有 © 绿盟科技 369 V6.0R04F03 限制分发级