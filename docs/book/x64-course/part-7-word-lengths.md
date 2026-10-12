## Part 7 - 字长

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在深入架构之前, 我们先谈谈各种位是如何定义的, 以及它们在处理器内部是如何组织的.

在 x64 和 x86 中, 我们都把字节 (byte) 定义为 8 位.&nbsp;我们把字 (word) 定义为 16 位.&nbsp;我们把双字 (double word) 定义为 32 位, 把四字 (quadword) 定义为 64 位.&nbsp;最后我们把双四字 (double quadword) 定义为 128 位.&nbsp;

Intel 处理器存储字节时采用我们所说的 "小端序" (little endian), 也就是说低位有效字节存放在较低的内存地址中.&nbsp;我们举一个简单的 16 位即 2 字节值的例子.&nbsp;在磁盘上是 0xAABB.&nbsp;进入内存后它被存成 0xBBAA, 希望这能给出一个直观的印象, 因为这个概念很容易让人困惑.

请记住, 8 位构成一个字节.&nbsp;4 位也称为半字节 (nibble), 它等同于一个十六进制数字.

下周我们深入通用架构! 敬请期待!