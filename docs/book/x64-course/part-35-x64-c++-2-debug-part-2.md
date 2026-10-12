## Part 35 - x64 C++ 2 调试 \[Part 2\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们回顾一下代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561714810492.png"/></div>

编译:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561714836259.jpg"/></div>

运行:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561714869555.jpg"/></div>

多年来我一直把 GDB 当作首选的调试器 (debugger). 原因在于, 世界上几乎所有跑 IoT 和服务器的 Linux 系统上都有它. 此外它也有 Windows 版本.

在这件事上我纠结了很久, 但最终还是决定介绍另一个基于终端的调试器, 叫做 Radare 2. 我之所以这么喜欢 Radare 2, 是因为它同样是基于终端的, 但功能集更强大. 如果你和我一样在跑 Kali Linux 虚拟机, 照着下面做就行.

我们以写模式打开这个二进制文件, 直接分析它.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561716186925.jpg"/></div>

好, 这里信息量很大, 我们拆开来看. 首先, 输入 '__r2 -w ./1__' 以写模式打开 Radare 2, 然后用 '__aaa__' 命令分析这个二进制文件. 接着用 '__s sym.main__' 定位到二进制的 main 例程, 也就是我们的入口点. 最后执行 '__pdf__' 命令反汇编这个二进制文件.

我们看到所谓的序言 (prologue), 把栈基址指针 __rbp__ 压入栈. 然后把 __rsp__ 移到 __rbp__ 里妥善保存, 再在栈上预留 __0x10__ 个十六进制字节, 也就是 16 个十进制字节, 给我们的字符串腾地方.

如果这些你完全看不懂, 请回到教程系列的开头复习基础汇编和寄存器, 因为在我们继续往下走之前, 你务必理解这些内容.

我们可以清楚地看到 '__Hello World\\n__' 这个 qword 位于内存地址 __0x2005__ 处, 然后还能看到我们调用 C++ 的输出流库 __cout __, 把字符串显示到终端.

我们检查一下 __0x2005__, 确认字符串确实在那个位置:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1561715552920.jpg"/></div>

下周我们会修改这个值, 改动这个二进制文件. 强烈建议大家装一个免费的 VirtualBox, 拿到 Kali Linux 的 VirtualBox 镜像, 顺便也把 Vim 装上.

这些内容在我之前的系列里都有教程. 敬请期待下周的修改!