## Part 29 - ASM 调试 3 \[在内存与寄存器之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们来调试!&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520241537282.jpg"/></div>

具体来说, 我们会把常量整数里十进制 10 这个值移入 ECX.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520590508110.jpg"/></div>

我们以安静模式打开 GDB, 在 \_start 处下断点, 然后按照上面的命令运行.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520193652626.jpg"/></div>

如我们所见, 当我们 info registers 时, ECX 的值是 0.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520590507589.jpg"/></div>

在我们两次单步步入之后, 现在看到 ECX 的值是十进制 10, 也就是十六进制 0xa.

期待下周与大家再见, 届时我们会深入修改我们的第三个汇编程序!