## Part 26 - ASM 调试 2 \[在寄存器之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们调试下面这第二个程序:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520143823093.jpg"/></div>

让我们启动 GDB, 在 \_start 上打断点, 运行这个二进制文件并执行 disas:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520559684472.jpg"/></div>

现在我们 __si__ 两次, 再执行 __i r__:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520203219432.jpg"/></div>

可以看到, __0x16__ 也就是十进制的 __22__ 确实成功移入了 EDX. 现在我们再次 __si__.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520144473531.jpg"/></div>

如你所见, 我们已经成功把 EDX 移入了 EAX.

期待下周与大家再见, 届时我们会深入修改第二个汇编程序!