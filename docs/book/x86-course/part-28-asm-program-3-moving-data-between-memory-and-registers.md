## Part 28 - ASM 程序 3 \[在内存与寄存器之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在我们的第三个程序里, 我们会演示如何在内存与寄存器之间移动数据.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520175192505.jpg"/></div>

具体来说, 我们会把常量整数里十进制 10 这个值移入 ECX.

记住, 汇编时我们输入:

__as -32 -o moving\_data\_between\_memory\_and\_registers.o moving\_data\_between\_memory\_and\_registers.s__

要链接目标文件, 我们输入:

__ld -m elf\_i386 -o moving\_data\_between\_memory\_and\_registers moving\_data\_between\_memory\_and\_registers.o __

期待下周与大家再见, 届时我们会深入调试我们的第三个汇编程序!