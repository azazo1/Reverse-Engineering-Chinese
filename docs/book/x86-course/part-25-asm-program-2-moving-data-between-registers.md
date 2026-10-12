## Part 25 - ASM 程序 2 \[在寄存器之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在第二个程序里, 我们会演示如何在寄存器之间移动数据. 把一个寄存器中的数据移到另一个寄存器, 是移动数据最快的方式. 为了速度, 只要工程上做得到, 就总是建议把数据保持在寄存器之间.

具体来说, 我们会把 EDX 中的值移入 EAX. 我们会用一个简单的立即值来初始化这个程序, 也就是十进制的 22, 它会进入 EDX, 最终进入 EAX.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520145020169.jpg"/></div>

请记住, 你只能在大小相同的寄存器之间移动数据. 我们知道 EAX 和 EDX 是 32 位寄存器. 我们知道这两个寄存器各自都可以用它们的 16 位形式访问, 分别是 ax 和 dx. 你不能把 32 位的值移入 16 位的值, 反过来也不行.

期待下周与大家再见, 届时我们会深入调试第二个汇编程序!