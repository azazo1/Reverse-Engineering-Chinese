## Part 14 - ADD

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

在 ARM 汇编中, 有三条指令处理加法, 第一条是 ADD, 第二条是 ADC (Add With Carry, 带进位加法), 最后一条是 ADDS (Set Flag, 设置标志位). 本周我们聚焦 ADD.

让我们看一个例子来说明:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520193949676.jpg"/></div>

这里我们看到, 我们把十进制 __67__ 移入 __r1__, 把十进制 __53__ 移入 __r2__. 然后我们把 __r1 __和 __r2__ 相加, 并把结果放入 __r0__.

"那这一堆东西到底是什么, 我为什么要在意它?"

这个系列与同类教程都不一样.&nbsp;目标是拿一小段一小段的代码, 看清它到底做了什么.&nbsp;如果你想理解如何逆向一个二进制文件或任何类型的恶意软件, 掌握基础是至关重要的.&nbsp;学习 ARM 汇编基础会在你逆向 iPhone 或 Android 时帮到你. 本教程系列会从极小的代码片段入手, 并讨论:

1)__代码__:&nbsp;(在此) 我们简要说明这段代码做了什么.

2)__调试__:&nbsp;我们在 GDB 调试器中拆解这个二进制文件, 逐条单步执行指令, 看看它对程序流程, 寄存器值和标志位具体做了什么.

3)__修改__:&nbsp;我们修改代码的某一部分, 让它做我们想做的事!

这种方式让你每周只花几分钟, 就能很好地掌握幕后发生的事情.

下周我们将深入调试 ADD.