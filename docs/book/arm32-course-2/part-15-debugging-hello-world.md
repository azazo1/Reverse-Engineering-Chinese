## Part 15 - 调试 Hello World

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们回顾一下上周的代码.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520191246374.jpg"/></div>

开始调试!&nbsp;让我们启动 GDB, 也就是 GNU 调试器, 用它拆解这个 C++ 二进制, 并逐行地按 ARM 汇编单步跟踪.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520232284963.jpg"/></div>

这就是我们看到的 ARM 反汇编.&nbsp;不管你用什么语言编程, 它最终都会落到这一层.&nbsp;

如果你没有学过我之前那门 ARM 汇编的课程, 这可能会让你有点害怕.&nbsp;如果你需要温习一下, 请回到那个系列去看.

你大概正在问自己, 为什么我们不用原始源码来调试, 看看它如何与汇编漂亮地对应起来.&nbsp;答案是, 当你是一名专业的逆向工程师时, 你在逆向二进制的时候, 不会享有查看源码这种奢侈.&nbsp;

这是一个简单得近乎幼稚的例子, 整个系列我们都会用非常简单的例子, 好让你学到有效的技巧.&nbsp;我们这里使用的是基于文本的调试器, 目的是让你彻底明白正在发生什么, 同时也做点训练: 万一你将来需要附加到一台陌生机器上正在运行的进程, 你就会知道如何正确地调试或修改.

我会只专注于这种方法, 而不去用 IDA 之类好用的图形化调试器, 这样你才能在非常底层的位置进行操作.

我们先把链接寄存器加载到 __r11 __, 再把 __4__ 加到栈指针上, 然后把它加到 __r11__.&nbsp;这只是一个例程, 让二进制得以保存链接寄存器, 并在栈上开辟空间.

我们注意到内存地址 __0x10750__ 正从内存加载到寄存器 __r1__.&nbsp;让我们检查一下字符串, 看看那个地址上有什么.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520233136878.jpg"/></div>

瞧!&nbsp;我们看到那个内存地址上就是我们的字符串 __"Hello World!"__.&nbsp;

让我们在 __main+16.__ 处设置一个断点.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520202291983.jpg"/></div>

让我们看看寄存器的值.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520193660539.jpg"/></div>

现在我们看看 __r1__ 寄存器里是什么, 然后单步跟踪这个二进制.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520235567544.jpg"/></div>

我们看到 __"Hello World!"__ 字符串现在位于 __r1__ 之中, 它处在内存地址 __0x10848__.&nbsp;最后让我们继续运行这个二进制.

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520190662835.jpg"/></div>

理解汇编并逐步调试, 能让你对任何二进制拥有完全的, 终极的控制权!&nbsp;更复杂的二进制可能要花你几小时, 几天甚至几周才能真正完成逆向, 但技巧是一样的, 只是更费时间.

逆向工程是高级计算机工程中最精妙的分析形式.&nbsp;专业逆向工程师会使用很多工具, 每一种工具都有它的用途和目的, 但这一技巧才是最精妙, 最全面的.

下周我们会深入 Hello World 的修改.