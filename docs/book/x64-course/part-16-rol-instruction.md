## Part 16 - ROL 指令

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

ROL 命令表示循环左移 (rotate left).

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1543575772711.jpg"/></div>

在上面这个运行于 Ubuntu Linux 机器的简单 x64 示例中, 我们看到我们把 __mov 1__ 移入 __al __, 然后循环左移 1 位.

二进制表示是 __00000001b__. 如果我们 __ROL__ 1 位, 这个值就变成 __00000010b__, 如下所示.

我们首先这样编译和链接:

__nasm -f elf64 -o test.o test.asm__

__ld -o test test.o__

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1543575972607.jpg"/></div>

在调试器 (debugger) 中我们可以看到 __al __起始值是 __1__, 循环左移后就变成 __10b__.

你也可以用更多的位数做 ROL. 逻辑保持不变, 因为这些位会像上面演示的那样循环左移.

下周我们将深入 ROR! 敬请期待!