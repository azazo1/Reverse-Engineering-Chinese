## Part 8 - 通用架构

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

x64 架构是 x86 平台的向后兼容扩展. 它既提供了与 x86 完全相同的传统 32 位模式, 也提供了一个新的 64 位模式.&nbsp;如果你想了解更多信息, 可以就在 LinkedIn 上翻看我以前那篇 x86 教程.

"x64" 这一术语同时涵盖 AMD 64 和 Intel64. 两者的指令集相似.

x64 把 x86 的 8 个通用寄存器 (general-purpose register) 扩展到 64 位, 并新增了 8 个 64 位寄存器. 这些 64 位寄存器的名字以 "__r__" 开头, 例如 __eax__ 的 64 位扩展就叫作 __rax__. 新寄存器命名为 __r8__ 到 __r15__.

每个寄存器的低 32 位, 低 16 位和低 8 位在操作数中都可以直接寻址. 这包括像 __esi__ 这样低 8 位以前无法寻址的寄存器. 下表列出了 64 位寄存器低位部分对应的汇编语言名称.

下面的表格逐一列出了各个字节的区分.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1538735142722.png"/></div>

输出到 32 位子寄存器的运算会自动零扩展 (zero-extended) 到整个 64 位寄存器. 输出到 8 位或 16 位子寄存器的运算则_不_做零扩展 (这是与 x86 兼容的行为).

__ax__, __bx__, __cx__ 和 __dx__ 的高 8 位仍然可以按 __ah__, __bh__, __ch__, __dh__ 寻址, 但不能与所有类型的操作数一起使用.

指令指针 (instruction pointer) __eip__ 和 __flags__ 寄存器也同样被扩展到了 64 位 (分别是 __rip__ 和 __rflags__).

x64 处理器还提供了几组浮点寄存器 (floating-point register):

*   八个 80 位的 x87 寄存器.
*   八个 64 位的 MMX 寄存器. (它们与 x87 寄存器有重叠.)
*   原本的八个 128 位 SSE 寄存器增加到了十六个.

下周我们深入调用约定 (calling convention)! 敬请期待!