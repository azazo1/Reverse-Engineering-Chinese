## Part 19 - 修改 ADDS

关于所有 Lesson 的完整目录, 请点击下方链接, 它会给出每节 Lesson 的简介, 以及将涵盖的主题.&nbsp;https://github.com/mytechnotalent/Reverse-Engineering-Tutorial

让我们再一次重新审视我们的代码:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520215587042.jpg"/></div>

我们再次 __add__ 把 __100__ 十进制加到 __r1__, 把 __4,294,967,295__ 加到 __r2__. 然后我们把 __add r1__ 与 __r2__ 相加, 并放入 __r0.__

让我们调试:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520594576879.jpg"/></div>

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

让我们看看如果再单步一次会怎样:

<div class="slate-resizable-image-embed slate-image-embed__resize-full-width"><img src="/imgs/1520149286284.jpg"/></div>

我们看到 __4294967295 十进制__ 或者说 __0xffffffff __在 __r2__ 中. 我们知道, 如果再单步一次, 就会让 CPSR 从 0001 变成 0010, 这意味着:

bit 31, 30, 29 和 28 (__NZCV__) 的二进制值是 __0010__, 那就意味着:

__负标志位未设置__

__零标志位未设置__

__进位标志位已设置__

__溢出标志位未设置__

这个动作会设置进位标志位. 不过让我们来修改:

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520147275008.jpg"/></div>

我们修改了 __r2__, 把它的值改成了 __1 十进制 __和__ 0x1 十六进制__. 现在我们知道, 上次__ CPSR __会变成 __0010__, 不过既然我们做了这样的修改, 就来看看单步时 __CPSR__ 会发生什么.

<div class="slate-resizable-image-embed slate-image-embed__resize-middle"><img src="/imgs/1520211562604.jpg"/></div>

砰! 我们修改成功了, 可以看到__ r0 __是 __101__, 因此没有触发进位标志位, __CPSR__ 保持在__ 0x10 十六进制 __, 也就是 __0001 二进制 __, 这意味着:

因此, 如果 bit 31, 30, 29 和 28 (__NZCV__) 的二进制值是 __0001__, 那就意味着:

__负标志位未设置__

__零标志位未设置__

__进位标志位未设置__

__溢出标志位已设置 __

完整地理解本节 Lesson 非常重要. 如果没有理解, 请复习前两周的 Lesson.

下周我们将深入 ADC.

  