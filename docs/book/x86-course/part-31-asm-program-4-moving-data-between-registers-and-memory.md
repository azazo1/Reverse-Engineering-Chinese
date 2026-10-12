## Part 31 - ASM 程序 4 \[在寄存器与内存之间移动数据\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在我们的第四个程序里, 我们会演示如何在寄存器与内存之间移动数据.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520625191381.jpg"/></div>

具体来说, 我们会把立即值十进制 777 移入 EAX. 然后我们把 EAX 中保存的那个值移入内存里的 constant 值, 它在运行时最初的值是十进制 10. 记住, 这个值本来可以叫任何名字, 不过我把它叫作 constant, 因为它是在 .data 段里被设置成常量的.

你可以清楚地看到它能够被操纵, 所以它并不是常量. 我故意选用 constant 这个名字, 是因为如果它是纯正的常量形式, 这个值就会一直保持为十进制 10, 也就是十六进制 0xa.

这段代码纯粹是学术练习, 因为可变数据通常应该放在 .bss 段里, 不过我想演示上面这种做法是可行的, 以展示汇编语言绝对的灵活性.

记住, 汇编时我们输入:

__as -32 -o moving\_data\_between\_registers\_and\_memory.o moving\_data\_between\_registers\_and\_memory.s__

要链接目标文件, 我们输入:

__ld -m elf\_i386 -o moving\_data\_between\_registers\_and\_memory moving\_data\_between\_registers\_and\_memory.o __

期待下周与大家再见, 届时我们会深入调试我们的第四个汇编程序!