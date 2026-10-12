## Part 12 - 加载有效地址

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

当一个二进制文件在 RAM 中执行时, 操作系统会把代码映射到数据段中它在内存里找到的空闲空间.

加载有效地址 (Load Effective Address) 会把给定的内存地址作为指向任意给定变量的指针加载进来. 例如:

__lea rbx, my\_var__

这会把 __my\_var __ 的地址加载到 __rbx__ 中.

在 C++ 中, 如果对某个东西做自增, 指针给用户看到的效果其实是加一, 但在底层它实际上是向前移动了 2 个字节, 前提是它的长度为一个字, 也就是 16 位或 2 个字节. 一回事.

在汇编语言中, 每一个字节都是可寻址的. 例如:

__lea rax, my\_var__

__inc rax__

__mov word ptr \[rax\], rbx__

假设 __rbx__ 中的值是 __0x20__. 上面这条指令会把 __0x20__ 的值放到非字边界上, 这会导致错误. 你必须把 __rax__ 增加 2, 才能确保这种情况不会发生.

下周我们将深入数据段 (data segment)! 敬请期待!