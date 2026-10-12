## Part 23 - ASM 调试 1 \[移动立即数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们先把这个二进制文件加载到 GDB 中.

要加载进 GDB 请输入:

__gdb -q moving\_immediate\_dat__

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520242394717.jpg"/></div>

我们先输入 b \_start 在 start 上设置一个断点.

然后我们可以输入 __r__ 来运行程序.

接着要开始反汇编, 我们只需输入 __disas__.

为了便于正确调试, 我们写了一个 __nop__, 从操作码 (OPCODE) 的角度看它表示无操作, 也就是 0x90, 断点正确地命中了它. 在编写汇编程序时这是一个好习惯.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520193761435.jpg"/></div>

正如我此前多次说过的, 原生语法就是你在上面看到的 AT&amp;T 语法. 我故意痛苦地来回切换, 是为了让你对两种语法都感到自在, 不过往后我会坚持使用 AT&amp;T 语法, 只是想先给你看几个两种语法的例子. 我再说明一次, 如果你什么时候想看 Intel 语法, 只要输入 set-disassembly-flavor intel, 就能得到你想要的东西.

我们先用 si 命令, 它的意思是单步步入 (step-into), 用来前进到下一条指令. 我们在 __\_start+0__ 看到的是, 你把十六进制值 __0x64__ 移入 __EAX__. 这只是把十进制 __100__, 或者说计算机眼中的十六进制 __0x64__, 移入 __EAX__, 演示了把立即值移入寄存器.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520144825193.jpg"/></div>

我们再次单步步入, 然后使用 i r 命令, 注意它们之间有一个空格, 它会给出 CPU 寄存器状态的信息.&nbsp;可以看到 EAX 现在的值是十六进制的 0x64, 也就是十进制的 100.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520492698882.jpg"/></div>

在我们再次单步步入并执行 __disas__ 之后, 可以看到我们接着把 __0x50__ 这个值移入了 __buffer__ 标签, 你可以回看上周的源代码来确认.

当处理非寄存器数据时, 我们可以像上面那样使用 print 命令, 输入 __print /x buffer__, 它清楚地显示 buffer 里面的值是 __0x50__. __/x__ 标记表示以十六进制显示这个值.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520492696905.jpg"/></div>

因此你可以回看本教程上面的第 2 张幻灯片, 你会看到在 __\_start+5__ 处, 立即值 __0x50__ 被加载到 __buffer__ 标签中, 在这个例子里也就是 __buffer__ 的地址 __0x8049090__, 我们可以用 examine 指令来检查它, 输入 __x/xb 0x8049090__, 它会显示该位置的一个十六进制字节, 结果是 __0x50__.

我们会用每一个程序示例都这样做, 以便深入调试过程. 如果有任何问题, 请在下面的评论里提出.

期待下周与大家再见, 届时我们会开始创建第一个汇编修改!