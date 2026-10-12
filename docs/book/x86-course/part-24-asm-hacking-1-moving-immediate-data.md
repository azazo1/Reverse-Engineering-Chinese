## Part 24 - ASM 修改 1 \[移动立即数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们先把这个二进制文件加载到 GDB 中.

要加载进 GDB 请输入:

__gdb -q moving\_immediate\_data__

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520534645555.jpg"/></div>

我们先输入 __b \_start__ 在 start 上设置一个断点.

然后我们可以输入 __r__ 来运行程序.

接着要开始反汇编, 我们只需输入 __disas__.

为了便于正确调试, 我们写了一个 __nop__, 从操作码 (OPCODE) 的角度看它表示无操作, 也就是 __0x90__, 断点正确地命中了它. 在编写汇编程序时这是一个好习惯.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520241969888.jpg"/></div>

让我们找点乐子! 这时我们 __si__ 一次, 再做一次 __i r__, 看看 __0x64__ 是否真的已经被移入 __EAX__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520148350561.jpg"/></div>

可以看到 __EAX__ 的值是 __0x64__, 也就是十进制的 __100__. 现在让我们修改这个值, 把 __EAX__ 设成像 __0x66__ 这样的值, 输入 __set $eax = 0x66__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520194300522.jpg"/></div>

砰! 成了! 你可以在这里看到汇编的终极力量! 我们刚刚把这个值从 __0x64__ 改成了 __0x66__, 也就是从十进制的 __100__ 改成了 __102__. 这是一个微不足道的例子, 不过你可以清楚地看到, 当你学会掌握这些概念后, 你就能对计算机拥有更大的掌控力. 我们创建的每一个程序, 都会配上一节像这样非常简单的 Lesson, 在其中我们至少劫持代码的一个部分, 这样我们不仅能看到程序是如何被创建和调试的, 还能看到我们如何把它操纵成任何我们想要的样子.

期待下周与大家再见, 届时我们会开始创建第二个汇编程序!