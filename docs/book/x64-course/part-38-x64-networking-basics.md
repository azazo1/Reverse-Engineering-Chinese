## Part 38 - x64 网络基础

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

好, 那接下来呢? 我们在世上处于什么位置? 我们的目的是什么? 我该专注于什么? 我该学什么?

今天有超过 300 亿台设备连着互联网. 不过, 所有基础架构里共同的那条主线都是 C 编程语言.

我们已经确认, 网络可以用一个非常高层级的伪框架来描述, 叫做 OSI 模型 (OSI Model), 它一共有 7 层.

__P__LEASE __D__O __N__OT __T__HROW __S__AUSAGE __P__IZZA __A__WAY. 好, 我没疯, 好吧, 我确实疯了, 但这是记住 OSI 模型各层的好办法, 也是大家公认的标准方法; OSI 模型就是我们的开放系统互连模型 (Open Systems Interconnection).

1)__物理层 (PHYSICAL LAYER)__ - 原始电气层, 读取以太网线上的电压, 或者读取 Wi-Fi 的 RF (radio frequencies, 射频). 相关协议: USB, DSL, ISDN, Infrared 等...

2)__数据链路层 (DATA LINK LAYER) __- 处理节点之间消息如何开始和结束, 也就是成帧 (framing), 其中包含一些纠错, 检错以及流量控制. 相关协议: Ethernet, VLAN 等...

3)__网络层 (NETWORK LAYER)__ - 在不同网络的节点之间传输数据包, 这涉及路由. 相关协议: IPX, NAT, ICMP, ARP 等...

4)__传输层 (TRANSPORT LAYER)__ - 在两个主机之间可靠地传递数据, 为此必须把数据切分成块再发送. 相关协议: NetBIOS, TCP, UDP 等...

5)__会话层 (SESSION LAYER)__ - 除了终止对话之外, 还加入了检查点与恢复. 相关协议: SMB, SOCKS 等...

6)__表示层 (PRESENTATION LAYER)__ - 在这里为应用程序创建数据结构和呈现形式, 我们会用到编码, 序列化和加密. 相关协议: TLS, SSL 等...

7)__应用层 (APPLICATION LAYER)__ - 使用 Web 界面的网页浏览器和应用, 比如电子邮件等. 相关协议: DHCP, DNS, HTTP, HTTPS, POP3, SMTP, FTP, TELNET 等...

当我们浏览一个网站时, 从物理层开始一路向上到应用层, 到达服务器时它在应用层, 然后一路向下回到物理层, 再走一遍这个循环.

这是一系列重要的概念, 任何基础网络知识里你都必须理解它们. 这并不是一门网络课程, 我们只会非常简短地碰一下这些概念, 所以如果你卡住了, 建议你到 YouTube 上找一门免费的网络课程. 我想先把一些基础理论过一遍, 这样我们才能动手写 C 网络应用.