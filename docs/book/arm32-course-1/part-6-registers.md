## Part 6 - 寄存器

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

我们的 ARM 微处理器带有内部存储, 因为不需要访问外部内存, 任何操作都快得多. 它有两种模式, User 和 Thumb. 我们会把重点放在 User Mode 上, 因为我们的目标终究是在 Linux 操作系统里为片上系统 (system on chip) 做开发, 而不是更适合单片机设备的裸机 (bare-metal) 编程.

在 User Mode 下我们有 16 个寄存器和一个 CPSR 寄存器, 每个都占一个字长, 也就是各占 32 位, 或者说各占 8 个字节.

R0 到 R12 是多用途寄存器, 而 R13 到 R15 以及 CPSR 各有专门的用途. 我们用一个简单的表来说明.

<pre spellcheck="false">R0 GPR (通用寄存器)
R1 GPR (通用寄存器)
R2 GPR (通用寄存器)
R3 GPR (通用寄存器)
R4 GPR (通用寄存器)
R5 GPR (通用寄存器)
R6 GPR (通用寄存器)
R7 GPR (通用寄存器)
R8 GPR (通用寄存器)
R9 GPR (通用寄存器)
R10 GPR (通用寄存器)
R11 GPR (通用寄存器)
R12 GPR (通用寄存器)
R13 栈指针 (Stack Pointer)
R14 链接寄存器 (Link Register)
R15 程序计数器 (Program Counter)
CPSR 当前程序状态寄存器 (Current Program Status Register)
</pre>

非常关键的一点是, 我们要非常细致地理解寄存器. 到这一步我们已经明白, R0 到 R12 是通用寄存器, 在编写程序时用来操作数据; 此外, 当你在手机或其他 ARM 设备上从一段十六进制转储 (hex dump) 出发去拆解或逆向二进制程序时, 不管这个程序是用什么高级语言写的, 它最终都要落到汇编上, 而你必须理解寄存器以及它们如何工作, 才能搞清楚上面提到的这类操作.

我们所用的这颗芯片属于加载-存储型机器. 也就是说, 我们把某个寄存器或内存位置的内容加载进一个寄存器, 也可以把一个寄存器的内容存储到某个内存或寄存器位置. 例如:

<pre spellcheck="false">ldr, r4, [r10] @ 
&nbsp;&nbsp;&nbsp; 把 r10 的内容加载到 r4, 如果 r10 的值是 
&nbsp;&nbsp;&nbsp; 比如说十进制 22, 那么 22 就会进入 r4

str, r9, [r4] @ 
&nbsp;&nbsp;&nbsp; 把 r9 的内容存储到 r4 指向的位置, 如果 r9 的值是 
&nbsp;&nbsp;&nbsp; 十六进制的 0x02, 那么 0x02 就会被存到 r4 指向的位置
</pre>

这里的 @ 只是告诉编译器, 某一行中它后面的内容是注释, 会被忽略.

接下来几周我们会慢慢来看每一个专用寄存器, 让你充分理解它们的作用.

下周我们深入了解程序计数器! 敬请期待!