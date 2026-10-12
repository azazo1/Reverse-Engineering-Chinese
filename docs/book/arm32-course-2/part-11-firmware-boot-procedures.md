## Part 11 - 固件启动流程

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们花点时间聊聊, 第一次给我们的 Raspberry Pi 设备上电时会发生什么.

Pi 一接到电源, 第一个运行的就是图形处理器, 因为主处理器被保持在复位状态, 于是 GPU 开始执行代码.&nbsp;ROM 从 SD 卡读取, 读到 __bootcode.bin __, 它会被加载到 C2 缓存中的内存里, 并打开其余的 RAM, 接着 __start.elf__ 就会被加载.

__start.elf __是图形处理器用的一个操作系统, 它会读取 __config.txt __, 这个文件你可以自行修改.&nbsp;随后 __kernel.img __会被加载到内存中的 __0x8000__, 也就是 Linux 内核所在的位置.

一旦加载完成, __kernel.img __就会开启 CPU, 并在内存中的 __0x8000 __处开始运行.&nbsp;

如果我们愿意, 可以创建自己的 __kernel.img__, 把机器码硬编码进一个文件, 替换掉原始镜像, 然后重启.&nbsp;要记住, ARM 字长是 32 位, 从 bit 0 一直到 bit 31.&nbsp;

如前所述, 当 __kernel.img__ 被加载时, 第一个字节也就是 8 位, 会被加载到地址 __0x800__.

让我们打开一个十六进制编辑器, 写入以下内容:

__FE FF FF EA__

把文件保存为 __kernel.img__ 并重启.

"好吧, 什么都没发生, 太糟了!"

其实确实发生了点什么, 你创建了自己的第一个裸机固件!&nbsp;该开香槟庆祝了!&nbsp;

当 Pi 启动时, 下面这段代码在执行到 __kernel.img __时会加载以下内容:

__FE FF FF EA__

__@ 地址 0x8000, 会加载 0xfe.__

__@ 地址 0x8001, 会加载 0xff.__

__@ 地址 0x8002, 会加载 0xff.__

__@ 地址 0x8003, 会加载 0xea.__

"那么到底发生了什么?"

这组指令只是执行了一个无限循环.&nbsp;

查阅数据手册:

<a href="https://www.raspberrypi.org/wp-content/uploads/2012/02/BCM2835-ARM-Peripherals.pdf" rel="nofollow noopener" target="_blank">https://www.raspberrypi.org/wp-content/uploads/2012/02/BCM2835-ARM-Peripherals.pdf</a>

上面这段代码由 3 部分组成:

1)条件字段 - 设为始终 (Always)

2)操作码 - 分支 (Branch)

3)偏移 - 在当前所在位置内要移动多远

__条件 - bits 31-28:&nbsp;0xe 或 1110__

__操作码 - bits 27-24:&nbsp;0xa 或 1010__

__偏移 - bits 23-0 -2__

我知道这些内容一下子要理解起来可能有点多, 但花时间去读上面链接的那份数据手册是至关重要的. 如果你真的有热情弄懂上面的内容, 就不要偷工减料.&nbsp;去读数据手册!

我会费尽心力把每一处都一步步拆开讲, 但像上面这样的练习, 我是要求你自己去查阅上面那份数据手册, 这样你才能学会更好地理解: 当你卡在某段例程或某组机器码上时, 该去哪里找答案.&nbsp;现在就是这样的时候, 请你读一读并研究上面那份数据手册!

"我好无聊!&nbsp;这些破东西到底有什么要紧?"

很高兴你问了!&nbsp;今天地球上最危险的恶意软件就是 rootkit 这一类.&nbsp;如果你对上面的内容没有基本的理解, 那么随着你认识不断深入, 你连 rootkit 是什么都无从谈起.

任何人都可以用自己改过的版本替换 __kernel.img__ 文件, 从而从启动开始就完全掌控整个过程.

下周我们会深入冯诺依曼架构.