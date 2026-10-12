## Part 27 - ASM 修改 2 \[在寄存器之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们修改下面这第二个程序:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520583727180.jpg"/></div>

让我们启动 GDB, 在 \_start 上打断点, 运行这个二进制文件并执行 disas:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520066773312.jpg"/></div>

现在我们 __si__ 两次, 再执行 __i r__:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520143945686.jpg"/></div>

可以看到, __0x16__ 也就是十进制的 __22__ 确实成功移入了 EDX. 这就是我们在上一节 Lesson 里做的事, 不过在这里我们要把这个值修改成别的.

例如我们可以执行 __set $edx = 0x19__:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520583727155.jpg"/></div>

如你所见, 我们轻松地把 __EDX__ 的值修改成了 __0x19__, 也就是十进制的 __25__.

既然我们现在开始接触非常简单的汇编语言程序, 希望你能看到一些非常简单的模式. 关键在于理解如何操纵值和指令, 从而完全掌控这个二进制文件.

在本教程余下的部分, 我们会继续以蜗牛般的速度前进, 因为我的目标是把如何理解 x86 汇编的例子切得很小, 一口一块地给到大家.

期待下周与大家再见, 届时我们会开始编写第三个汇编程序!