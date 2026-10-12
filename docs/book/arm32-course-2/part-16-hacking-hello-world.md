## Part 16 - 修改 Hello World

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下两周前的代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520191330889.jpg"/></div>

让我们再调试一次.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520233045514.jpg"/></div>

让我们再次检查内存地址 __0x10750__ 处字符串的内容, 并继续执行程序.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520200292099.jpg"/></div>

如你所见, 它保存着 "__Hello World!__" 字符串, 当我们继续运行时, 它会照样回显到终端.

开始修改!&nbsp;现在我们用字符串 "__Hacked World!__" 覆盖该内存地址里的值, 然后继续执行.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520148428152.jpg"/></div>

哇哦!&nbsp;我们的第一次修改!&nbsp;如你所见, 当你理解汇编之后, 无论二进制是用什么语言写成的, 你都对它拥有绝对的控制权.&nbsp;在这个非常简单的例子里, 我们成功修改了 __0x10750__ 这个内存地址里的值, 执行时它把 "__Hacked World!__" 回显到了终端也就是标准输出.

让我们再次运行这个二进制并做一次反汇编.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520230658310.jpg"/></div>

现在我们做同样的操作, 不过这次 __si__ 三次, 并检查 __r1__ 里的字符串.&nbsp;我们看到它包含 "__Hello World!__", 因为它在 __main+12__ 处已经成功地被 __ldr __(从内存加载到寄存器).

现在我们把 r1 设为 "__Hacked World!__" 并继续执行.&nbsp;如你所见, 这次我们修改的是从寄存器里出来的内容, 而不是内存里的.&nbsp;你显然可以开始看出, 修改任何东西都有很多种方式, 这里就是一个简单的例子, 展示了其中两种.&nbsp;

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520231520333.jpg"/></div>

逆向工程的核心就是理解程序如何执行, 劫持执行流, 并按我们的目的修改变量值!&nbsp;今天你在这段精彩旅程中迈出了第一步!

下周我们会深入常量.