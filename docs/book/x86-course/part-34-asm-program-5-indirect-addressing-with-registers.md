## Part 34 - ASM 程序 5 \[用寄存器间接寻址\]

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在我们的第五个程序里, 我们会演示如何用寄存器来操纵间接寻址.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520086819422.jpg"/></div>

如上面所示, 我们可以把不止一个值放进内存. 过去我们的内存位置只包含一个单独的值. 在上面你可以看到 constants 的值包含了 11 个独立的值.

这样就产生了一组按顺序放进内存的数据值. 每个数据值占用一个内存单位, 也就是一个整数, 即 4 个字节.

我们必须用索引系统来确定这些值, 因为我们上面创建的东西是一个数组.

我们会使用索引内存模式, 其中内存地址由基地址, 要加到基地址上的偏移地址, 以及数据元素的大小共同决定, 在我们的例子里就是一个 4 字节的整数, 此外还要用一个索引来决定选中哪个数据元素.

记住, 数组从索引 0 开始. 因此在上面这段代码里, 我们看到 1 被移入 edi, 它是第 2 个索引, 最终会进入 ebx.

我们会在下一节调试 Lesson 里更深入地讲它, 不过我希望你花点时间研究上面的代码, 好好把握其中发生的事情.

记住, 汇编时我们输入:

__as -32 -o indirect\_addressing\_with\_registers.o indirect\_addressing\_with\_registers.s__

要链接目标文件, 我们输入:

__ld -m elf\_i386 -o indirect\_addressing\_with\_registers indirect\_addressing\_with\_registers.o __

期待下周与大家再见, 届时我们会深入调试我们的第五个汇编程序!