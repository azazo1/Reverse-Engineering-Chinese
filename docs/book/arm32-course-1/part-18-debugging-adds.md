## Part 18 - 调试 ADDS

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们重新审视我们的代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520230639459.jpg"/></div>

我们再次 __add__ 把 __100__ 十进制加到 __r1__, 把 __4,294,967,295__ 加到 __r2__. 然后我们把 __add r1__ 与 __r2__ 相加, 并放入 __r0.__

让我们调试:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520149414710.jpg"/></div>

我们再次看到 __adds __, 它会在 CPSR 中设置标志位. 我们必须记住, 在 GDB 中调试时, CPSR 的值是十六进制的. 要看清哪些标志位被设置, 我们必须把十六进制转换成二进制. 等我们在接下来的教程里开始调试和修改这个例子时, 你就会明白其中的道理.

我们需要记住, CPSR 中的 bit 31, 20, 29 和 28 分别表示以下含义:

__bit 31 - N = 负标志位 (Negative Flag)__

__bit 30 - Z = 零标志位 (Zero Flag)__

__bit 29 - C = 进位标志位 (Carry Flag)__

__bit 28 - V = 溢出标志位 (Overflow Flag)__

我们看到 __CPSR__ 是 __10 十六进制__. __10 十六进制__ 转成二进制是 __0001__.

因此, 如果 bit 31, 30, 29 和 28 (__NZCV__) 的二进制值是 __0001__, 那就意味着:

__负标志位未设置__

__零标志位未设置__

__进位标志位未设置__

__溢出标志位已设置 __

上面的代码里没有任何东西设置 __溢出标志位__, 然而在执行这个二进制文件时, 它天生就处于被设置的状态.

让我们单步执行这个程序:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520609481159.jpg"/></div>

我们看到 __64 十六进制__ 或者说 __100 十进制 __如预期地被移入 __r1__. __CPSR__ 没有变化. 让我们再单步几次.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520042941149.jpg"/></div>

我们看到上面发生的加法运算, 并注意到 __100 十进制__ 与 __4294967295 十进制__ 相加之后, __r0 __的值是 __99 十进制__. 这怎么可能? 答案很简单, 这次加法让 __r0__ 这个 32 位寄存器溢出了.

如果我们查看 __CPSR__, 现在看到的是 __20000010 十六进制__, 或者说 __0010 0000 0000 0000 0000 0000 0001 0000 二进制__. 我们只需要关注最高几位, 也就是 __0010__:

bit 31, 30, 29 和 28 (__NZCV__) 的二进制值是 __0010__, 那就意味着:

__负标志位未设置__

__零标志位未设置__

__进位标志位已设置__

__溢出标志位未设置__

我们看到 __进位标志位__ 被设置了, 而 __溢出标志位 __没有被设置. 这是为什么呢?

__进位标志位__ 是两个 __无符号数 (unsigned numbers)__ 相加, 结果大于保存它的寄存器时被设置的标志位. 我们处理的是 32 位寄存器. 我们处理的也是无符号数, 因此 __CF__ 被设置而 __OF__ 没有, 因为 __OF__ 标志位处理的是 __有符号数 (signed numbers)__.

下周我们将深入修改 ADDS.