## Part 17 - ROR 指令

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

ROR 命令表示循环右移 (rotate right).

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1544181149655.png"/></div>

在上面这个运行于 Ubuntu Linux 机器的简单 x64 示例中, 我们看到我们把 mov 1 放入 al, 然后循环右移 1 位.

二进制表示是 __00000001b__. 如果我们 __ROR__ 1 位, 这个值就变成 __10000000b__, 如下所示.

我们首先这样编译和链接:

__nasm -f elf64 -o test.o test.asm__

__ld -o test test.o__

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1544181229818.jpg"/></div>

在调试器 (debugger) 中我们可以看到 al 起始值是 1, 循环右移后就变成 __10000000b__.

下周我们将深入引导扇区基础 (Boot Sector Basics)! 敬请期待!