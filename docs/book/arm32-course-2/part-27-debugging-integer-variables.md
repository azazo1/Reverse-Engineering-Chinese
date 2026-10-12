## Part 27 - 调试整型变量

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下我们的代码.&nbsp;我想再次引用上周 Lesson 中下面的内容, 来强调整数相关的机制到底是怎么一回事.

一个 32 位寄存器可以存储 2^32 个不同的值. 32 位中能存储的整数取值范围取决于所用的整数表示法. 对于最常见的两种表示法, 以 (无符号) 二进制数表示时, 范围是 0 到 4,294,967,295 (2^32 - 1), 以二进制补码表示时, 范围是 -2,147,483,648 (-2^31) 到 2,147,483,647 (2^31 - 1).

请记住, 使用 32 位内存地址, 你最多可以直接访问 4 GB 的字节可寻址内存.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520217390524.jpg"/></div>

开始调试!

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520233314454.jpg"/></div>

我们看到在 __main+12 __处, 地址 __0x10730 __把数据加载进 __r3__.&nbsp;让我们仔细看看.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520192010424.jpg"/></div>

当我们查看 __0x10730__ 内部的数据时, 可以清楚地看到整数 __777__ 就在那里.&nbsp;继续执行时, 我们看到 __777 __被回显到终端, 这很合理, 因为我们在 c++ 中用了 __cout__ 函数.\#linux \#arm \#asm \#cplusplus \#reverseengineering

下周我们将深入探讨修改整型变量.