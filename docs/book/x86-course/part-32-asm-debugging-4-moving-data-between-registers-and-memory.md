## Part 32 - ASM 调试 4 \[在寄存器与内存之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在我们的第四个程序里, 我们会演示如何在寄存器与内存之间移动数据.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520642123733.jpg"/></div>

具体来说, 我们会把立即值十进制 777 移入 EAX. 然后我们把 EAX 中保存的那个值移入内存里的 constant 值, 它在运行时最初的值是十进制 10. 记住, 这个值本来可以叫任何名字, 不过我把它叫作 constant, 因为它是在 .data 段里被设置成常量的.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520642123169.jpg"/></div>

如你在上面所见, 我们进入 GDB 后清楚地看到 constant 的值已被替换成十进制 777, 而在代码里, 它在本教程开头那段代码的第 6 行中明明被设成了十进制 10.

我们可以清楚地看到, 在代码的第 16 行, 十进制 777 这个值被成功地移入了 EAX, 也移入了内存中的 constant 值.

期待下周与大家再见, 届时我们会深入修改我们的第四个汇编程序!