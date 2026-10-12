## Part 20 - 引导扇区基础 \[Part 3\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

对于熟悉汇编的人来说, 接下来这几周甚至几个月可能会显得我们进展非常缓慢, 不过我们的目标是帮助那些对硬件了解不多的人更好地理解支撑云端的这些系统本身.

绝大多数 AWS 和 Azure 以及许多其他云服务都使用基于 x64 的操作系统. 理解这些系统启动时发生了什么很有价值, 这就是为什么我们要用一个非常缓慢的过程, 逐个查看机器加载时引导扇区的每一部分.

我们来看一下源代码. 用 Vim 或 Nano 跟着做.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1545990601552.jpg"/></div>

上周我们学习了第 1 行和第 2 行的操作码, 这些就不必复习了. 今天我们在代码里加入一个字节的数据. 注意这是一个十六进制数, 检查二进制文件时它会与之对应. 在以后的课程中我们会看看用十进制和其他进制时是什么样子.

我们来编译. 如果你还没有安装 NASM, 请确保输入 __sudo apt-get install nasm__.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1545990746117.jpg"/></div>

我们在十六进制编辑器里看看这个二进制文件. 我用的是 GHex, 因为我坚持 GNU 传统, 就像以后的课程中我们会使用名为 GDB 的 GNU 调试器一样. 这些都在你的 Linux 系统上, 因为这些教程我用的都是 Ubuntu.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1545990876404.jpg"/></div>

上周我们看到 __EB__ 和 __FE__ 对应我们的 __INC__ 和 __JMP__ 指令. 如果还不清楚, 请重读上周的课程. 我们看到第 3 个字节是 __10__. 记住这是十六进制, 所以它的十进制值是 __16__.

下周我们会继续往代码里添加内容, 在操作系统开发系列中向前推进.