## Part 10: 通用寄存器

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

通用寄存器 (general-purpose register) 用于在处理器处理数据时临时存放这些数据. 这些寄存器随时间发生了巨大的演变, 并且仍在继续演变. 就我们的目的而言, 我们将聚焦于 32 位 x86 架构.

每一代新的通用寄存器都被设计为&nbsp;向后兼容此前的处理器. 这意味着在 8080 芯片上使用 8 位寄存器的代码, 在今天的 64 位芯片组上依然能运行.

通用寄存器可以用来保存任何类型的数据, 其中一些寄存器在程序中形成了特定的用途. 让我们回顾一下 IA-32 架构中的 8 个通用寄存器.

__EAX__: 用于算术计算的主寄存器. 也被称为累加器 (accumulator), 因为它保存算术运算的结果和函数返回值.

__EBX__: 基址寄存器 (Base Register). 指向 DS 段中数据的指针. 用于保存程序的基地址.

__ECX__: 计数寄存器 (Counter register) 常用于保存一个数值, 表示某个过程需要重复多少次. 用于循环和字符串操作.

__EDX__: 一个通用寄存器. 另外还用于 I/O 操作. 此外还会把 EAX 扩展到 64 位.

__ESI__: 源索引寄存器 (Source Index register). 指向由 DS 寄存器所指段中数据的指针. 在字符串和数组操作中用作偏移地址. 它保存读取数据所在的地址.

__EDI__: 目的索引寄存器 (Destination Index register). 指向由 ES 寄存器所指段中数据 (或目的地址) 的指针. 在字符串和数组操作中用作偏移地址. 它保存所有字符串操作隐含的写入地址.

__EBP__: 基址指针 (Base Pointer). 指向栈上 (SS 段中) 数据的指针. 它指向当前栈帧 (stack frame) 的底部. 用于引用局部变量.

__ESP__: 栈指针 (Stack Pointer) (位于 SS 段中). 它指向当前栈帧的顶部. 用于引用局部变量.

请记住, 上述每个寄存器的长度都是 32 位, 也就是 4 字节. EAX, EBX, ECX 和 EDX 寄存器各自低位的那 2 个字节可以用 AX 来引用, 而 AX 又可以细分为高字节 AH, BH, CH 和 DH, 以及低字节 AL, BL, CL 和 DL, 每个都是 1 字节.

此外, ESI, EDI, EBP 和 ESP 可以用它们对应的 16 位形式来引用, 即 SI, DI, BP, SP.

对于没有学过计算机工程的人来说, 这可能有点令人困惑, 不过让我用下面的表格来说明:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520145792750.jpg"/></div>

EAX 以 AX 作为它的 16 位片段, 然后你还可以进一步把 AX 细分为表示低 8 位的 AL 和表示高 8 位的 AH. EBX, ECX 和 EDX 也是如此. EBX 以 BX 作为它的 16 位片段, 然后你可以进一步把 BX 细分为表示低 8 位的 BL 和表示高 8 位的 BH. ECX 以 CX 作为它的 16 位片段, 然后你可以进一步把 CX 细分为表示低 8 位的 CL 和表示高 8 位的 BH. EDX 以 DX 作为它的 16 位片段, 然后你可以进一步把 DX 细分为表示低 8 位的 DL 和表示高 8 位的 DH.

ESI, EDI, EBP 和 ESP 可以按如下方式拆分成它们的 16 位片段:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520613988729.jpg"/></div>

ESI 的 16 位片段是 SI, EDI 的 16 位片段是 DI, EBP 的 16 位片段是 BP, ESP 的 16 位片段是 SP.

在下一节教程中, 我们将继续讨论 IA-32 架构, 介绍段寄存器.